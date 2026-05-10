from ddgs import DDGS
import bs4
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
import re
import os
import requests
import heapq
from typing import Optional
from pydantic import BaseModel
import itertools
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
import math
from collections import Counter
import hashlib
from langchain.tools import tool
from langchain.agents import create_agent
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from typing import List
from rank_bm25 import BM25Okapi
from .logger import get_logger

logger = get_logger("rag_pipeline")

class TextData(BaseModel):
    text : str
    title : Optional[str]
    href : Optional[str]

# this module scrapes information from the web, takes k top answers, cleans the text and returns a list of splitted docs
class ScrapeCleanStore:

    def __init__(self, **kwargs):
        self.vector_db = kwargs.get("vector_db", "chroma_langchain_db")
        self.embedding_model = kwargs.get("embed_model", "all-minilm")
        self.max_pages = kwargs.get("max_pages", 2)
        self.request_timeout = kwargs.get("request_timeout", 5)
        self.max_tags_per_page = kwargs.get("max_tags_per_page", 150)
        self.max_chunks_per_source = kwargs.get("max_chunks_per_source", 10)
        self.embeddings = OllamaEmbeddings(
            model = self.embedding_model,
            base_url=os.getenv("OLLAMA_URL")
        )
        self.vector_store = Chroma(
            collection_name="web_collection",
            embedding_function=self.embeddings,
            persist_directory=os.path.join(os.path.dirname(__file__), f"data/{self.vector_db}")
        )

    def top_links(self, query:str, n=None):
        n = n or self.max_pages
        with DDGS() as ddgs:
            results = ddgs.text(query, max_results=n)
            return [TextData(text=r["body"], href=r["href"], title=r["title"]) for r in results if len(r["body"]) > 100]

    def create_header(self):
        return {
            "User-Agent" : (
                "MyTextFetcher/0.1"
                "(Research Project; https://github.com/anukul; anukul@gmail.com)"
            ),
            "Accept-Encoding" : "gzip"
        }

    def word_entropy(self, text:str):
        words = text.lower().split()
        if len(words) < 10:
            return 0
        counts = Counter(words)
        total = len(words)
        return -1 * sum((c / total) * math.log2(c / total) for c in counts.values())

    def rank_text(self, text:str):
        length_score = math.log(len(text) + 1) * 200
        sentence_score = text.count(".") * 20
        paragraph_score = text.count("\n") * 5
        digit_penalty = len(re.findall(r"\d", text)) * 5
        symbol_penalty = len(re.findall(r"[|/\\=<>_{}<>@#$^*_+=~`[\]]", text)) * 10
        short_word_pen = len(re.findall(r"\b\w{1,2}\b", text)) * 5

        entropy = self.word_entropy(text)
        entropy_pen = 0 if entropy > 2.5 else (2.5 - entropy) * 300

        return length_score + sentence_score + paragraph_score - digit_penalty - symbol_penalty - short_word_pen - entropy_pen

    def clean_text(self, text:str):
        text = re.sub(r"https?://[^\s]+", "", text) # URLs, keep line breaks also
        text = re.sub(r"[.!?]{2,}", ".", text) # remove the trailing .s
        text = re.sub(r"\[[^\]]{1,4}\]", "", text) # remove texts like [1] [2]
        text = re.sub(r"[|•·–—]+", " ", text) # whitespace after separators
        text = re.sub(r"[<>@#$^*_+=~`]", " ", text) # whitespace after these symbols
        text = re.sub(r"\b[a-zA-Z]{30,}\b", " ", text) # remove the long words, generally meaningless
        text = re.sub(r"[ \t]+", " ", text)     # collapse spaces only
        text = re.sub(r"\n{3,}", "\n\n", text)  # keep paragraphs
        text = text.strip()

        lines = []
        for line in re.split(r"(?<=[.!?])\s+", text):
            line = line.strip()
            if len(line) < 25:
                continue
            if line.isupper():
                continue
            lines.append(line)
        return " ".join(line.rstrip(".!?") + "." for line in lines)

    def normalized_hash(self, text:str):
        t = text.lower()
        t = re.sub(r"\s+", " ", t)
        t = re.sub(r"[^\w\s]", "", t)
        return hashlib.sha1(t.encode()).hexdigest()

    def identify_code_css(self, text:str):
        css_tokens = re.findall(r"[.#][a-zA-Z_-]+", text)
        css_ratio = len(css_tokens) / max(len(text.split()), 1)
        symb_ratio = len(re.findall(r"[{};:]", text)) / max(len(text), 1)
        id_ratio = len(re.findall(r"\b[a-z]+(?:-[a-z]+)+\b|\b[a-z]+(?:_[a-z]+)+\b", text)) / max(len(text.split()), 1)
        return css_ratio > 0.15 or symb_ratio > 0.02 or id_ratio > 0.2
    
    def parse_and_score(self, query:str):
        page_info = self.top_links(query)
        html_pages = []
        valid_page_info = []
        for link in page_info:
            try:
                resp = requests.get(link.href, timeout=self.request_timeout, headers=self.create_header())
                html_pages.append(resp)
                valid_page_info.append(link)
            except requests.exceptions.RequestException as e:
                logger.warning(f"Skipping {link.href}: {e}")
        page_info = valid_page_info
        text_strainer = bs4.SoupStrainer(["article", "section", "div", "main", "h1", "h2", "h3"])#, class_=[re.compile("content")])
        
        soups = []
        for page, info in zip(html_pages, page_info):
            soup = bs4.BeautifulSoup(page.text, features="lxml", parse_only=text_strainer)

            for bad in soup.find_all(["style", "script", "noscript"]):
                bad.decompose()
            soups.append((soup, info.title, info.href))

        # chunk_size=400 to fit all-minilm's 256-token (~400 char) context limit
        splitter = RecursiveCharacterTextSplitter(chunk_size = 400, chunk_overlap=40, add_start_index=True)
        hash_counter = Counter()
        chunk_counter = itertools.count()
        chunks = []

        for soup in soups:
            for tag in soup[0].find_all(True)[:self.max_tags_per_page]:
                cleaned_text = self.clean_text(tag.get_text(" ", strip=True))
                if len(cleaned_text) < 150:
                    continue
                raw_chunks = splitter.split_text(cleaned_text)
                for c in raw_chunks:
                    if(self.identify_code_css(c)):
                        continue
                    h = self.normalized_hash(c)
                    hash_counter[h] += 1
                    chunks.append(TextData(text=c, title=soup[1], href=soup[2]))
        
        candidates = []
        for chunk in chunks:
            h = self.normalized_hash(chunk.text)
            if hash_counter.get(h, 0) > 3:
                continue
            score = self.rank_text(chunk.text)
            heapq.heappush(candidates, (-1 * score, next(chunk_counter), chunk))
        
        return page_info, candidates
    
    def create_docs(self, page_info:List[TextData], candidates:List[tuple]):

        docs = []
        sources_cnt = {i.href : self.max_chunks_per_source for i in page_info}
        seen = set()

        while len(candidates):
            popped_elem = heapq.heappop(candidates)[2]
            if sources_cnt.get(popped_elem.href) is not None:
                if sources_cnt.get(popped_elem.href) >= 0:
                    key = (popped_elem.href, self.normalized_hash(popped_elem.text))
                    if key in seen:
                        continue
                    seen.add(key)
                    sources_cnt[popped_elem.href] -= 1
                    docs.append(
                        Document(
                            page_content=popped_elem.text,
                            metadata={
                                "source" : popped_elem.href,
                                "title" : popped_elem.title
                            }
                        )
                    )
        return docs
    
    def store(self, docs:List[Document]):
        self.vector_store.add_documents(documents=docs)

    # query here is web searchable query
    def main(self, user_query:str):
        page_info, candidates = self.parse_and_score(user_query)
        doc_objects = self.create_docs(page_info, candidates)
        # Seed with DDGS snippets as guaranteed-relevant fallback docs
        snippet_docs = [
            Document(
                page_content=info.text,
                metadata={"source": info.href, "title": info.title}
            )
            for info in page_info if info.text
        ]
        all_docs = snippet_docs + doc_objects
        self.store(all_docs)
        return all_docs

# modules for structured outputs 
class RAGDecision(BaseModel):
    needs_rag : bool
    reason : str

class SearchQuery(BaseModel):
    query : str

class ModelOutput(BaseModel):
    answer : str

# creates a chain which converts user query into web searchable query if the model doesnt know the answer
# otherwise just returns information that LLM produces
# this module stores the info in a vector db and uses a provided model to retrieve docs from the mentioned vectorDB
# implements a tool for retrieval, and chain for augmentation and summarization of the final answer 
class RetrieveSummarize:
    def __init__(self, **kwargs):
        self.vector_db = kwargs.get("vector_db", "chroma_langchain_db")
        self.embedding_model = kwargs.get("embed_model", "all-minilm")
        self.embeddings = OllamaEmbeddings(
            model = "all-minilm",
            base_url=os.getenv("OLLAMA_URL")
        )

        self.vector_store = Chroma(
            collection_name="web_collection",
            embedding_function=self.embeddings,
            persist_directory=os.path.join(os.path.dirname(__file__), f"data/{self.vector_db}")
        )

        self.chat_model = ChatOllama(
            model=os.getenv("LLM_AS_JUDGE_MODEL"),
            base_url=os.getenv("OLLAMA_URL"),
            disable_streaming=False
        )

        self.info_retreiver = ScrapeCleanStore()

    def search_decision(self, user_prompt:str):
        prompt = ChatPromptTemplate.from_messages([
            ("system",
            "Decide whether answering the user's question requires"
            "external knowledge, private or recent documents from the internet."
            "If answering the question requires external help, set needs_rag=true."
            ),
            ("human",
            "{question}"
            )
        ])
        decision_chain = prompt | self.chat_model.with_structured_output(RAGDecision)
        return decision_chain.invoke({"question" : user_prompt}).needs_rag
    
    def direct_response(self, user_prompt:str):
        prompt = ChatPromptTemplate.from_messages([
            ("system",
            "Answer clearly and concisely."
            ),
            ("human",
            "{question}"
            )
        ])

        direct_chain = prompt | self.chat_model.with_structured_output(ModelOutput)
        return direct_chain.invoke({"question" : user_prompt}).answer

    def gen_search_query(self, user_prompt:str):
        prompt = ChatPromptTemplate.from_messages([
            ("system",
            "You generate a concise web search query."
            "Return only the query. No quotes, no explanations."
            ),
            ("human",
            "{input}"
            )
        ])
        query_chain = prompt | self.chat_model.with_structured_output(SearchQuery)
        return query_chain.invoke({"input" : user_prompt}).query

    def _rrf_score(self, rank: int, k: int = 60) -> float:
        """Reciprocal Rank Fusion score. k=60 is the standard constant."""
        return 1.0 / (k + rank + 1)

    def hybrid_retrieve(self, query: str, k: int = 5, fetch_k: int = 20) -> List[Document]:
        """
        Hybrid retrieval: Dense (Chroma) + BM25 sparse, fused via RRF.
        Step 1 - Dense: fetch fetch_k candidates from Chroma.
        Step 2 - BM25: score same candidates by keyword match.
        Step 3 - RRF: combine both rank lists, return top k.
        """
        dense_results = self.vector_store.similarity_search_with_score(query, k=fetch_k)
        if not dense_results:
            logger.warning("No documents returned from dense retrieval.")
            return []
        docs = [doc for doc, _ in dense_results]

        tokenized_corpus = [doc.page_content.lower().split() for doc in docs]
        bm25 = BM25Okapi(tokenized_corpus)
        bm25_scores = bm25.get_scores(query.lower().split())
        bm25_ranked_indices = sorted(range(len(docs)), key=lambda i: bm25_scores[i], reverse=True)

        rrf = {}
        for dense_rank, _ in enumerate(dense_results):
            rrf[dense_rank] = rrf.get(dense_rank, 0.0) + self._rrf_score(dense_rank)
        for bm25_rank, doc_idx in enumerate(bm25_ranked_indices):
            rrf[doc_idx] = rrf.get(doc_idx, 0.0) + self._rrf_score(bm25_rank)

        top_indices = sorted(rrf, key=lambda i: rrf[i], reverse=True)[:k]
        return [docs[i] for i in top_indices]

    def make_retrieve_tool(self, vector_store):
        @tool(response_format="content_and_artifact")
        def retrieve_context(query:str):
            """Retrieve information to help answer a query using hybrid search."""
            retrieved_docs = self.hybrid_retrieve(query, k=5)
            serealized = "\n\n".join(
                (f"Source : {doc.metadata} \n Content:{doc.page_content}")
                for doc in retrieved_docs
            )
            return serealized, retrieved_docs
        return retrieve_context
    
    def answer_with_context(self, context:str, question:str):
        prompt = ChatPromptTemplate.from_messages([
            ("system",
            "You are a helpful assistant"
            "Use only the provided context to answer the question."
            "If the answer is not in the context set answer=NA"
            ),
            ("human",
            "Context:\n{context}\n\nQuestion:\n{question}"
            )
        ])
        answer_chain = prompt | self.chat_model.with_structured_output(ModelOutput)
        return answer_chain.invoke({"context" : context, "question":question}).answer
    
    def make_context(self, docs:List[Document]):
        return "\n\n".join(
            (f"Content : {doc.page_content}")
            for doc in docs
        )
        
    def main(self, user_prompt:str, use_agent:bool = True, use_db:bool = True):
        if self.search_decision(user_prompt):
            logger.info("Cannot generate the ground truth using the model. Using external sources...")
            query = self.gen_search_query(user_prompt)
            logger.info(f"Generated the search query for web search : {query}")
            retrieved_docs = self.info_retreiver.main(query)
            if use_agent:
                prompt = (
                    "You have access to a tool that retrieves context from the internet."
                    "Use the tool to help answer queries."
                    "Summarize the final answer into 2 to 3 sentences."
                )
                tools = [self.make_retrieve_tool(self.vector_store)]
                agent = create_agent(self.chat_model, tools=tools, system_prompt=prompt)
                result = agent.invoke(
                    {
                        "messages" : [
                            {
                                "role" : "user",
                                "content" : query
                            }
                        ]
                    }
                )
                final = result["messages"][-1].content
                final = re.sub(r"<think>.*?</think>", "", final, re.DOTALL).strip()
            else:
                if use_db:
                    context = "\n\n".join(
                        f"Source : {doc.metadata}\nContent: {doc.page_content}"
                        for doc in self.hybrid_retrieve(query, k=5)
                    )
                else:
                    context = self.make_context(retrieved_docs)
                final = "NA"
                tries = 2
                while(final == "NA" and tries > 0):
                    final = self.answer_with_context(context, user_prompt)
                    tries -= 1
            return final
        else:
            logger.info("Generating a direct response...")
            return self.direct_response(user_prompt)



