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

load_dotenv()

os.environ.setdefault("GOOGLE_API_KEY", os.getenv("GEMINI_API_KEY", ""))

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

agent = Agent(
    name="assistant",
    model="gemini-2.0-flash",
    instruction="You are a helpful assistant.",
)

session_service = InMemorySessionService()
runner = Runner(agent=agent, app_name="ssepoc", session_service=session_service)


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

    await session_service.create_session(
        app_name="ssepoc", user_id=user_id, session_id=session_id
    )

    content = types.Content(role="user", parts=[types.Part(text=last_message)])

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
