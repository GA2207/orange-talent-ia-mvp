import os
import shutil
import csv
import io
from fastapi import FastAPI, UploadFile, File, Request, Depends, Query
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy import or_, cast, String

from parser_logic import extract_text_from_pdf, analyze_cv_with_ai
from scoring_logic import calculate_score_ai, load_job_description
from database import SessionLocal, Candidat, Base, engine

# Creation des tables au demarrage
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Orange Talent IA", version="1.0.0")
templates = Jinja2Templates(directory="app/templates")
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/")
async def home(request: Request, db: Session = Depends(get_db)):
    candidats_db = db.query(Candidat).order_by(Candidat.score_global.desc()).all()
    files = os.listdir(UPLOAD_DIR)
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "files": files,
        "candidats_db": candidats_db,
        "search_query": ""
    })


@app.get("/search")
async def search_candidates(
    request: Request,
    query: str = Query(default=""),
    db: Session = Depends(get_db)
):
    """Recherche multilingue dans les candidats."""
    if not query.strip():
        return RedirectResponse(url="/", status_code=303)

    # Recherche dans nom, email, competences (JSON stocke comme texte)
    search_term = f"%{query}%"
    results = db.query(Candidat).filter(
        or_(
            Candidat.nom.ilike(search_term),
            Candidat.email.ilike(search_term),
            cast(Candidat.competences, String).ilike(search_term),
            Candidat.experience.ilike(search_term)
        )
    ).order_by(Candidat.score_global.desc()).all()

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "files": [],
        "candidats_db": results,
        "search_query": query,
        "result_count": len(results)
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

        # 3. Scoring intelligent (Jour 4)
        job_reqs = load_job_description()
        scoring_result = calculate_score_ai(candidat_data, job_reqs)

        # 4. Verification si le candidat existe deja (deduplication par email)
        existing = db.query(Candidat).filter(Candidat.email == candidat_data.get("email")).first()

        if existing:
            # Mise a jour du profil existant
            existing.nom = candidat_data.get("nom", existing.nom)
            existing.filename = file.filename
            existing.competences = candidat_data.get("competences", [])
            existing.experience = candidat_data.get("experience", "")
            existing.points_forts = candidat_data.get("points_forts", [])
            existing.data_json = candidat_data
            # Scoring
            existing.score_global = scoring_result.get("score_total", 0)
            existing.score_tech = scoring_result.get("score_tech", 0)
            existing.score_experience = scoring_result.get("score_experience", 0)
            existing.score_cloud = scoring_result.get("score_cloud", 0)
            existing.explication_score = scoring_result.get("explication", "")
            existing.gaps = scoring_result.get("gaps", [])
            existing.points_forts_match = scoring_result.get("points_forts_match", [])
            existing.recommandation = scoring_result.get("recommandation", "A_VERIFIER")
            existing.flags = scoring_result.get("flags", [])
            # Soft Skills (Jour 7)
            existing.score_soft_skills = scoring_result.get("score_soft_skills", 0)
            existing.analyse_comportementale = scoring_result.get("analyse_comportementale", "")
            existing.soft_skills_detectes = scoring_result.get("soft_skills_detectes", [])
            existing.culture_fit = scoring_result.get("culture_fit", "Moyen")
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
                data_json=candidat_data,
                # Scoring
                score_global=scoring_result.get("score_total", 0),
                score_tech=scoring_result.get("score_tech", 0),
                score_experience=scoring_result.get("score_experience", 0),
                score_cloud=scoring_result.get("score_cloud", 0),
                explication_score=scoring_result.get("explication", ""),
                gaps=scoring_result.get("gaps", []),
                points_forts_match=scoring_result.get("points_forts_match", []),
                recommandation=scoring_result.get("recommandation", "A_VERIFIER"),
                flags=scoring_result.get("flags", []),
                # Soft Skills (Jour 7)
                score_soft_skills=scoring_result.get("score_soft_skills", 0),
                analyse_comportementale=scoring_result.get("analyse_comportementale", ""),
                soft_skills_detectes=scoring_result.get("soft_skills_detectes", []),
                culture_fit=scoring_result.get("culture_fit", "Moyen")
            )
            db.add(nouveau_candidat)
            db.commit()
            db.refresh(nouveau_candidat)
            candidat_id = nouveau_candidat.id

        # 5. Redirection vers la fiche du candidat
        return RedirectResponse(url=f"/candidat/{candidat_id}", status_code=303)

    except Exception as e:
        return {"error": f"Erreur lors de l'analyse IA : {str(e)}"}


@app.get("/candidat/{candidat_id}")
async def voir_candidat(request: Request, candidat_id: int, db: Session = Depends(get_db)):
    candidat = db.query(Candidat).filter(Candidat.id == candidat_id).first()
    if not candidat:
        return {"error": "Candidat non trouve"}

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
            # Scoring
            "score_global": candidat.score_global,
            "score_tech": candidat.score_tech,
            "score_experience": candidat.score_experience,
            "score_cloud": candidat.score_cloud,
            "explication_score": candidat.explication_score or "",
            "gaps": candidat.gaps or [],
            "points_forts_match": candidat.points_forts_match or [],
            "recommandation": candidat.recommandation or "A_VERIFIER",
            "flags": candidat.flags or [],
            # Soft Skills (Jour 7)
            "score_soft_skills": candidat.score_soft_skills or 0,
            "analyse_comportementale": candidat.analyse_comportementale or "",
            "soft_skills_detectes": candidat.soft_skills_detectes or [],
            "culture_fit": candidat.culture_fit or "Moyen"
        }
    })


@app.get("/shortlist")
async def shortlist(request: Request, db: Session = Depends(get_db)):
    """Affiche uniquement les candidats en shortlist, tries par score."""
    candidats_shortlist = db.query(Candidat).filter(
        Candidat.recommandation == "SHORTLIST"
    ).order_by(Candidat.score_global.desc()).all()

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "files": [],
        "candidats_db": candidats_shortlist,
        "search_query": "",
        "filter_mode": "shortlist"
    })


@app.post("/import-csv")
async def import_csv(request: Request, file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Import massif de candidats depuis un fichier CSV.
    Colonnes attendues: Nom, Email, Poste, Skills, Experience, Source
    Les candidats importes ont un score de 0 (en attente de CV).
    """
    try:
        content = await file.read()
        # Gestion encodage UTF-8 avec BOM ou sans
        try:
            decoded = content.decode('utf-8-sig')
        except:
            decoded = content.decode('utf-8')

        reader = csv.DictReader(io.StringIO(decoded))

        count_added = 0
        count_updated = 0
        count_skipped = 0

        for row in reader:
            email = row.get("Email", "").strip()
            if not email:
                count_skipped += 1
                continue

            # Verification doublon
            existing = db.query(Candidat).filter(Candidat.email == email).first()

            # Parser les skills (separees par virgules ou point-virgules)
            skills_raw = row.get("Skills", "") or row.get("Competences", "") or ""
            skills_list = [s.strip() for s in skills_raw.replace(";", ",").split(",") if s.strip()]

            if existing:
                # Mise a jour si le profil existe deja
                if not existing.competences or len(existing.competences) == 0:
                    existing.competences = skills_list
                if row.get("Poste"):
                    existing.experience = f"Poste actuel: {row.get('Poste')}"
                count_updated += 1
            else:
                # Creation d'un nouveau candidat "fantome" (sans CV)
                nouveau_candidat = Candidat(
                    nom=row.get("Nom", "").strip() or row.get("Name", "").strip() or "Inconnu",
                    email=email,
                    competences=skills_list,
                    experience=f"Poste: {row.get('Poste', 'Non specifie')}. Source: {row.get('Source', 'CSV Import')}",
                    score_global=0,
                    recommandation="A_VERIFIER",
                    flags=["Import CSV - En attente de CV"]
                )
                db.add(nouveau_candidat)
                count_added += 1

        db.commit()

        return templates.TemplateResponse("import_result.html", {
            "request": request,
            "count_added": count_added,
            "count_updated": count_updated,
            "count_skipped": count_skipped,
            "filename": file.filename
        })

    except Exception as e:
        return {"error": f"Erreur lors de l'import CSV : {str(e)}"}


@app.get("/import")
async def import_page(request: Request):
    """Page d'import CSV."""
    return templates.TemplateResponse("import.html", {"request": request})
