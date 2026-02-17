import os
import json
import uuid
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.agents.run_config import RunConfig, StreamingMode
from google.genai import types
from google import genai
from qdrant_client import AsyncQdrantClient

load_dotenv()

os.environ.setdefault("GOOGLE_API_KEY", os.getenv("GEMINI_API_KEY", ""))

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Qdrant setup
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION_NAME")

qdrant = AsyncQdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
genai_client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

agent = Agent(
    name="assistant",
    model="gemini-2.0-flash",
    instruction=(
        "You are a helpful assistant. Answer questions based on the provided context. "
        "If the context doesn't contain enough information to answer, let the user know."
    ),
)

session_service = InMemorySessionService()
runner = Runner(agent=agent, app_name="ssepoc", session_service=session_service)


async def get_relevant_context(query: str, limit: int = 5) -> str:
    embedding_result = await genai_client.aio.models.embed_content(
        model="gemini-embedding-001",
        contents=[query],
    )
    query_vector = embedding_result.embeddings[0].values

    results = await qdrant.query_points(
        collection_name=QDRANT_COLLECTION,
        query=query_vector,
        limit=limit,
    )

    contexts = []
    for point in results.points:
        payload = point.payload
        text = (
            payload.get("text")
            or payload.get("content")
            or payload.get("page_content")
            or str(payload)
        )
        contexts.append(text)

    return "\n\n---\n\n".join(contexts)


class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: List[Message]


@app.post("/chat")
async def chat(req: ChatRequest):
    user_messages = [m for m in req.messages if m.role == "user"]
    if not user_messages:
        return StreamingResponse(iter([]), media_type="text/event-stream")

    last_message = user_messages[-1].content
    session_id = str(uuid.uuid4())
    user_id = "user"

    # Retrieve relevant context from Qdrant
    context = await get_relevant_context(last_message)

    augmented_message = (
        f"Use the following context to answer the question. "
        f"If the context doesn't contain relevant information, say so.\n\n"
        f"Context:\n{context}\n\n"
        f"Question: {last_message}"
    )

    await session_service.create_session(
        app_name="ssepoc", user_id=user_id, session_id=session_id
    )

    content = types.Content(role="user", parts=[types.Part(text=augmented_message)])

    async def generate():
        run_config = RunConfig(streaming_mode=StreamingMode.SSE)
        async for event in runner.run_async(
            user_id=user_id, session_id=session_id, new_message=content,
            run_config=run_config,
        ):
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if hasattr(part, "text") and part.text:
                        yield f"data: {json.dumps({'type': 'token', 'content': part.text})}\n\n"

                for fc in event.get_function_calls():
                    yield f"data: {json.dumps({'type': 'tool_call', 'name': fc.name, 'args': dict(fc.args)})}\n\n"

            if event.is_final_response():
                yield f"data: {json.dumps({'type': 'done'})}\n\n"
                break

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-store, no-transform",
            "X-Accel-Buffering": "no",
        },
    )
