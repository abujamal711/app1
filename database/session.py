from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# إنشاء محرك SQLite
engine = create_engine(
    settings.SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}  # ضروري لـ SQLite
)

# إنشاء جلسة محلية
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# القاعدة للنماذج
Base = declarative_base()

# Dependency للحصول على جلسة DB
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
