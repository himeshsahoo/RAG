# Contextual AI Manual Reader 🧠

A dynamic, high-performance web application designed to let you easily "chat" with your technical manuals (PDFs and TXTs) using localized semantic search, powered by Large Language Models (LLMs).

## Overview

This project uses **Retrieval-Augmented Generation (RAG)** to provide accurate, context-aware answers based strictly on the documents you upload.

Initially built as a Streamlit application, it has been completely rewritten to use a robust **FastAPI backend** paired with a highly customized **HTML/JS/CSS frontend**. This decoupled architecture provides maximum flexibility, superior aesthetic control, and high responsiveness.

### Features
- **Local Document Processing**: Uses LangChain to chunk and store document contents locally using a ChromaDB vector store.
- **Strict Answering**: If the local model (`gemma4:e4b` via Ollama) cannot find the answer in the document, it refuses to hallucinate and defaults to a cloud fallback.
- **Cloud Fallback mechanism**: Automatically securely bundles the document context and prompts Google's Gemini Cloud (`gemini-2.5-flash`) for deeper reasoning if the local model is uncertain.
- **Modern UI**: Features glassmorphism, animated gradients, smooth scroll behaviors, and responsive dynamic chat elements—all built purely with Vanilla CSS and JS.

## Getting Started

### Prerequisites
1. **Python 3.8+**
2. **Ollama**: Ensure Ollama is running locally with the `gemma4:e4b` model installed (`ollama pull gemma4:e4b`).
3. **Gemini API Key**: For the cloud fallback mechanism.

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/himeshsahoo/RAG.git
   cd RAG
   ```

2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Setup your environment variables:
   - Create a `.env` file in the root directory.
   - Add your Gemini key
     ```env
     GEMINI_API_KEY=your_api_key_here
     ```

### Running the Application

Start the FastAPI server utilizing `uvicorn`:

```bash
uvicorn main:app --reload
```

Then, open your web browser and navigate to:
**[http://localhost:8000](http://localhost:8000)**

## Architecture Details
- **Backend (`main.py`)**: Defines the REST APIs (`/upload` and `/chat`) and handles all RAG operations using `langchain`, `chromadb`, and `huggingface-hub`.
- **Frontend (`static/`)**: Contains the static application assets:
  - `index.html`: Layout structure.
  - `style.css`: All the styling including the dynamic animations and glass effects.
  - `script.js`: Handles API calls via fetch, DOM manipulation, and frontend state management.
