from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
from dotenv import load_dotenv
import logging
import asyncio
import json

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="AI Interview System - Python Services",
    description="Microservices for LLM processing and Vector DB operations",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import service modules
from services.llm_service import LLMService
from services.vector_service import VectorService
from services.audio_processing import RealTimeVADStreamer

# Initialize services
llm_service = LLMService()
vector_service = VectorService()

# Request/Response models
class QuestionRequest(BaseModel):
    question: str
    context: str = ""

class QuestionResponse(BaseModel):
    answer: str
    model_used: str
    processing_time: float

class VectorSearchResponse(BaseModel):
    results: list
    query: str
    total_results: int

@app.get("/")
async def root():
    return {
        "service": "AI Interview System - Python Services",
        "status": "healthy",
        "endpoints": ["/llm/answer", "/vector/search", "/vector/ingest"]
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "services": {
            "llm": llm_service.is_ready(),
            "vector_db": vector_service.is_ready()
        }
    }

# F.0.2: LLM Q&A Endpoint
@app.post("/llm/answer", response_model=QuestionResponse)
async def answer_question(request: QuestionRequest):
    try:
        logger.info(f"Processing LLM question: {request.question[:50]}...")
        
        result = await llm_service.answer_question(
            question=request.question,
            context=request.context
        )
        
        return QuestionResponse(**result)
        
    except Exception as e:
        logger.error(f"LLM processing error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"LLM processing failed: {str(e)}")

# F.0.3: Vector Search Endpoint
@app.get("/vector/search", response_model=VectorSearchResponse)
async def search_vectors(query: str, limit: int = 5):
    try:
        logger.info(f"Vector search query: {query}")
        
        results = await vector_service.search(query=query, limit=limit)
        
        return VectorSearchResponse(
            results=results,
            query=query,
            total_results=len(results)
        )
        
    except Exception as e:
        logger.error(f"Vector search error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Vector search failed: {str(e)}")

# Vector DB data ingestion endpoint
@app.post("/vector/ingest")
async def ingest_documents(documents: list[dict]):
    try:
        logger.info(f"Ingesting {len(documents)} documents")
        
        result = await vector_service.ingest_documents(documents)
        
        return {
            "status": "success",
            "documents_ingested": result["count"],
            "message": "Documents successfully ingested into vector database"
        }
        
    except Exception as e:
        logger.error(f"Document ingestion error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Document ingestion failed: {str(e)}")

# F.1.1: Streaming Audio WebSocket Endpoint
@app.websocket("/ws/stream/audio")
async def stream_audio(websocket: WebSocket):
    """
    WebSocket endpoint for streaming audio and detecting End-of-Turn (EoT).
    
    This endpoint:
    1. Accepts raw audio chunks from the client
    2. Uses VAD to detect speech activity
    3. Detects End-of-Turn when silence threshold is met
    4. Returns the complete audio buffer for transcription
    """
    await websocket.accept()
    logger.info("WebSocket audio stream connection established")
    
    # Initialize VAD streamer
    vad_streamer = RealTimeVADStreamer()
    
    try:
        while True:
            # Receive audio chunk from client
            data = await websocket.receive_bytes()
            
            # Log chunk size for debugging
            logger.debug(f"Received audio chunk: {len(data)} bytes")
            
            # Process chunk through VAD
            complete_audio = vad_streamer.process_chunk(data)
            
            # If EoT detected, send the complete audio buffer
            if complete_audio:
                logger.info(f"EoT detected, sending complete audio buffer: {len(complete_audio)} bytes")
                
                # Send EoT signal with audio data
                eot_message = {
                    "type": "eot",
                    "audio_size": len(complete_audio),
                    "vad_state": vad_streamer.get_state()
                }
                
                await websocket.send_text(json.dumps(eot_message))
                
                # Send the complete audio buffer
                await websocket.send_bytes(complete_audio)
                
                # Reset for next utterance
                vad_streamer = RealTimeVADStreamer()
                
            # Send periodic status updates
            elif len(data) > 0:  # Only send status for non-empty chunks
                status_message = {
                    "type": "status",
                    "vad_state": vad_streamer.get_state()
                }
                await websocket.send_text(json.dumps(status_message))
                
    except WebSocketDisconnect:
        logger.info("WebSocket audio stream connection closed")
    except Exception as e:
        logger.error(f"WebSocket audio stream error: {e}")
        try:
            await websocket.close()
        except:
            pass

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)