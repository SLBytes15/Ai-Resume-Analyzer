
from llama_index.core import (
    SimpleDirectoryReader,
    StorageContext,
    VectorStoreIndex,
    Settings
)

from llama_index.embeddings.huggingface import (
    HuggingFaceEmbedding
)

from llama_index.vector_stores.chroma import ChromaVectorStore

import chromadb


Settings.embed_model = HuggingFaceEmbedding(
    model_name="BAAI/bge-small-en-v1.5"
)

documents = SimpleDirectoryReader(
    "../data/jds"
).load_data()

print("Documents:" , len(documents))

db = chromadb.PersistentClient(
    path="../chroma_db"
)

jd_collection = db.get_or_create_collection(
    "jd_collection"
)

vector_store = ChromaVectorStore(
    chroma_collection=jd_collection
)

storage_context = StorageContext.from_defaults(
    vector_store=vector_store
)

index = VectorStoreIndex.from_documents(
    documents,
    storage_context=storage_context
)

print(
    "Vectors Stored:",
    jd_collection.count()
)