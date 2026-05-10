"""
group_prompts.py
----------------
Reads all prompts from updated_datapoints.json, then uses Gemini to decide
whether each consecutive pair (within the same metric) is a contextual
follow-up or an independent question.

Groups them into conversation chains and prints the result.

Usage:
    python group_prompts.py
    python group_prompts.py --datapoints ../../data/updated_datapoints.json
    python group_prompts.py --output groups.json
"""

import json
import os
import re
import argparse
from google import genai
from google.genai import types
from openai import OpenAI
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Load API keys from .env
# ---------------------------------------------------------------------------
ENV_PATH = os.path.join(os.path.dirname(__file__), "../../.env")
load_dotenv(ENV_PATH)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# Gemini fallback: read from PQET's API_keys.json
if not GEMINI_API_KEY:
    keys_path = os.path.join(os.path.dirname(__file__), "prompt_quality_evaluation_tool", "API_keys.json")
    if os.path.exists(keys_path):
        with open(keys_path) as f:
            data = json.load(f)
        keys = [k for k in data.get("GEMINI_API_KEYS", []) if k.strip()]
        if keys:
            GEMINI_API_KEY = keys[0]


# ---------------------------------------------------------------------------
# LLM check: are two prompts contextually linked?
# ---------------------------------------------------------------------------

def _build_prompt(prev: dict, curr: dict) -> str:
    return f"""You are analyzing chatbot test cases.

PREVIOUS TEST CASE:
  System Prompt: {prev['SYSTEM_PROMPT'][:200]}
  User Prompt: {prev['PROMPT']}

CURRENT TEST CASE:
  System Prompt: {curr['SYSTEM_PROMPT'][:200]}
  User Prompt: {curr['PROMPT']}

Question: Is the CURRENT user prompt a natural follow-up or continuation of the PREVIOUS one — meaning a real user would ask this second question AFTER getting an answer to the first, within the same conversation?

Answer YES only if there is a clear contextual link (e.g., same topic being deepened, a reference to previous content, a correction, or a logical next step).
Answer NO if they are independent questions that happen to share a topic but could stand alone.

Respond in exactly this JSON format:
{{"linked": true or false, "reason": "<one sentence>"}}

Output ONLY the JSON."""


def _parse_llm_response(raw: str) -> tuple[bool, str]:
    raw = re.sub(r"```(?:json)?", "", raw).strip().rstrip("`").strip()
    try:
        parsed = json.loads(raw)
        return bool(parsed.get("linked", False)), parsed.get("reason", "")
    except Exception:
        return False, "Could not parse LLM response — defaulting to not linked"


def is_followup(prev: dict, curr: dict, provider: str = "gemini") -> tuple[bool, str]:
    """
    Ask an LLM whether `curr` is a natural follow-up to `prev`.
    provider: 'gemini' or 'openai'
    Returns (True/False, reason string).
    """
    prompt = _build_prompt(prev, curr)

    if provider == "openai":
        if not OPENAI_API_KEY:
            raise RuntimeError("OPENAI_API_KEY not found in .env — uncomment and set it.")
        client = OpenAI(api_key=OPENAI_API_KEY)
        resp = client.chat.completions.create(
            model="gpt-5.4-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
        )
        raw = resp.choices[0].message.content.strip()
    else:  # gemini (default)
        if not GEMINI_API_KEY:
            raise RuntimeError("No Gemini API key found. Set GEMINI_API_KEY in .env or populate prompt_quality_evaluation_tool/API_keys.json")
        client = genai.Client(api_key=GEMINI_API_KEY)
        resp = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(temperature=0.1),
        )
        raw = resp.candidates[0].content.parts[0].text.strip()

    return _parse_llm_response(raw)


# ---------------------------------------------------------------------------
# Core grouping logic
# ---------------------------------------------------------------------------

def group_prompts(datapoints: dict, provider: str = "gemini") -> list:
    """
    For each metric, iterate through its cases and group consecutive
    contextually-linked prompts into conversation chains.

    Returns a list of groups, each group being a list of test cases.
    """
    all_groups = []

    for metric_id, block in datapoints.items():
        cases = block.get("cases", [])
        if not cases:
            continue

        print(f"\n── Metric {metric_id} ({len(cases)} cases) ──")

        # Start the first group with the first case
        current_group = [cases[0]]

        for i in range(1, len(cases)):
            prev = cases[i - 1]
            curr = cases[i]

            # Hard rule: different system_prompt → always a new group, skip LLM call
            if prev["SYSTEM_PROMPT"].strip() != curr["SYSTEM_PROMPT"].strip():
                print(f"  [{prev['PROMPT_ID']} → {curr['PROMPT_ID']}] SPLIT (different system prompt)")
                all_groups.append({"metric_id": metric_id, "cases": current_group})
                current_group = [curr]
                continue

            # LLM check
            linked, reason = is_followup(prev, curr, provider=provider)
            tag = "LINKED" if linked else "SPLIT "
            print(f"  [{prev['PROMPT_ID']} → {curr['PROMPT_ID']}] {tag} | {reason}")

            if linked:
                current_group.append(curr)
            else:
                all_groups.append({"metric_id": metric_id, "cases": current_group})
                current_group = [curr]

        # Close the last group
        all_groups.append({"metric_id": metric_id, "cases": current_group})

    return all_groups


# ---------------------------------------------------------------------------
# Output formatters
# ---------------------------------------------------------------------------

def format_output(groups: list) -> dict:
    """Diagnostic summary — used for console display only."""
    result = []
    for i, group in enumerate(groups, 1):
        cases = group["cases"]
        result.append({
            "group_id": i,
            "metric_id": group["metric_id"],
            "size": len(cases),
            "type": "conversation" if len(cases) > 1 else "standalone",
            "prompt_ids": [c["PROMPT_ID"] for c in cases],
            "turns": [
                {"PROMPT_ID": c["PROMPT_ID"], "PROMPT": c["PROMPT"]}
                for c in cases
            ]
        })
    return {"total_groups": len(result), "groups": result}


def _merge_conversation(cases: list) -> dict:
    """
    Merge a multi-turn group into a single datapoint entry.

    Format (matches metric 23 style):
      PROMPT = "User: <turn1> Bot: <expected1> User: <turn2> Bot: <expected2> User: <lastTurn>"
      EXPECTED_OUTPUT = last case's EXPECTED_OUTPUT
    All other fields (SYSTEM_PROMPT, LLM_AS_JUDGE, DOMAIN, STRATEGY) taken from the first case.
    The PROMPT_ID of the merged entry is the first case's ID suffixed with _CONV.
    """
    prompt_parts = []
    for i, case in enumerate(cases):
        prompt_parts.append(f"User: {case['PROMPT']}")
        # Add bot reply for every turn except the last
        if i < len(cases) - 1:
            prompt_parts.append(f"Bot: {case.get('EXPECTED_OUTPUT', '')}")

    first = cases[0]
    return {
        "PROMPT_ID": first["PROMPT_ID"] + "_CONV",
        "LLM_AS_JUDGE": first.get("LLM_AS_JUDGE", "No"),
        "SYSTEM_PROMPT": first["SYSTEM_PROMPT"],
        "PROMPT": " ".join(prompt_parts),
        "EXPECTED_OUTPUT": cases[-1].get("EXPECTED_OUTPUT", ""),
        "DOMAIN": first.get("DOMAIN", "general"),
        "STRATEGY": first.get("STRATEGY", []),
    }


def format_datapoints(groups: list) -> dict:
    """
    Produce output in updated_datapoints.json format, ready to merge.

    For conversation groups:
      - All individual cases are kept as-is (so per-turn scoring is preserved).
      - A merged multi-turn entry (PROMPT_ID suffixed _CONV) is appended after them.
    For standalone cases: kept as-is.
    Result is keyed by metric_id, same as the source file.
    """
    INTERNAL_KEYS = {"_test_note"}

    merged: dict = {}
    for group in groups:
        metric_id = group["metric_id"]
        cases = group["cases"]
        bucket = merged.setdefault(metric_id, {"cases": []})["cases"]

        if len(cases) > 1:
            # Keep every individual turn
            for case in cases:
                bucket.append({k: v for k, v in case.items() if k not in INTERNAL_KEYS})
            # Append the merged multi-turn entry as an extra
            bucket.append(_merge_conversation(cases))
        else:
            # Standalone — strip internal-only keys and keep
            bucket.append({k: v for k, v in cases[0].items() if k not in INTERNAL_KEYS})

    return merged


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Group prompts into conversation chains using Gemini")
    parser.add_argument(
        "--datapoints", "-d",
        default=os.path.join(os.path.dirname(__file__), "../../data/updated_datapoints.json"),
        help="Path to updated_datapoints.json"
    )
    parser.add_argument(
        "--output", "-o",
        default=None,
        help="Optional path to save the grouped output as JSON"
    )
    parser.add_argument(
        "--provider", "-p",
        default="gemini",
        choices=["gemini", "openai"],
        help="LLM provider to use for grouping decisions (default: gemini)"
    )
    parser.add_argument(
        "--metric", "-m",
        default=None,
        help="Only process a specific metric ID (e.g. 2)"
    )
    args = parser.parse_args()

    with open(args.datapoints, "r", encoding="utf-8") as f:
        datapoints = json.load(f)

    # Filter to a single metric if requested
    if args.metric:
        if args.metric not in datapoints:
            print(f"Metric {args.metric} not found. Available: {list(datapoints.keys())}")
            exit(1)
        datapoints = {args.metric: datapoints[args.metric]}

    print(f"Loaded {sum(len(v['cases']) for v in datapoints.values())} test cases across {len(datapoints)} metrics")
    print(f"Using provider: {args.provider.upper()}")

    groups = group_prompts(datapoints, provider=args.provider)
    output = format_output(groups)

    # Summary
    print(f"\n{'='*50}")
    print(f"Total groups : {output['total_groups']}")
    conversations = [g for g in output['groups'] if g['type'] == 'conversation']
    standalones   = [g for g in output['groups'] if g['type'] == 'standalone']
    print(f"Conversations: {len(conversations)} (multi-turn groups)")
    print(f"Standalone   : {len(standalones)} (independent questions)")

    for g in conversations:
        print(f"  Group {g['group_id']} [metric {g['metric_id']}]: {' → '.join(g['prompt_ids'])}")

    # Build datapoints-compatible output
    dp_output = format_datapoints(groups)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(dp_output, f, indent=4, ensure_ascii=False)
        print(f"\nSaved datapoints-compatible output to {args.output}")
    else:
        print("\n--- Datapoints-compatible output (ready to merge into updated_datapoints.json) ---")
        print(json.dumps(dp_output, indent=4, ensure_ascii=False))
