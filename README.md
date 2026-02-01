# Orange Talent IA - MVP

Agent IA de gestion des recrutements Data/IA pour Orange.

## Fonctionnalites

- **Analyse de CV multilingue** : Traite les CV en francais et anglais
- **Scoring intelligent** : Compare les candidats a une offre de reference
- **Synonymes FR/EN** : "Data Engineer" = "Ingenieur de donnees"
- **Deduplication** : Mise a jour automatique si meme email
- **Recherche** : Filtrage par competences, nom, experience
- **Shortlist** : Classification automatique des candidats
- **Anti-biais** : Aucune donnee sensible (age, genre, origine)

## Installation

### 1. Cloner le projet

```bash
git clone https://github.com/GA2207/orange-talent-ia-mvp.git
cd orange-talent-ia-mvp
```

### 2. Creer l'environnement virtuel

```bash
python -m venv venv

# Windows
.\venv\Scripts\activate

# Mac/Linux
source venv/bin/activate
```

### 3. Installer les dependances

```bash
pip install -r requirements.txt
```

### 4. Configurer la cle API OpenAI

Creer un fichier `.env` a la racine :

```
OPENAI_API_KEY=sk-votre-cle-ici
```

### 5. Lancer le serveur

```bash
uvicorn main:app --reload
```

Ouvrir http://127.0.0.1:8000

## Structure du projet

```
orange-talent-ia-mvp/
├── app/
│   └── templates/
│       ├── dashboard.html    # Page d'accueil
│       └── candidat.html     # Fiche candidat
├── main.py                   # Routes FastAPI
├── parser_logic.py           # Extraction PDF + Analyse IA
├── scoring_logic.py          # Scoring intelligent
├── database.py               # Modele SQLAlchemy
├── job_description.json      # Offre de reference
├── requirements.txt          # Dependances Python
└── README.md
```

## Endpoints API

| Route | Methode | Description |
|-------|---------|-------------|
| `/` | GET | Dashboard principal |
| `/upload` | POST | Upload et analyse d'un CV |
| `/candidat/{id}` | GET | Fiche detaillee d'un candidat |
| `/search?query=` | GET | Recherche multilingue |
| `/shortlist` | GET | Candidats en shortlist |

## Technologies

- **Backend** : Python, FastAPI
- **Frontend** : HTML, Tailwind CSS
- **Database** : SQLite + SQLAlchemy
- **IA** : OpenAI GPT-4o

## Auteurs

Projet realise par des etudiants de La Plateforme (Marseille) - 2025
