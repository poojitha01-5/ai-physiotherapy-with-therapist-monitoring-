#!/usr/bin/env python3
"""
Knowledge Base Ingestion Script for PhysioVision RAG Chatbot

This script ingests PDF, TXT, and Markdown files from the KnowledgeBase folder,
splits them into chunks, generates embeddings using Gemini, and stores them in ChromaDB.
"""

import os
import sys
from pathlib import Path
from typing import List, Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import chromadb
from chromadb.config import Settings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from langchain_community.document_loaders import (
    PyPDFLoader,
    TextLoader,
    UnstructuredMarkdownLoader,
)
from google.generativeai import genai
import google.generativeai as genai

# Configuration
KNOWLEDGE_BASE_DIR = Path(__file__).parent / "KnowledgeBase"
CHROMA_DB_DIR = Path(__file__).parent / "chroma_db"
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
COLLECTION_NAME = "physiotherapy_knowledge_base"

# Gemini Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    print("ERROR: GEMINI_API_KEY environment variable not set.")
    print("Please set it using: export GEMINI_API_KEY='your-api-key'")
    sys.exit(1)

genai.configure(api_key=GEMINI_API_KEY)


class KnowledgeBaseIngestor:
    """Handles ingestion of documents into ChromaDB with Gemini embeddings."""

    def __init__(self):
        """Initialize the ingestor with ChromaDB client."""
        self.chroma_client = chromadb.PersistentClient(
            path=str(CHROMA_DB_DIR),
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True,
            )
        )
        self.collection = None
        self.embedding_model = "models/embedding-001"

    def load_documents(self) -> List[Document]:
        """Load all documents from the KnowledgeBase folder."""
        documents = []
        
        if not KNOWLEDGE_BASE_DIR.exists():
            print(f"ERROR: KnowledgeBase directory not found at {KNOWLEDGE_BASE_DIR}")
            print("Please create the directory and add your documents.")
            return documents

        print(f"Loading documents from {KNOWLEDGE_BASE_DIR}...")

        # Load PDF files
        for pdf_file in KNOWLEDGE_BASE_DIR.glob("*.pdf"):
            print(f"  Loading PDF: {pdf_file.name}")
            try:
                loader = PyPDFLoader(str(pdf_file))
                docs = loader.load()
                for doc in docs:
                    doc.metadata["source"] = pdf_file.name
                    doc.metadata["file_type"] = "pdf"
                documents.extend(docs)
            except Exception as e:
                print(f"    ERROR loading {pdf_file.name}: {e}")

        # Load TXT files
        for txt_file in KNOWLEDGE_BASE_DIR.glob("*.txt"):
            print(f"  Loading TXT: {txt_file.name}")
            try:
                loader = TextLoader(str(txt_file))
                docs = loader.load()
                for doc in docs:
                    doc.metadata["source"] = txt_file.name
                    doc.metadata["file_type"] = "txt"
                documents.extend(docs)
            except Exception as e:
                print(f"    ERROR loading {txt_file.name}: {e}")

        # Load Markdown files
        for md_file in KNOWLEDGE_BASE_DIR.glob("*.md"):
            print(f"  Loading Markdown: {md_file.name}")
            try:
                loader = UnstructuredMarkdownLoader(str(md_file))
                docs = loader.load()
                for doc in docs:
                    doc.metadata["source"] = md_file.name
                    doc.metadata["file_type"] = "markdown"
                documents.extend(docs)
            except Exception as e:
                print(f"    ERROR loading {md_file.name}: {e}")

        print(f"Total documents loaded: {len(documents)}")
        return documents

    def split_documents(self, documents: List[Document]) -> List[Document]:
        """Split documents into chunks for better retrieval."""
        print("Splitting documents into chunks...")
        
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            separators=["\n\n", "\n", ". ", " ", ""],
        )

        chunks = text_splitter.split_documents(documents)
        print(f"Total chunks created: {len(chunks)}")
        return chunks

    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for a text using Gemini."""
        try:
            result = genai.embed_content(
                model=self.embedding_model,
                content=text,
                task_type="retrieval_document",
            )
            return result["embedding"]
        except Exception as e:
            print(f"ERROR generating embedding: {e}")
            return [0.0] * 768  # Return zero vector on error

    def store_in_chromadb(self, chunks: List[Document]) -> None:
        """Store document chunks in ChromaDB with embeddings."""
        print("Storing chunks in ChromaDB...")

        # Delete existing collection if it exists
        try:
            self.chroma_client.delete_collection(COLLECTION_NAME)
            print(f"Deleted existing collection: {COLLECTION_NAME}")
        except:
            pass

        # Create new collection
        self.collection = self.chroma_client.create_collection(
            name=COLLECTION_NAME,
            metadata={"description": "Physiotherapy knowledge base"}
        )

        # Prepare data for batch insertion
        ids = []
        embeddings = []
        documents = []
        metadatas = []

        for idx, chunk in enumerate(chunks):
            chunk_id = f"chunk_{idx}"
            ids.append(chunk_id)
            
            # Generate embedding
            embedding = self.generate_embedding(chunk.page_content)
            embeddings.append(embedding)
            
            documents.append(chunk.page_content)
            
            # Prepare metadata
            metadata = {
                "source": chunk.metadata.get("source", "unknown"),
                "file_type": chunk.metadata.get("file_type", "unknown"),
                "chunk_index": idx,
            }
            metadatas.append(metadata)

        # Add to collection in batches
        batch_size = 100
        for i in range(0, len(ids), batch_size):
            batch_ids = ids[i:i+batch_size]
            batch_embeddings = embeddings[i:i+batch_size]
            batch_documents = documents[i:i+batch_size]
            batch_metadatas = metadatas[i:i+batch_size]
            
            self.collection.add(
                ids=batch_ids,
                embeddings=batch_embeddings,
                documents=batch_documents,
                metadatas=batch_metadatas,
            )
            print(f"  Added batch {i//batch_size + 1}/{(len(ids)-1)//batch_size + 1}")

        print(f"Successfully stored {len(ids)} chunks in ChromaDB")
        print(f"Collection name: {COLLECTION_NAME}")
        print(f"Database location: {CHROMA_DB_DIR}")

    def run(self) -> None:
        """Run the complete ingestion pipeline."""
        print("=" * 60)
        print("PhysioVision Knowledge Base Ingestion")
        print("=" * 60)
        
        # Load documents
        documents = self.load_documents()
        if not documents:
            print("ERROR: No documents loaded. Aborting.")
            return

        # Split documents
        chunks = self.split_documents(documents)
        if not chunks:
            print("ERROR: No chunks created. Aborting.")
            return

        # Store in ChromaDB
        self.store_in_chromadb(chunks)

        print("=" * 60)
        print("Ingestion completed successfully!")
        print("=" * 60)


def main():
    """Main entry point for the ingestion script."""
    ingestor = KnowledgeBaseIngestor()
    ingestor.run()


if __name__ == "__main__":
    main()
