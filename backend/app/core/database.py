from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.core.config import settings

connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

try:
    engine = create_engine(
        settings.DATABASE_URL,
        pool_pre_ping=True,
        connect_args=connect_args
    )
    with engine.connect() as conn:
        pass
except Exception:
    # Em caso de falha de conexão remota, fallback seguro para SQLite local
    from pathlib import Path
    fallback_path = settings.BASE_DIR / "local_sniper.db"
    settings.DATABASE_URL = f"sqlite:///{fallback_path}"
    engine = create_engine(
        settings.DATABASE_URL,
        pool_pre_ping=True,
        connect_args={"check_same_thread": False}
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def init_db():
    try:
        import app.models.base_models
        import app.models.agent_memory
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        pass

init_db()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
