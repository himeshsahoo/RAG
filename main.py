import os
import tempfile
from contextlib import asynccontextmanager

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from dotenv import load_dotenv

from langchain_community.document_loaders import TextLoader, PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
# pyrefly: ignore [missing-import]
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_community.llms import Ollama
from langchain_classic.chains import create_retrieval_chain
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage

# Load environment variables
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

class AppState:
    def __init__(self):
        self.rag_chain = None
        self.current_file_name = None
        self.chat_history = []

state = AppState()

app = FastAPI(title="Contextual AI API")

# Ensure static directory exists
os.makedirs("static", exist_ok=True)

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def root():
    return FileResponse("static/index.html")

@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    if not file.filename.endswith(('.pdf', '.txt')):
        raise HTTPException(status_code=400, detail="Only PDF or TXT files allowed")

    if state.current_file_name != file.filename:
        state.rag_chain = None
        state.chat_history = []
        state.current_file_name = file.filename

    if state.rag_chain is None:
        try:
            file_extension = os.path.splitext(file.filename)[1]
            contents = await file.read()
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as tmp_file:
                tmp_file.write(contents)
                tmp_path = tmp_file.name

            if tmp_path.endswith('.pdf'):
                loader = PyPDFLoader(tmp_path)
            else:
                loader = TextLoader(tmp_path)
                
            docs = loader.load()
            
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
            splits = text_splitter.split_documents(docs)
            
            embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
            vectorstore = Chroma.from_documents(documents=splits, embedding=embeddings)
            
            llm = Ollama(model="gemma4:e4b")
            
            system_prompt = (
                "You are a strict technical manual reading assistant with memory of this conversation. "
                "Use the retrieved context to answer the question. "
                "CRITICAL: If the answer cannot be found in the context or conversation history, you MUST reply "
                "exactly with: 'I DO NOT KNOW'. Do not try to make up an answer.\n\n"
                "Context:\n{context}"
            )
            
            prompt = ChatPromptTemplate.from_messages([
                ("system", system_prompt),
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", "{input}"),
            ])
            
            question_answer_chain = create_stuff_documents_chain(llm, prompt)
            retriever = vectorstore.as_retriever(search_kwargs={"k": 3}) 
            
            state.rag_chain = create_retrieval_chain(retriever, question_answer_chain)
            os.remove(tmp_path)
            
            return {"message": "Document processed successfully"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    return {"message": "Document already loaded"}

class ChatMessage(BaseModel):
    message: str

@app.post("/chat")
async def chat(chat_message: ChatMessage):
    if state.rag_chain is None:
        raise HTTPException(status_code=400, detail="No document loaded")

    user_question = chat_message.message
    
    try:
        response = state.rag_chain.invoke({
            "input": user_question,
            "chat_history": state.chat_history
        })
        local_answer = response["answer"].strip()
        
        is_cloud = False
        final_answer = local_answer
        
        if "I DO NOT KNOW" in local_answer or len(local_answer) < 5:
            if not api_key:
                final_answer = "Gemma 4 doesn't know, and GEMINI_API_KEY is missing from your .env file to check the cloud."
            else:
                is_cloud = True
                retrieved_docs = response.get("context", [])
                context_text = "\n\n".join([doc.page_content for doc in retrieved_docs])
                
                gemini_prompt = (
                    f"You are helping a user analyze a manual because their local model couldn't find a direct match. "
                    f"Use the following source text pulled directly from the user's uploaded file to answer their question. "
                    f"If the text still doesn't contain the answer, use your general knowledge but mention that it wasn't explicitly found in the document.\n\n"
                    f"--- Document Snippets ---\n{context_text}\n---------------------\n\n"
                    f"User Question: {user_question}"
                )
                
                cloud_llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=api_key)
                cloud_response = cloud_llm.invoke(gemini_prompt)
                final_answer = cloud_response.content
        
        state.chat_history.append(HumanMessage(content=user_question))
        state.chat_history.append(AIMessage(content=final_answer))
        
        return {
            "answer": final_answer,
            "is_cloud": is_cloud
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
