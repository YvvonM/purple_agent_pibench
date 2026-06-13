import time
import json
import re
import os
from typing import List
from dotenv import load_dotenv
from deepeval.test_case import LLMTestCase
from deepeval.models import DeepEvalBaseLLM
from deepeval.metrics import (
    ContextualPrecisionMetric,
    ContextualRecallMetric,
    ContextualRelevancyMetric,
    AnswerRelevancyMetric,
    FaithfulnessMetric,
)
import litellm

load_dotenv()

SLEEP_SECONDS = 4.0
JSON_PATH = "Data_cleaning/evaluation_dataset/rag_evaluation_results.json"


# --- KEY ROTATOR ---

class KeyRotator:
    def __init__(self, keys: List[str], per_key: int = 2):
        self.keys = [k for k in keys if k]
        if not self.keys:
            raise ValueError("No API keys")
        self.per_key = per_key
        self.idx = 0
        self.count = 0

    def get(self):
        key = self.keys[self.idx]
        self.count += 1
        if self.count >= self.per_key:
            self.count = 0
            self.idx = (self.idx + 1) % len(self.keys)
        return key


rotator = KeyRotator([
    os.getenv("DEEP_EVAL_API"),
    os.getenv("Y_GROQ"),
    os.getenv("J_GROQ"),
    os.getenv("GROQ_API_KEY"),
])


# --- CUSTOM JUDGE MODEL ---

class LLMLiteModel(DeepEvalBaseLLM):
    def __init__(self, model="groq/meta-llama/llama-4-scout-17b-16e-instruct"):
        self.model = model

    def load_model(self):
        return self.model

    def generate(self, prompt: str) -> str:
        resp = litellm.completion(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            api_key=rotator.get(),
            temperature=0.2,
            max_tokens=4096,
        )
        raw = resp.choices[0].message.content
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw.strip())
        return raw.strip()

    async def a_generate(self, prompt: str) -> str:
        return self.generate(prompt)

    def get_model_name(self):
        return self.model


# Instantiate ONCE and pass to every metric
eval_model = LLMLiteModel()


# --- LOAD DATA ---

with open("Data_cleaning/evaluation_dataset/goldens.json", "r", encoding="utf-8") as f:
    answers = json.load(f)

with open("Data_cleaning/evaluation_dataset/rag_answers.json", "r", encoding="utf-8") as f:
    rag_answers = json.load(f)

expected_lookup = {item["input"]: item["expected_output"] for item in answers}

test_cases = []
for item in rag_answers:
    test_cases.append(LLMTestCase(
        input=item.get("query", ""),
        actual_output=item.get("answer", ""),
        expected_output=expected_lookup.get(item.get("query", ""), ""),
        retrieval_context=item.get("retrieved_context", []),
    ))

print(f"Built {len(test_cases)} test cases")


# --- METRICS: pass model HERE at init time ---

metrics = [
    ("Contextual Precision", ContextualPrecisionMetric(threshold=0.6, model=eval_model)),
    ("Contextual Recall",    ContextualRecallMetric(threshold=0.6, model=eval_model)),
    ("Contextual Relevancy", ContextualRelevancyMetric(threshold=0.6, model=eval_model)),
    ("Answer Relevancy",   AnswerRelevancyMetric(threshold=0.6, model=eval_model)),
    ("Faithfulness",       FaithfulnessMetric(threshold=0.6, model=eval_model)),
]


# --- RESUME LOGIC ---

if os.path.exists(JSON_PATH):
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        results = json.load(f)
    print(f"Resumed: {len(results)} rows")
else:
    results = []

done = {
    (r["question_num"] - 1, r["metric"])
    for r in results
    if "metric" in r
}


# --- EVALUATE + SAVE AFTER EACH METRIC ---

for i, tc in enumerate(test_cases):
    for metric_name, metric in metrics:
        if (i, metric_name) in done:
            print(f"Skip Q{i+1} × {metric_name}")
            continue

        print(f"Q{i+1} × {metric_name} ...", end=" ")
        try:
            metric.measure(tc)
            results.append({
                "question_num": i + 1,
                "question": tc.input,
                "metric": metric_name,
                "score": metric.score,
                "passed": metric.is_successful(),
                "reason": getattr(metric, "reason", "")[:300],
            })
            print(f"score={metric.score:.2f}")
        except Exception as e:
            results.append({
                "question_num": i + 1,
                "question": tc.input,
                "metric": metric_name,
                "score": None,
                "passed": False,
                "reason": str(e),
            })
            print(f"ERROR: {e}")

        with open(JSON_PATH, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)
        time.sleep(SLEEP_SECONDS)


# --- SUMMARY ---

print("\n" + "=" * 40)
from collections import defaultdict
by_metric = defaultdict(list)
for r in results:
    if r.get("score") is not None:
        by_metric[r["metric"]].append(r["score"])

for name, _ in metrics:
    scores = by_metric.get(name, [])
    passes = sum(1 for r in results if r.get("metric") == name and r.get("passed"))
    total = sum(1 for r in results if r.get("metric") == name)
    if scores:
        print(f"{name}: avg={sum(scores)/len(scores):.2f} pass={passes}/{total}")