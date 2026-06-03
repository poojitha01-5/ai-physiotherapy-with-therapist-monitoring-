# Next Steps - RAG Chatbot Implementation

## Current Chatbot Implementation Status

The PhysioVision chatbot has been successfully migrated from a Mistral-based fallback system to a complete Gemini + ChromaDB + LangChain RAG (Retrieval-Augmented Generation) implementation.

**Status:** Implementation complete, ready for configuration and testing

**Key Components:**
- RAG chatbot module using Gemini 2.5 Flash for response generation
- Gemini embeddings for vector similarity search
- ChromaDB for persistent vector storage
- LangChain for document processing and chunking
- Source document tracking in responses
- User context integration from MongoDB
- Comprehensive error handling

**Modified Files:**
- `Backend/Backend/app/main.py` - Updated to use new RAG chatbot
- `app/chatbot/page.tsx` - Updated to display sources in responses

**New Files Created:**
- `Backend/Backend/app/rag_chatbot.py` - RAG chatbot implementation
- `Backend/Backend/ingest_knowledge_base.py` - Document ingestion script
- `Backend/Backend/KnowledgeBase/` - Folder for documents
- `Backend/Backend/rag_requirements.txt` - New dependencies
- `Backend/Backend/RAG_CHATBOT_SETUP.md` - Detailed setup guide

## Required Environment Variables

### GEMINI_API_KEY
**Required:** Yes
**Description:** API key for Google Gemini AI services
**How to obtain:** Get from [Google AI Studio](https://makersuite.google.com/app/apikey)
**Set command:**
```bash
export GEMINI_API_KEY='your-gemini-api-key-here'
```

**For persistent setup (add to ~/.bashrc or ~/.zshrc):**
```bash
echo 'export GEMINI_API_KEY="your-gemini-api-key-here"' >> ~/.bashrc
source ~/.bashrc
```

**Verification:**
```bash
echo $GEMINI_API_KEY
```

## Location of Ingestion Script

**File Path:** `Backend/Backend/ingest_knowledge_base.py`

**Purpose:** Processes documents from KnowledgeBase folder, generates embeddings, and stores them in ChromaDB

**Supported File Formats:**
- PDF files (*.pdf)
- Text files (*.txt)
- Markdown files (*.md)

**Configuration Parameters (in script):**
- `CHUNK_SIZE = 1000` - Character count per chunk
- `CHUNK_OVERLAP = 200` - Character overlap between chunks
- `COLLECTION_NAME = "physiotherapy_knowledge_base"` - ChromaDB collection name

## Required KnowledgeBase Folder Structure

**Location:** `Backend/Backend/KnowledgeBase/`

**Structure:**
```
Backend/Backend/KnowledgeBase/
├── rehabilitation_guide.pdf
├── exercise_protocols.md
├── posture_correction.txt
├── pediatric_rehabilitation.pdf
└── ...
```

**Requirements:**
- Folder must exist before running ingestion script
- Add your physiotherapy-related documents here
- Supported formats: PDF, TXT, MD
- No subdirectories (flat structure)

**Recommended Document Types:**
- Rehabilitation guides
- Exercise protocols
- Posture correction techniques
- Pediatric rehabilitation resources
- Balance training exercises
- Strength training programs
- Exercise safety guidelines

**Note:** If the folder is empty, the ingestion script will report no documents loaded and abort.

## Commands to Generate Embeddings

### 1. Navigate to Backend Directory
```bash
cd Backend/Backend
```

### 2. Install Dependencies (if not already installed)
```bash
pip install -r rag_requirements.txt
```

### 3. Set Environment Variable (if not already set)
```bash
export GEMINI_API_KEY='your-gemini-api-key-here'
```

### 4. Run Ingestion Script
```bash
python ingest_knowledge_base.py
```

**Expected Output:**
```
============================================================
PhysioVision Knowledge Base Ingestion
============================================================
Loading documents from /path/to/KnowledgeBase...
  Loading PDF: rehabilitation_guide.pdf
  Loading TXT: posture_correction.txt
  Loading Markdown: exercise_protocols.md
Total documents loaded: 3
Splitting documents into chunks...
Total chunks created: 45
Storing chunks in ChromaDB...
  Added batch 1/1
Successfully stored 45 chunks in ChromaDB
Collection name: physiotherapy_knowledge_base
Database location: /path/to/chroma_db
============================================================
Ingestion completed successfully!
============================================================
```

### 5. Verify ChromaDB Creation
```bash
ls -la chroma_db
```

**Expected:** ChromaDB files and folders should be present

## Commands to Start the Backend

### 1. Navigate to Backend Directory
```bash
cd Backend/Backend
```

### 2. Ensure Environment Variable is Set
```bash
echo $GEMINI_API_KEY
```

### 3. Start FastAPI Server
```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

**Expected Output:**
```
INFO:     Started server process
INFO:     Waiting for application startup.
Connected to the MongoDB database!
RAG Chatbot initialized successfully
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8001
```

**Server URL:** `http://127.0.0.1:8001`

**Chatbot Endpoint:** `http://127.0.0.1:8001/chats`

**Note:** The server will auto-reload when code changes are made (due to --reload flag)

## Commands to Test the Chatbot

### Using curl

**Test with a simple query:**
```bash
curl -X POST http://127.0.0.1:8001/chats \
  -H "Content-Type: application/json" \
  -d '{
    "username": "test_user",
    "user_input": "What exercises help with lower back pain?"
  }'
```

**Expected Response:**
```json
{
  "response": "Based on the knowledge base, here are exercises that help with lower back pain...",
  "sources": ["rehabilitation_guide.pdf", "exercise_protocols.md"],
  "success": true
}
```

### Using the Frontend

1. Start the Next.js frontend (if not already running):
```bash
cd /Users/poojitha/Desktop/PhysioVision-AI-Powered-Physiotherapy-System
npm run dev
```

2. Open browser to: `http://localhost:3000`

3. Log in with your credentials

4. Navigate to the chatbot page

5. Ask a physiotherapy-related question

**Expected Behavior:**
- Bot response appears with formatted text
- Sources are displayed below the response
- Response is grounded in the knowledge base documents

### Test Cases to Verify

**1. Basic Query:**
- Question: "What exercises help with lower back pain?"
- Expected: Relevant exercises with sources

**2. Pediatric Rehabilitation:**
- Question: "How do I approach pediatric rehabilitation?"
- Expected: Age-appropriate rehabilitation guidance with sources

**3. Posture Correction:**
- Question: "What are the best posture correction techniques?"
- Expected: Posture improvement methods with sources

**4. Exercise Safety:**
- Question: "What safety precautions should I take during strength training?"
- Expected: Safety guidelines with sources

**5. No Relevant Information:**
- Question: "What is the weather today?"
- Expected: "I couldn't find relevant information in my knowledge base..." with empty sources

## Troubleshooting

### Chatbot Not Initialized
**Error:** "RAG Chatbot not initialized"
**Solution:** 
- Verify GEMINI_API_KEY is set
- Run ingestion script to create ChromaDB
- Check ChromaDB folder exists

### No Documents Loaded
**Error:** "No documents loaded. Aborting."
**Solution:**
- Add documents to KnowledgeBase folder
- Verify file formats are supported (PDF, TXT, MD)
- Check file permissions

### API Key Error
**Error:** "GEMINI_API_KEY environment variable not set"
**Solution:**
- Set the environment variable
- Verify it's set with `echo $GEMINI_API_KEY`

### Import Errors
**Error:** Module import errors
**Solution:**
```bash
pip install --upgrade langchain langchain-community chromadb google-generativeai
```

## Additional Resources

- **Detailed Setup Guide:** `Backend/Backend/RAG_CHATBOT_SETUP.md`
- **Dependencies:** `Backend/Backend/rag_requirements.txt`
- **RAG Chatbot Code:** `Backend/Backend/app/rag_chatbot.py`
- **Ingestion Script:** `Backend/Backend/ingest_knowledge_base.py`

## Summary Checklist

- [ ] Obtain Gemini API key from Google AI Studio
- [ ] Set GEMINI_API_KEY environment variable
- [ ] Install dependencies from rag_requirements.txt
- [ ] Add physiotherapy documents to KnowledgeBase folder
- [ ] Run ingestion script to generate embeddings
- [ ] Verify ChromaDB was created successfully
- [ ] Start backend server
- [ ] Test chatbot with curl or frontend
- [ ] Verify sources are displayed in responses
