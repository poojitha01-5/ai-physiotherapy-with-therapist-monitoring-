"""
RAG Chatbot using Gemini + ChromaDB + LangChain

This module implements a retrieval-augmented generation chatbot for physiotherapy
assistance using Gemini embeddings and Gemini 2.5 Flash for response generation.
"""

import os
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import chromadb
from chromadb.config import Settings
from google.generativeai import genai
import google.generativeai as genai

# Configuration
CHROMA_DB_DIR = Path(__file__).parent.parent / "chroma_db"
COLLECTION_NAME = "physiotherapy_knowledge_base"
EMBEDDING_MODEL = "models/embedding-001"
GENERATION_MODEL = "models/gemini-2.0-flash-exp"  # Gemini 2.5 Flash equivalent
TOP_K_RESULTS = 5
SIMILARITY_THRESHOLD = 0.7


class RAGChatbot:
    """RAG Chatbot for physiotherapy assistance using Gemini and ChromaDB."""

    def __init__(self):
        """Initialize the RAG chatbot with ChromaDB and Gemini."""
        self.chroma_client = None
        self.collection = None
        self.generation_model = None
        self.embedding_model = EMBEDDING_MODEL
        self.is_initialized = False
        self.error_message = None

        # Initialize components
        self._initialize()

    def _initialize(self) -> None:
        """Initialize ChromaDB client and Gemini models."""
        try:
            # Check for API key
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                raise ValueError("GEMINI_API_KEY environment variable not set")

            # Configure Gemini
            genai.configure(api_key=api_key)
            self.generation_model = genai.GenerativeModel(GENERATION_MODEL)

            # Initialize ChromaDB
            if not CHROMA_DB_DIR.exists():
                raise ValueError(
                    f"ChromaDB directory not found at {CHROMA_DB_DIR}. "
                    "Please run the ingestion script first."
                )

            self.chroma_client = chromadb.PersistentClient(
                path=str(CHROMA_DB_DIR),
                settings=Settings(anonymized_telemetry=False, allow_reset=True)
            )

            # Get or create collection
            try:
                self.collection = self.chroma_client.get_collection(COLLECTION_NAME)
                count = self.collection.count()
                if count == 0:
                    raise ValueError(f"Collection '{COLLECTION_NAME}' is empty")
                print(f"Connected to ChromaDB with {count} documents")
            except Exception as e:
                raise ValueError(
                    f"Collection '{COLLECTION_NAME}' not found or empty. "
                    f"Please run the ingestion script first. Error: {e}"
                )

            self.is_initialized = True

        except Exception as e:
            self.error_message = str(e)
            print(f"ERROR initializing RAG chatbot: {e}")

    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for a text using Gemini."""
        try:
            result = genai.embed_content(
                model=self.embedding_model,
                content=text,
                task_type="retrieval_query",
            )
            return result["embedding"]
        except Exception as e:
            print(f"ERROR generating embedding: {e}")
            raise

    def retrieve_relevant_chunks(
        self, query: str, top_k: int = TOP_K_RESULTS
    ) -> List[Dict[str, Any]]:
        """Retrieve relevant document chunks based on the query."""
        if not self.is_initialized:
            raise RuntimeError("Chatbot not initialized")

        try:
            # Generate query embedding
            query_embedding = self.generate_embedding(query)

            # Query ChromaDB
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                include=["documents", "metadatas", "distances"]
            )

            # Format results
            retrieved_chunks = []
            if results["documents"] and results["documents"][0]:
                for idx, (doc, metadata, distance) in enumerate(
                    zip(results["documents"][0], results["metadatas"][0], results["distances"][0])
                ):
                    # Convert distance to similarity score (ChromaDB uses cosine distance)
                    similarity = 1 - distance
                    if similarity >= SIMILARITY_THRESHOLD:
                        retrieved_chunks.append({
                            "content": doc,
                            "metadata": metadata,
                            "similarity": similarity,
                            "source": metadata.get("source", "unknown"),
                        })

            return retrieved_chunks

        except Exception as e:
            print(f"ERROR retrieving chunks: {e}")
            raise

    def generate_response(
        self, query: str, user_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate a response using RAG pipeline.

        Args:
            query: User's question
            user_context: Optional user context (age, condition, etc.)

        Returns:
            Dictionary containing response, sources, and metadata
        """
        if not self.is_initialized:
            return {
                "response": self.error_message or "Chatbot not initialized. Please check configuration.",
                "sources": [],
                "success": False,
            }

        try:
            # Retrieve relevant chunks
            retrieved_chunks = self.retrieve_relevant_chunks(query)

            if not retrieved_chunks:
                return {
                    "response": "I couldn't find relevant information in my knowledge base to answer your question. Please try rephrasing or ask a different question related to physiotherapy, rehabilitation, or exercise safety.",
                    "sources": [],
                    "success": True,
                }

            # Build context from retrieved chunks
            context_parts = []
            sources = set()
            for chunk in retrieved_chunks:
                context_parts.append(f"Source: {chunk['source']}\nContent: {chunk['content']}")
                sources.add(chunk['source'])

            context = "\n\n---\n\n".join(context_parts)

            # Build user context string if available
            user_context_str = ""
            if user_context:
                user_context_str = f"\nUser Context: {user_context}\n"

            # Build prompt for Gemini
            prompt = f"""You are a knowledgeable physiotherapy assistant specializing in rehabilitation, posture correction, pediatric rehabilitation, balance training, strength exercises, and exercise safety.

User Question: {query}{user_context_str}

Relevant Information from Knowledge Base:
{context}

Instructions:
1. Answer the user's question based primarily on the provided context.
2. If the context doesn't contain enough information, you can use your general knowledge about physiotherapy, but clearly indicate when you're doing so.
3. Provide accurate, safe, and helpful information.
4. Include practical advice when appropriate.
5. If the question is about a specific medical condition, always recommend consulting a healthcare professional.
6. Format your response in a clear, readable manner with appropriate paragraphs and bullet points.
7. Be concise but thorough.

Response:"""

            # Generate response using Gemini
            response = self.generation_model.generate_content(prompt)
            generated_text = response.text

            return {
                "response": generated_text,
                "sources": list(sources),
                "success": True,
                "retrieved_chunks_count": len(retrieved_chunks),
            }

        except Exception as e:
            print(f"ERROR generating response: {e}")
            return {
                "response": f"An error occurred while generating the response: {str(e)}",
                "sources": [],
                "success": False,
            }

    def chat(self, query: str, username: Optional[str] = None) -> Dict[str, Any]:
        """
        Main chat interface that handles user queries.

        Args:
            query: User's question
            username: Optional username for personalization

        Returns:
            Dictionary containing the response and metadata
        """
        # Get user context from database if username is provided
        user_context = None
        if username:
            try:
                from pymongo import MongoClient
                uri = os.getenv("MONGODB_URI", "mongodb+srv://abdullahmasood450:harry_potter123@cluster0.ys9yt.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
                client = MongoClient(uri)
                db = client["PhysioVision"]
                physical_attributes_collection = db["User_PhysicalAttributes"]
                user_doc = physical_attributes_collection.find_one({"username": username})
                if user_doc:
                    user_context = {
                        "age": user_doc.get("age"),
                        "sex": user_doc.get("sex"),
                        "bmi": user_doc.get("bmi"),
                        "pain_level": user_doc.get("pain_level"),
                        "pain_category": user_doc.get("pain_category"),
                        "hypertension": user_doc.get("hypertension"),
                        "diabetes": user_doc.get("diabetes"),
                    }
            except Exception as e:
                print(f"Warning: Could not fetch user context: {e}")

        # Generate response
        return self.generate_response(query, user_context)


# Singleton instance
_rag_chatbot_instance: Optional[RAGChatbot] = None


def get_rag_chatbot() -> RAGChatbot:
    """Get or create the singleton RAG chatbot instance."""
    global _rag_chatbot_instance
    if _rag_chatbot_instance is None:
        _rag_chatbot_instance = RAGChatbot()
    return _rag_chatbot_instance


def reset_rag_chatbot() -> None:
    """Reset the singleton RAG chatbot instance (useful for testing)."""
    global _rag_chatbot_instance
    _rag_chatbot_instance = None
