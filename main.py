import os
import shutil
from fastapi import FastAPI, UploadFile, File, Request
from fastapi.templating import Jinja2Templates
from langdetect import detect
import fitz  # PyMuPDF

app = FastAPI()
templates = Jinja2Templates(directory="templates")
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.get("/")
async def home(request: Request):
    files = os.listdir(UPLOAD_DIR)
    return templates.TemplateResponse("index.html", {"request": request, "files": files})

@app.post("/upload")
async def upload_cv(file: UploadFile = File(...)):
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    
    # Sauvegarde locale
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Extraction rapide pour détecter la langue (MVP)
    doc = fitz.open(file_path)
    first_page_text = doc[0].get_text()
    try:
        lang = detect(first_page_text)
    except:
        lang = "inconnue"

    return {
        "filename": file.filename, 
        "langue_detectee": lang,
        "status": "Sauvegardé et analysé"
    }