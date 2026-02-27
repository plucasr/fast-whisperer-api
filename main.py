from typing import Optional, List, Dict, Any
from fastapi import FastAPI, File, Form, HTTPException, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langchain_core.messages import HumanMessage
from agent_graph import app as agent_app
from chat_agent import app as chat_agent_app
import json
import asyncio
import uvicorn
from audio_utils import AudioProcessor, get_supported_languages

# Define Response Models
class AudioTranscriptionResponse(BaseModel):
    success: bool
    transcript: Optional[str] = None
    language: Optional[str] = None
    language_probability: Optional[float] = None
    duration: Optional[float] = None
    segments: Optional[List[Dict[str, Any]]] = None
    word_count: Optional[int] = None
    character_count: Optional[int] = None
    segment_count: Optional[int] = None
    average_confidence: Optional[float] = None
    model_info: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

# Initialize Audio Processor
audio_processor = AudioProcessor()

app = FastAPI(title="Lexios Whisperer API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.websocket("/chat/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            try:
                message_data = json.loads(data)
                user_message = message_data.get("message")
                messages = message_data.get("messages", [])
                
                if user_message:
                     # Construct history. If client sends full history, use it. 
                     # Otherwise, we might need to manage state here or rely on client to send history.
                     # For simplicity and statelessness matching the HTTP endpoint, let's assume client sends history + new message
                     # OR just the new message and we append to a list provided in 'messages'.
                     
                    lc_messages = []
                    for msg in messages:
                        if msg["role"] == "user":
                            lc_messages.append(HumanMessage(content=msg["content"]))
                        elif msg["role"] == "assistant":
                            # LangChain doesn't have a direct AIMessage(content=...) for input in this specific graph context usually,
                            # but standard is AIMessage.
                            from langchain_core.messages import AIMessage
                            lc_messages.append(AIMessage(content=msg["content"]))
                    
                    lc_messages.append(HumanMessage(content=user_message))
                    
                    initial_state = {"messages": lc_messages}

                    async for event in chat_agent_app.astream_events(initial_state, version="v2"):
                        kind = event["event"]
                        name = event.get("name", "Unknown")
                        data = event.get("data", {})
                        
                        # print(f"DEBUG: Event={kind}")
                        
                        if kind == "on_chat_model_stream":
                            chunk = event["data"]["chunk"]
                            content = chunk.content
                            if content:
                                await websocket.send_json({"chunk": content, "status": "streaming"})
                        elif kind == "on_tool_end":
                             # Handle tool output to send as a component
                             output = data.get("output")
                             # Check if it matches our DictionaryEntry structure (roughly)
                             # or check tool name if available in event metadata (usually in event['name'] or data)
                             if name == "DictionaryEntry":
                                 # Send a special component message
                                 # output should be the DictionaryEntry instance or dict
                                 props = output.dict() if hasattr(output, "dict") else output
                                 component_msg = {
                                     "type": "component",
                                     "name": "DictionaryWordView",
                                     "props": props,
                                     "status": "component"
                                 }
                                 await websocket.send_json(component_msg)

                        elif kind == "on_chat_model_end":
                            output = event["data"].get("output")
                            if output:
                                # Check for tool calls
                                tool_calls = getattr(output, "tool_calls", [])
                                if tool_calls:
                                    for tool_call in tool_calls:
                                        if tool_call["name"] == "DictionaryEntry":
                                            component_msg = {
                                                "type": "component",
                                                "name": "DictionaryWordView",
                                                "props": tool_call["args"],
                                                "status": "component"
                                            }
                                            await websocket.send_json(component_msg)

                                # Check for usage metadata
                                if hasattr(output, "usage_metadata"):
                                    await websocket.send_json({"usage": output.usage_metadata, "status": "usage"})
                        
                    await websocket.send_json({"status": "final"})
                    
            except json.JSONDecodeError:
                await websocket.send_json({"error": "Invalid JSON", "status": "error"})
            except Exception as e:
                print(f"Error in websocket loop: {e}")
                await websocket.send_json({"error": str(e), "status": "error"})

    except WebSocketDisconnect:
        print("Client disconnected")

@app.post("/transcribe", response_model=AudioTranscriptionResponse)
# ... (rest of file)
async def transcribe_audio(
    file: UploadFile = File(...),
    language: Optional[str] = Form(None),
    include_word_timestamps: bool = Form(True),
):
    """
    Transcribe an uploaded audio file using Whisper.

    Args:
        file: Audio file (mp3, wav, m4a, flac, etc.)
        language: Optional language code (e.g., 'en', 'pt', 'es'). Auto-detect if not provided.
        include_word_timestamps: Whether to include word-level timestamps (default: True)

    Returns:
        AudioTranscriptionResponse with transcript and detailed metadata
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    try:
        # Read file content
        content = await file.read()

        # Transcribe using AudioProcessor
        result = await audio_processor.transcribe_uploaded_file(
            file_content=content,
            filename=file.filename,
            language=language,
            include_word_timestamps=include_word_timestamps,
        )

        # Return result as response model
        if result["success"]:
            return AudioTranscriptionResponse(
                success=True,
                transcript=result["transcript"],
                language=result["language"],
                language_probability=result.get("language_probability"),
                duration=result["duration"],
                segments=result["segments"],
                word_count=result.get("word_count"),
                character_count=result.get("character_count"),
                segment_count=result.get("segment_count"),
                average_confidence=result.get("average_confidence"),
                model_info=result.get("model_info"),
            )
        else:
            return AudioTranscriptionResponse(
                success=False,
                transcript=None,
                language=None,
                duration=None,
                segments=None,
                error=result["error"],
            )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")


@app.get("/supported-languages")
def get_languages():
    """Get list of supported languages"""
    return {
        "languages": get_supported_languages(),
        "note": "Use language code as parameter, or omit for auto-detection",
    }


@app.get("/health")
def health_check():
    """Health check endpoint with system info"""
    return {
        "status": "healthy",
        "whisper_model": audio_processor.model_size,
        "supported_formats": list(AudioProcessor.SUPPORTED_FORMATS),
        "api_version": "1.1.0",
        "ai_hub": "active"
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
