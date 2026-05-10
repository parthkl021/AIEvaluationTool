import warnings, os
from lib.data import TestCase, Conversation, LLMJudgePrompt
from .strategy_base import Strategy
from .logger import get_logger
from .utils_new import FileLoader
from .llm_judge import LLMJudgeStrategy, _build_judge_model
from ._rag_modules import RetrieveSummarize
import re

warnings.filterwarnings("ignore")

FileLoader._load_env_vars(__file__)
logger = get_logger("hallucination")
dflt_vals = FileLoader._to_dot_dict(__file__, os.getenv("DEFAULT_VALUES_PATH"), simple=True, strat_name="hallucination")

# Few-shot hallucination criteria
HALLUCINATION_CRITERIA = """
Detect whether the agent response contains hallucinated facts not supported \
by the expected output. A hallucination is any claim that contradicts, \
fabricates, or materially distorts the expected output.

Examples:

Example 1 (HALLUCINATED):
  Expected: "Argentina won the 2022 FIFA World Cup."
  Agent:    "France won the 2022 FIFA World Cup on penalties."
  → HALLUCINATED — wrong winner and wrong outcome.

Example 2 (NOT HALLUCINATED):
  Expected: "The Eiffel Tower is 330 metres tall."
  Agent:    "The Eiffel Tower stands at 330 metres."
  → NOT HALLUCINATED — semantically equivalent, same fact.

Score 0 if the agent response is NOT hallucinated (faithful to expected output).
Score 1 if the agent response IS hallucinated (contradicts or fabricates facts).
"""

class HallucinationStrategy(Strategy):
    def __init__(self, name="hallucination", **kwargs):
        super().__init__(name, **kwargs)
        self.rag_module = RetrieveSummarize()
        self.llm_judge = LLMJudgeStrategy(metric_name=kwargs.get("metric_name", "hallucination"))
        self.eval_type = name.split("_")[-1]

        # If LLM_AS_VERIFIER_MODEL is set and different from the primary judge
        verifier_model_name = os.getenv("LLM_AS_VERIFIER_MODEL", "")
        if verifier_model_name and verifier_model_name != os.getenv("LLM_AS_JUDGE_MODEL", ""):
            try:
                self.llm_judge.models.append(_build_judge_model(verifier_model_name))
                self.llm_judge.model_names.append(verifier_model_name)
                logger.info(f"Dual-model verification enabled. Verifier: {verifier_model_name}")
            except Exception as e:
                logger.warning(f"Could not load verifier model '{verifier_model_name}': {e}. Using single-model.")

    def extract_prediction(self, response: str) -> str:
        response = response.strip().lower()
        response_clean = re.sub(r"[^a-zA-Z]", "", response.split()[0].upper())
        if response_clean in ["A", "B", "C", "D"]:
            return response_clean
        return "NA"

    def evaluate(self, testcase:TestCase, conversation:Conversation):
        reason = ""
        if self.eval_type == "haluqa" or self.eval_type == "halusumm":
            if not testcase.judge_prompt:
                testcase.judge_prompt = LLMJudgePrompt(HALLUCINATION_CRITERIA)
            testcase.judge_prompt.prompt = HALLUCINATION_CRITERIA
            testcase.prompt.system_prompt = ("You are a hallucination detection agent."
                                            "Based on the expected output, evaluate if the user prompt is hallucinated.")
            if testcase.response.response_text.strip() == "":
                grounded_truth = self.rag_module.main(testcase.prompt.user_prompt, use_agent=False, use_db=False)
                if(grounded_truth != "NA"):
                    testcase.response.response_text = grounded_truth

            score, reason = self.llm_judge.evaluate(testcase, conversation)
        else:
            prediction = self.extract_prediction(conversation.agent_response).strip()
            score = 1.0 if prediction == testcase.response.response_text.upper() else 0.0
        return score, reason
