import os
import fitz
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def extract_text_from_pdf(file_path):
    doc = fitz.open(file_path)
    return "".join([page.get_text() for page in doc])

def analyze_cv_with_ai(text):
    prompt = f"""
    Tu es un expert en recrutement Tech pour Orange. 
    Analyse ce CV et extrait les infos en JSON. 
    L'ANALYSE DOIT ÊTRE EN FRANÇAIS, même si le CV est en anglais.
    
    Format JSON :
    {{
        "nom": "Prénom Nom",
        "email": "email",
        "competences": ["comp1", "comp2"],
        "experience": "Résumé court de l'expérience en français",
        "points_forts": ["point1", "point2"],
        "score_data": 0
    }}
    
    CV à analyser : {text}
    """
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "system", "content": "Tu es un assistant spécialisé en recrutement."},
                  {"role": "user", "content": prompt}],
        response_format={ "type": "json_object" }
    )
    return json.loads(response.choices[0].message.content)