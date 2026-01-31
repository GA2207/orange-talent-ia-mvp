import os
import shutil
from fastapi import FastAPI, UploadFile, File, Request
from fastapi.templating import Jinja2Templates
from parser_logic import extract_text_from_pdf, analyze_cv_with_ai

app = FastAPI()
templates = Jinja2Templates(directory="app/templates")
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.get("/")
async def home(request: Request):
    files = os.listdir(UPLOAD_DIR)
    return templates.TemplateResponse("dashboard.html", {"request": request, "files": files})

@app.post("/upload")
async def upload_cv(request: Request, file: UploadFile = File(...)):
    # 1. Définir le chemin de sauvegarde
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    
    # 2. Sauvegarde physique du fichier
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        return {"error": f"Erreur lors de la sauvegarde : {str(e)}"}
    
    # 3. Extraction du texte (Appel à la logique du Jour 2)
    try:
        raw_text = extract_text_from_pdf(file_path)
        
        # 4. Analyse par l'IA (C'est ici que la magie opère)
        candidat_data = analyze_cv_with_ai(raw_text)
        
        # On ajoute le nom du fichier pour l'affichage
        candidat_data["filename"] = file.filename
        
        # 5. Redirection vers la fiche candidat détaillée
        return templates.TemplateResponse("candidat.html", {
            "request": request, 
            "candidat": candidat_data
        })
        
    except Exception as e:
        # En cas d'erreur IA ou PDF, on affiche l'erreur proprement
        return {"error": f"Erreur lors de l'analyse IA : {str(e)}"}