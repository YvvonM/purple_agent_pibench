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
    AnswerRelevancyMetric
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

contextual_precision = ContextualPrecisionMetric()
contextual_recall = ContextualRecallMetric()
contextual_relevancy = ContextualRelevancyMetric()

print(goldens[0])