
import json
from fastapi import FastAPI, Request,Form
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import search_devices
from typing import Annotated

app = FastAPI()

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def index(request: Request):
    merged_services = search_devices.get_services()
    return templates.TemplateResponse("avahi.html", {"request": request, "rows" : merged_services, "comments" : search_devices.comments})

@app.get('/api')
def avahi_api(request: Request):
    merged_services = search_devices.get_services()
    all = {}
    for service in merged_services:
        ret = {}
        ret["os_version"] = service[1]
        ret["name"] = service[2]
        ret["ip"] = service[3]
        ret["comment"] = search_devices.comments[ret["name"]] if ret["name"] in search_devices.comments else "" 
        all[ret["name"]] = ret 
    return JSONResponse(all)

class CommentUpdate(BaseModel):
    dev_name: str
    comment: str
    
@app.post('/set-comment')
def set_comment(data: CommentUpdate, request: Request):
    host = data.dev_name.partition('.')[-1]
    if host:
        search_devices.comments[host] = data.comment

    with open(search_devices.fileName, 'w') as f:
        json.dump(search_devices.comments, f)
    return f"for {data.dev_name} set comment {data.comment}"

