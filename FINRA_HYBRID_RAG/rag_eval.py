import json
import re
import os
import time
from dotenv import load_dotenv
from deepeval import evaluate
from deepeval.test_case import LLMTestCase
from deepeval.models import DeepEvalBaseLLM
from deepeval.metrics import (
    ContextualPrecisionMetric,
    ContextualRecallMetric,
    ContextualRelevancyMetric,
    AnswerRelevancyMetric,
    FaithfulnessMetric,
)
from deepeval.dataset import Golden
import litellm

from hybrid_rag import make_prediction

load_dotenv()
DEEP_EVAL_API = os.getenv("DEEP_EVAL_API")
if not DEEP_EVAL_API:
    raise ValueError("DEEP_EVAL_API key not set!")


with open("Data_cleaning/evaluation_dataset/goldens1.json", "r", encoding="utf-8") as f:
    data = json.load(f)

goldens = [
    Golden(input=item["input"], expected_output=item["expected_output"])
    for item in data
]

print(f"Loaded {len(goldens)} goldens from JSON")


def clean_context(raw_context):
    """Strip metadata and return clean text passages."""
    if isinstance(raw_context, str):
        raw_context = [raw_context]
    elif not isinstance(raw_context, list):
        raw_context = list(raw_context) if raw_context else []
    
    cleaned = []
    for ctx in raw_context:
        ctx = str(ctx)
        # Remove common metadata prefixes
        ctx = re.sub(r'^Entities:\s*.*?\n', '', ctx, flags=re.IGNORECASE)
        ctx = re.sub(r'^Source:\s*.*?\n', '', ctx, flags=re.IGNORECASE)
        ctx = re.sub(r'^Tags:\s*.*?\n', '', ctx, flags=re.IGNORECASE)
        ctx = re.sub(r'^Metadata:\s*.*?\n', '', ctx, flags=re.IGNORECASE)
        # Remove any filenames at start
        ctx = re.sub(r'^[a-zA-Z0-9_\-]+\.(txt|md|pdf|json)\s*', '', ctx)
        # Strip extra whitespace
        ctx = ctx.strip()
        if ctx:
            cleaned.append(ctx)
    
    return cleaned


class LLMLiteModel(DeepEvalBaseLLM):
    def __init__(self, model="groq/llama-3.3-70b-versatile"):
        self.model = model

    def load_model(self):
        return self.model

    def generate(self, prompt: str) -> str:
        response = litellm.completion(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=4096,
        )
        raw = response.choices[0].message.content
        
        # Clean markdown
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw.strip())
        return raw.strip()

    async def a_generate(self, prompt: str) -> str:
        return self.generate(prompt)

    def get_model_name(self):
        return self.model


# Build test cases
test_cases = []
for item in goldens:
    question = item.input
    expected_output = item.expected_output
    
    try:
        rag_result, raw_context = make_prediction(question)
    except Exception as e:
        print(f"WARNING: make_prediction failed for '{question[:50]}...': {e}")
        continue

    # Clean the context before passing to DeepEval
    retrieved_context = clean_context(raw_context)

    # Debug: show what we're passing
    print(f"\nQuestion: {question[:60]}...")
    for i, ctx in enumerate(retrieved_context):
        print(f"  Context[{i}]: {ctx[:100]}...")

    test_case = LLMTestCase(
        input=question,
        actual_output=str(rag_result) if rag_result is not None else "",
        expected_output=expected_output,
        retrieval_context=retrieved_context,
        context=retrieved_context,
    )
    test_cases.append(test_case)

print(f"\nHave {len(test_cases)} test cases to evaluate.")



eval_model = LLMLiteModel()

metrics_to_run = [
    ("Contextual Precision", ContextualPrecisionMetric(model=eval_model, threshold=0.5)),
    ("Contextual Recall", ContextualRecallMetric(model=eval_model, threshold=0.5)),
    ("Contextual Relevancy", ContextualRelevancyMetric(model=eval_model, threshold=0.5)),
    ("Faithfulness", FaithfulnessMetric(model=eval_model, threshold=0.5)),
    ("Answer Relevancy", AnswerRelevancyMetric(model=eval_model, threshold=0.5
    )),
]

all_results = {}

for metric_name, metric in metrics_to_run:
    print(f"\n{'='*60}")
    print(f"Running: {metric_name}")
    print(f"{'='*60}")
    
    metric_scores = []
    
    for i, test_case in enumerate(test_cases):
        print(f"\n  Test case {i+1}/{len(test_cases)}...")
        
        try:
            # Evaluate ONE test case with ONE metric
            result = evaluate([test_case], metrics=[metric])
            
            # Extract score
            if result.test_results:
                test_result = result.test_results[0]
                for metric_data in test_result.metrics_data:
                    score = metric_data.score
                    metric_scores.append(score)
                    print(f"    Score: {score:.3f}")
                    if hasattr(metric_data, 'reason') and metric_data.reason:
                        print(f"    Reason: {metric_data.reason[:80]}...")
            
            # Sleep between test cases to stay under Groq TPM limit
            # 12K TPM limit, ~4K tokens per call = max 3 calls/minute
            if i < len(test_cases) - 1:
                print(f"    Sleeping 25s...")
                time.sleep(25)
                
        except Exception as e:
            print(f"    ERROR: {e}")
            metric_scores.append(0.0)
            time.sleep(30)
    
    # Calculate average for this metric
    avg_score = sum(metric_scores) / len(metric_scores) if metric_scores else 0
    all_results[metric_name] = {
        "scores": metric_scores,
        "average": avg_score
    }
    
    print(f"\n  {metric_name} Average: {avg_score:.3f}")
    print(f"  Completed. Sleeping 15s before next metric...")
    time.sleep(15)

print("\n" + "="*60)
print("ALL METRICS COMPLETE")
print("="*60)
for name, result in all_results.items():
    print(f"\n{name}: {result['average']:.3f}")
    print(f"  Individual scores: {[round(s, 3) for s in result['scores']]}")