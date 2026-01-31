import os
import shutil
from fastapi import FastAPI, UploadFile, File, Request, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from parser_logic import extract_text_from_pdf, analyze_cv_with_ai
from database import SessionLocal, Candidat, Base, engine

# Creation des tables au demarrage
Base.metadata.create_all(bind=engine)

app = FastAPI()
templates = Jinja2Templates(directory="app/templates")
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


# Dependency pour obtenir la session DB
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/")
async def home(request: Request, db: Session = Depends(get_db)):
    # Recuperer tous les candidats de la base
    candidats_db = db.query(Candidat).order_by(Candidat.created_at.desc()).all()
    files = os.listdir(UPLOAD_DIR)
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "files": files,
        "candidats_db": candidats_db
    })


@app.post("/upload")
async def upload_cv(request: Request, file: UploadFile = File(...), db: Session = Depends(get_db)):
    file_path = os.path.join(UPLOAD_DIR, file.filename)

    # 1. Sauvegarde physique du fichier
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        return {"error": f"Erreur lors de la sauvegarde : {str(e)}"}

    # 2. Extraction et analyse IA
    try:
        raw_text = extract_text_from_pdf(file_path)
        candidat_data = analyze_cv_with_ai(raw_text)
        candidat_data["filename"] = file.filename

        # 3. Verification si le candidat existe deja (deduplication par email)
        existing = db.query(Candidat).filter(Candidat.email == candidat_data.get("email")).first()

        if existing:
            # Mise a jour du profil existant
            existing.nom = candidat_data.get("nom", existing.nom)
            existing.filename = file.filename
            existing.competences = candidat_data.get("competences", [])
            existing.experience = candidat_data.get("experience", "")
            existing.points_forts = candidat_data.get("points_forts", [])
            existing.score_global = candidat_data.get("score_data", 0)
            existing.data_json = candidat_data
            db.commit()
            candidat_id = existing.id
        else:
            # Creation d'un nouveau candidat
            nouveau_candidat = Candidat(
                nom=candidat_data.get("nom", "Inconnu"),
                email=candidat_data.get("email", ""),
                filename=file.filename,
                competences=candidat_data.get("competences", []),
                experience=candidat_data.get("experience", ""),
                points_forts=candidat_data.get("points_forts", []),
                score_global=candidat_data.get("score_data", 0),
                data_json=candidat_data
            )
            db.add(nouveau_candidat)
            db.commit()
            db.refresh(nouveau_candidat)
            candidat_id = nouveau_candidat.id

        # 4. Redirection vers la fiche du candidat
        return RedirectResponse(url=f"/candidat/{candidat_id}", status_code=303)

    except Exception as e:
        return {"error": f"Erreur lors de l'analyse IA : {str(e)}"}


@app.get("/candidat/{candidat_id}")
async def voir_candidat(request: Request, candidat_id: int, db: Session = Depends(get_db)):
    candidat = db.query(Candidat).filter(Candidat.id == candidat_id).first()
    if not candidat:
        return {"error": "Candidat non trouve"}

    # On passe l'objet candidat au template
    return templates.TemplateResponse("candidat.html", {
        "request": request,
        "candidat": {
            "id": candidat.id,
            "nom": candidat.nom,
            "email": candidat.email,
            "filename": candidat.filename,
            "competences": candidat.competences or [],
            "experience": candidat.experience or "",
            "points_forts": candidat.points_forts or [],
            "score_data": candidat.score_global
        }
    })
