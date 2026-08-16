### document for chuncking the json files
from json
from langchain.schema import Document
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma


with open("main_document.json", "r") as f:
    main_json = json.load(f)

with open("metadata_registry.json", "r") as f:
    metadata_registry = json.load(f)
