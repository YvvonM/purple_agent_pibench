import json 
from dotenv import load_dotenv 
from deepeval import evaluate
from deepeval.test_case import LLMTestCase
from deepeval.models import DeepEvalBaseLLM
import litellm
from deepeval.metrics import (
    ContextualPrecisionMetric,
    ContextualRecallMetric,
    ContextualRelevancyMetric,
    AnswerRelevancyMetric,
    FaithfulnessMetric
)
import os 
from hybrid_rag import make_prediction
from deepeval.dataset import Golden

load_dotenv()
DEEP_EVAL_API = os.getenv("DEEP_EVAL_API")
if not DEEP_EVAL_API:
    raise ValueError("Api key not set!")


with open("Data_cleaning/evaluation_dataset/goldens.json", "r", encoding="utf-8") as f:
    data = json.load(f)

goldens = [
    Golden(input=item["input"], expected_output=item["expected_output"])
    for item in data
]

print(f"Loaded {len(goldens)} goldens from JSON")


class LLMLiteModel(DeepEvalBaseLLM):
    def __init__(self, model="groq/meta-llama/llama-4-scout-17b-16e-instruct"):
        self.model = model 

    def load_model(self):
        return self.model 

    def generate(self, prompt: str) -> str:
        response = litellm.completion(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        return response.choices[0].message.content 

    async def a_generate(self, prompt: str) -> str:
        return self.generate(prompt)

    def get_model_name(self):
        return self.model

eval_model = LLMLiteModel()
metrics = [
ContextualPrecisionMetric(model=eval_model),
ContextualRecallMetric(model=eval_model),
ContextualRelevancyMetric(model=eval_model),
FaithfulnessMetric(model=eval_model),
AnswerRelevancyMetric(model=eval_model)]


test_cases = []
for item in goldens:
    question = item.input
    expected_output = item.expected_output
    rag_result, retrieved_context = make_prediction(question)

    test_case = LLMTestCase(
        input = question,
        actual_output = rag_result,
        expected_output = expected_output,
        retrieval_context = retrieved_context
    )
    test_cases.append(test_case)
print(f"Have {len(test_cases)} number of questions to test.")
results = evaluate(test_cases, metrics=metrics)

print("*" * 60)
print(results)
print("*" * 60)