import json
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def load_job_description(path="job_description.json"):
    """Charge l'offre d'emploi de reference."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def calculate_score_ai(candidate_data: dict, job_requirements: dict) -> dict:
    """
    Compare un candidat avec une offre d'emploi via l'IA.
    Gere les synonymes multilingues (Data Engineer = Ingenieur de donnees).
    Retourne un scoring detaille en francais avec flags ethiques.
    """
    prompt = f"""
    Tu es un expert en recrutement Data/IA pour Orange.
    Compare ce candidat avec l'offre d'emploi ci-dessous.

    IMPORTANT :
    - Gere les synonymes FR/EN (ex: "Data Engineer" = "Ingenieur de donnees", "Machine Learning" = "Apprentissage automatique")
    - Sois flexible sur les noms de technologies (ex: "AWS S3" compte pour "AWS")
    - L'explication DOIT etre en FRANCAIS
    - ANTI-BIAIS : Ne jamais mentionner age, genre, origine, photo ou toute donnee sensible

    === OFFRE D'EMPLOI ===
    Titre: {job_requirements.get('titre')}
    Skills requises: {job_requirements.get('skills_requises')}
    Skills bonus: {job_requirements.get('skills_bonus', [])}
    Experience minimum: {job_requirements.get('experience_min')} ans
    Cloud/DevOps: {job_requirements.get('mots_cles_cloud')}

    === CANDIDAT ===
    Nom: {candidate_data.get('nom')}
    Competences: {candidate_data.get('competences')}
    Experience: {candidate_data.get('experience')}
    Points forts: {candidate_data.get('points_forts')}

    === FORMAT DE REPONSE (JSON) ===
    {{
        "score_total": int (0-100),
        "score_tech": int (0-100),
        "score_experience": int (0-100),
        "score_cloud": int (0-100),
        "explication": "Explication detaillee en francais (2-3 phrases)",
        "points_forts_match": ["competence1", "competence2"],
        "gaps": ["competence manquante 1", "competence manquante 2"],
        "recommandation": "SHORTLIST" | "A_VERIFIER" | "NON_RETENU",
        "flags": ["Liste d'alertes objectives comme: Profil junior, Expert Cloud, Reconversion detectee, Surqualifie pour le poste, etc."]
    }}
    """

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "Tu es un assistant RH expert en recrutement tech. Reponds uniquement en JSON."},
            {"role": "user", "content": prompt}
        ],
        response_format={"type": "json_object"}
    )

    return json.loads(response.choices[0].message.content)
