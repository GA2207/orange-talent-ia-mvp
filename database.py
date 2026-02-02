from sqlalchemy import create_engine, Column, Integer, String, JSON, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

DATABASE_URL = "sqlite:///./orange_talents.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Candidat(Base):
    __tablename__ = "candidats"

    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String(255))
    email = Column(String(255), unique=True, index=True)
    filename = Column(String(255))

    # Donnees extraites du CV
    competences = Column(JSON)
    experience = Column(Text)
    points_forts = Column(JSON)
    data_json = Column(JSON)

    # Scoring intelligent (Jour 4)
    score_global = Column(Integer, default=0)
    score_tech = Column(Integer, default=0)
    score_experience = Column(Integer, default=0)
    score_cloud = Column(Integer, default=0)
    explication_score = Column(Text)
    gaps = Column(JSON)  # Competences manquantes
    points_forts_match = Column(JSON)  # Competences qui matchent
    recommandation = Column(String(50))  # SHORTLIST, A_VERIFIER, NON_RETENU
    flags = Column(JSON)  # Alertes ethiques (Jour 5)

    # Soft Skills & Culture Fit (Jour 7)
    score_soft_skills = Column(Integer, default=0)
    analyse_comportementale = Column(Text)
    soft_skills_detectes = Column(JSON)
    culture_fit = Column(String(50))  # Fort, Moyen, Faible

    created_at = Column(DateTime, default=datetime.utcnow)


# Creation de la table au demarrage
Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
