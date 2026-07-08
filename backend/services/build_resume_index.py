import os
import shutil
from pathlib import Path
from llama_index.core import SimpleDirectoryReader, StorageContext, VectorStoreIndex, Settings
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.vector_stores.chroma import ChromaVectorStore
import chromadb

def build_clean_index():
    print("--- Starting Clean Indexing Process ---")
    chroma_dir = "../chroma_db"
    if os.path.exists(chroma_dir):
        shutil.rmtree(chroma_dir)

    Settings.embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")
    input_dir = "../data/resumes"

    # Custom file metadata injector for LlamaIndex
    def file_metadata_hook(file_path):
        return {"resume_id": Path(file_path).stem}

    # file_metadata ensures every chunk carries the original filename stem!
    reader = SimpleDirectoryReader(input_dir, file_metadata=file_metadata_hook)
    documents = reader.load_data()

    db = chromadb.PersistentClient(path=chroma_dir)
    resume_collection = db.get_or_create_collection("resume_collection")
    vector_store = ChromaVectorStore(chroma_collection=resume_collection)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    
    index = VectorStoreIndex.from_documents(documents, storage_context=storage_context)
    print(f"✓ Re-indexing Complete. Vectors Stored: {resume_collection.count()}")

if __name__ == "__main__":
    build_clean_index()