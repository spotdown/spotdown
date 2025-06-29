from fastapi import FastAPI, Form, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.downloader import process_spotify_url
import os

app = FastAPI()

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")


@app.get("/", response_class=HTMLResponse)
async def homepage(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/download")
async def download(request: Request, url: str = Form(...)):
    try:
        mp3_path = process_spotify_url(url)
        filename = os.path.basename(mp3_path)
        return FileResponse(path=mp3_path, filename=filename, media_type="audio/mpeg")
    except Exception as e:
        return templates.TemplateResponse("index.html", {
            "request": request,
            "error": str(e)
        })
