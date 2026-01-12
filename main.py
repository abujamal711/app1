from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import uvicorn
import os
from pathlib import Path

from app.api.endpoints import auth, cases, evidence
from app.core.config import settings
from app.database.session import engine, Base

# إنشاء المجلدات الضرورية
def create_required_dirs():
    dirs = [
        "storage",
        "storage/evidence",
        "storage/databases",
        "logs"
    ]
    
    for dir_path in dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)

# إنشاء الجداول عند بدء التشغيل
@asynccontextmanager
async def lifespan(app: FastAPI):
    # عند البدء
    create_required_dirs()
    Base.metadata.create_all(bind=engine)
    
    # إنشاء مستخدم مسؤول افتراضي إذا لم يكن موجودًا
    from app.database.session import SessionLocal
    from app.database import models
    from app.core.auth import get_password_hash
    
    db = SessionLocal()
    try:
        admin_user = db.query(models.User).filter(
            models.User.username == "admin"
        ).first()
        
        if not admin_user:
            admin_user = models.User(
                username="admin",
                email="admin@cybershield.legal",
                full_name="System Administrator",
                hashed_password=get_password_hash("admin123"),
                role=models.UserRole.ADMIN
            )
            db.add(admin_user)
            db.commit()
            print("✅ تم إنشاء المستخدم المسؤول الافتراضي")
    except:
        pass
    finally:
        db.close()
    
    yield
    # عند الإغلاق

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    lifespan=lifespan
)

# إعداد CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # يمكن تضييق هذا لاحقًا
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# تسجيل الروابط
app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["authentication"])
app.include_router(cases.router, prefix=f"{settings.API_V1_STR}/cases", tags=["cases"])
app.include_router(evidence.router, prefix=f"{settings.API_V1_STR}/evidence", tags=["evidence"])

# خدمة الملفات الثابتة لواجهة المستخدم
app.mount("/static", StaticFiles(directory="app/frontend/assets"), name="static")

@app.get("/")
def read_root():
    return {
        "message": "مرحبًا بكم في نظام Abu Jamal CyberShield",
        "version": settings.VERSION,
        "status": "✅ يعمل بنجاح",
        "database": "SQLite (محلي)",
        "authentication": "JWT (محلي)",
        "storage": "Local Storage"
    }

@app.get("/health")
def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=not settings.IS_REPLIT  # إعادة التحميل التلقائي خارج Replit
    )
