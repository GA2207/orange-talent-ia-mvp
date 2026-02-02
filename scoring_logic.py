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
    Inclut l'analyse des Soft Skills et du Fit Culturel Orange.
    """
    prompt = f"""
    Tu es un expert en recrutement Data/IA pour Orange.
    Compare ce candidat avec l'offre d'emploi ci-dessous.

    === REGLES STRICTES ===
    - Gere les synonymes FR/EN (ex: "Data Engineer" = "Ingenieur de donnees")
    - Sois flexible sur les technologies (ex: "AWS S3" compte pour "AWS")
    - Toutes les analyses DOIVENT etre en FRANCAIS
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

    === ANALYSE SOFT SKILLS (IMPORTANT) ===
    En plus des competences techniques, analyse les SOFT SKILLS du candidat.
    Cherche des indices dans le CV sur :
    1. TRAVAIL D'EQUIPE : Projets collaboratifs, methodologies Agile/Scrum, travail en squad
    2. COMMUNICATION : Vulgarisation technique, presentations, redaction de docs, formations donnees
    3. LEADERSHIP : Mentorat, gestion de projet, encadrement, prise d'initiative
    4. AUTONOMIE : Projets menes de bout en bout, auto-formation, side projects

    === FORMAT DE REPONSE (JSON) ===
    {{
        "score_total": int (0-100),
        "score_tech": int (0-100),
        "score_experience": int (0-100),
        "score_cloud": int (0-100),
        "score_soft_skills": int (0-100),
        "explication": "Explication technique detaillee en francais (2-3 phrases)",
        "analyse_comportementale": "Analyse des soft skills en francais (2-3 phrases sur le profil humain du candidat)",
        "soft_skills_detectes": ["Travail en equipe", "Communication", "Leadership", "Autonomie"],
        "points_forts_match": ["competence1", "competence2"],
        "gaps": ["competence manquante 1", "competence manquante 2"],
        "recommandation": "SHORTLIST" | "A_VERIFIER" | "NON_RETENU",
        "flags": ["Alertes objectives comme: Profil junior, Expert Cloud, etc."],
        "culture_fit": "Fort" | "Moyen" | "Faible"
    }}
    """

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": "Tu es un expert RH Orange. Tu ne dois JAMAIS tenir compte de l'age, du genre, de l'origine ou de la photo. Concentre-toi uniquement sur les competences techniques, l'experience et les soft skills. Reponds uniquement en JSON valide."
            },
            {"role": "user", "content": prompt}
        ],
        response_format={"type": "json_object"}
    )

    return json.loads(response.choices[0].message.content)
