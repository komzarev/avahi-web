
import asyncio
import json
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List
from sse_starlette.sse import EventSourceResponse
from typing import Iterable
from pydantic.json import pydantic_encoder

from services_repository import MyServiceInfo, ServiceRepository

repo = ServiceRepository()
STREAM_DELAY = 5  # second
RETRY_TIMEOUT = 15000  # millisecond

app = FastAPI()

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/matrix")
async def index_matrix(request: Request):
    return templates.TemplateResponse("avahi_matrix.html", {"request": request})

@app.get("/")
async def index(request: Request):
    return templates.TemplateResponse("avahi.html", {"request": request})

@app.get('/api')
async def avahi_api(request: Request)->List[MyServiceInfo]:
    return repo.get_services()

class CommentUpdate(BaseModel):
    dev_name: str
    comment: str
    
@app.post('/set-comment')
async def set_comment(data: CommentUpdate, request: Request) -> str:
    host = data.dev_name.partition('.')[-1]
    if host:
        repo.set_service_comment(host,data.comment)
        return f"for {host} comment {data.comment} was set"
    return f"No host {host}"

async def event_generator(request: Request):
    def get_new_messages() -> Iterable:
        return [
            {
                "event": "new_message",
                "retry": RETRY_TIMEOUT,
                "data": json.dumps(repo.get_services(),default=pydantic_encoder)
            }
        ]
    while True:
        if await request.is_disconnected():
            break
        for message in get_new_messages():
            yield message
        await asyncio.sleep(STREAM_DELAY)

@app.get("/stream")
async def message_stream(request: Request):
    return EventSourceResponse(event_generator(request))