import json 
from deepeval.dataset import Golden



def convert_format(data: dict):

    goldens = [
    Golden(input=item['question'], expected_output=item['answer'])
    for item in data
]
    return goldens

def main(input_link, output_link):
    with open(input_link, "r", encoding="utf-8") as f:
        data = json.load(f)  

    goldens = convert_format(data)

    with open(output_link, "w", encoding="utf-8") as f:
        json.dump([
            {"input": g.input, "expected_output": g.expected_output}
            for g in goldens
        ], f, indent=2)
if __name__ == "__main__":
    main("evaluation_dataset/dataset.json", "evaluation_dataset/goldens.json
    ")