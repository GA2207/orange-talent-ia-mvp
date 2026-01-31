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
    competences = Column(JSON)  # Liste des competences
    experience = Column(Text)   # Resume de l'experience
    points_forts = Column(JSON) # Liste des points forts
    score_global = Column(Integer, default=0)
    data_json = Column(JSON)    # Backup du JSON complet de l'IA
    created_at = Column(DateTime, default=datetime.utcnow)


# Creation de la table au demarrage
Base.metadata.create_all(bind=engine)


# Fonction utilitaire pour obtenir une session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
