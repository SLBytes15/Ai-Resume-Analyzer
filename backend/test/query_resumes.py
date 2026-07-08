from llama_index.core import (
    VectorStoreIndex,
    Settings
)

from llama_index.embeddings.huggingface import (
    HuggingFaceEmbedding
)

from llama_index.llms.ollama import Ollama

from llama_index.vector_stores.chroma import (
    ChromaVectorStore
)

import chromadb

Settings.embed_model = HuggingFaceEmbedding(
    model_name="BAAI/bge-small-en-v1.5"
)

# 2. Cloud LLM (Zero memory usage on your Mac, massive context window)
Settings.llm = Ollama(
    model="nemotron-3-super:cloud",  # Use this free cloud option instead!
    request_timeout=120
)

db = chromadb.PersistentClient(
    path="../chroma_db"
)

collection = db.get_collection(
    "resume_collection"
)

vector_store = ChromaVectorStore(
    chroma_collection=collection
)

index = VectorStoreIndex.from_vector_store(
    vector_store=vector_store
)

query_engine = index.as_query_engine(
    similarity_top_k = 5
)

response = query_engine.query(
    """
    Find candidates suitable for a React job
    """
)

print(response)

for node in response.source_nodes:
    print("\n---------")
    print(node.metadata.get("file_name"))