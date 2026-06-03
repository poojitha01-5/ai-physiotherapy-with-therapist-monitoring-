# RAG Chatbot Setup Guide

This guide explains how to set up and run the Gemini + ChromaDB + LangChain RAG chatbot for PhysioVision.

## Overview

The RAG (Retrieval-Augmented Generation) chatbot uses:
- **Gemini 2.5 Flash** for response generation
- **Gemini Embeddings** for document embeddings
- **ChromaDB** for vector storage and retrieval
- **LangChain** for document processing

## Prerequisites

1. Python 3.11 or higher
2. Gemini API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
3. MongoDB connection (existing setup)

## Installation

### 1. Install Dependencies

```bash
cd Backend/Backend
pip install -r rag_requirements.txt
```

### 2. Set Environment Variables

Set your Gemini API key:

```bash
export GEMINI_API_KEY='your-gemini-api-key-here'
```

For persistent setup, add this to your shell profile (~/.bashrc, ~/.zshrc, etc.):

```bash
echo 'export GEMINI_API_KEY="your-gemini-api-key-here"' >> ~/.bashrc
source ~/.bashrc
```

## Knowledge Base Setup

### 1. Prepare Documents

Place your physiotherapy-related documents in the `KnowledgeBase` folder:

```bash
cd Backend/Backend/KnowledgeBase
```

Supported formats:
- PDF files (*.pdf)
- Text files (*.txt)
- Markdown files (*.md)

Example documents to include:
- Rehabilitation guides
- Exercise protocols
- Posture correction techniques
- Pediatric rehabilitation resources
- Balance training exercises
- Strength training programs
- Exercise safety guidelines

### 2. Run Ingestion Script

Process documents and create embeddings:

```bash
cd Backend/Backend
python ingest_knowledge_base.py
```

This script will:
- Load all documents from KnowledgeBase folder
- Split documents into chunks (1000 characters with 200 overlap)
- Generate embeddings using Gemini
- Store embeddings in ChromaDB (persistent storage in `chroma_db` folder)

### 3. Verify Ingestion

Check if ChromaDB was created successfully:

```bash
ls -la Backend/Backend/chroma_db
```

You should see ChromaDB files indicating successful ingestion.

## Running the Chatbot

### Start the Backend Server

```bash
cd Backend/Backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

The chatbot will be available at: `http://127.0.0.1:8001/chats`

## API Usage

### Chat Endpoint

**POST** `/chats`

Request body:
```json
{
  "username": "user123",
  "user_input": "What exercises help with lower back pain?"
}
```

Response:
```json
{
  "response": "Based on the knowledge base, here are exercises that help with lower back pain...",
  "sources": ["rehabilitation_guide.pdf", "exercise_protocols.md"],
  "success": true
}
```

## Error Handling

The chatbot handles the following errors gracefully:

1. **API Key Missing**
   - Error: "GEMINI_API_KEY environment variable not set"
   - Solution: Set the GEMINI_API_KEY environment variable

2. **Database Missing**
   - Error: "ChromaDB directory not found"
   - Solution: Run the ingestion script first

3. **Knowledge Base Empty**
   - Error: "Collection is empty"
   - Solution: Add documents to KnowledgeBase folder and run ingestion script

4. **No Relevant Information**
   - Response: "I couldn't find relevant information in my knowledge base..."
   - This is normal when the query doesn't match any documents

## Troubleshooting

### Chatbot Not Initialized

If you see "RAG Chatbot not initialized" in the logs:

1. Check if GEMINI_API_KEY is set: `echo $GEMINI_API_KEY`
2. Verify ChromaDB exists: `ls Backend/Backend/chroma_db`
3. Check ingestion script output for errors
4. Restart the backend server

### No Responses

If the chatbot returns empty responses:

1. Verify documents were ingested successfully
2. Check if queries match document content
3. Review similarity threshold in `rag_chatbot.py` (default: 0.7)
4. Check Gemini API quota and limits

### Import Errors

If you get import errors:

```bash
pip install --upgrade langchain langchain-community chromadb google-generativeai
```

## File Structure

```
Backend/Backend/
├── KnowledgeBase/          # Place documents here
│   ├── *.pdf
│   ├── *.txt
│   └── *.md
├── chroma_db/             # Created by ingestion script
├── app/
│   ├── main.py           # FastAPI app (updated)
│   └── rag_chatbot.py    # New RAG chatbot module
├── ingest_knowledge_base.py  # New ingestion script
└── rag_requirements.txt  # New dependencies
```

## Modified Files

### New Files Created
1. `Backend/Backend/app/rag_chatbot.py` - RAG chatbot implementation
2. `Backend/Backend/ingest_knowledge_base.py` - Document ingestion script
3. `Backend/Backend/KnowledgeBase/` - Folder for documents
4. `Backend/Backend/rag_requirements.txt` - New dependencies
5. `Backend/Backend/RAG_CHATBOT_SETUP.md` - This setup guide

### Modified Files
1. `Backend/Backend/app/main.py` - Updated to use new RAG chatbot
   - Replaced Mistral-based imports with Gemini + ChromaDB
   - Updated chat endpoint to use new RAG pipeline
   - Added sources to response model

## Frontend Updates

The frontend chatbot (`app/chatbot/page.tsx`) has been updated to handle the new response format that includes sources. The sources are displayed below each bot response.

## Chatbot Behavior

The chatbot acts as a physiotherapy assistant specializing in:
- Rehabilitation exercises
- Posture correction
- Pediatric rehabilitation
- Balance training
- Strength exercises
- Exercise safety

It provides grounded responses based on the knowledge base and includes source document references for transparency.

## Maintenance

### Re-ingesting Documents

To update the knowledge base:

1. Add new documents to `KnowledgeBase` folder
2. Remove old documents if needed
3. Run ingestion script: `python ingest_knowledge_base.py`
4. Restart the backend server

### Clearing Database

To clear the ChromaDB and start fresh:

```bash
rm -rf Backend/Backend/chroma_db
python ingest_knowledge_base.py
```

## Performance Tips

1. **Chunk Size**: Adjust `CHUNK_SIZE` in `ingest_knowledge_base.py` (default: 1000)
2. **Top K Results**: Adjust `TOP_K_RESULTS` in `rag_chatbot.py` (default: 5)
3. **Similarity Threshold**: Adjust `SIMILARITY_THRESHOLD` in `rag_chatbot.py` (default: 0.7)

## Security Notes

- Never commit GEMINI_API_KEY to version control
- Use environment variables for sensitive data
- The ChromaDB is stored locally and not encrypted
- MongoDB connection uses existing credentials

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review logs in the backend server console
3. Verify all prerequisites are met
4. Ensure documents are in supported formats
