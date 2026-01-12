from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid
from datetime import datetime

from app.database.session import get_db
from app.database import models
from app.core.auth import verify_token
from app.rules_engine.classifier import RuleBasedClassifier, DEFAULT_RULES
from app.evidence.engine import EvidenceEngine
from app.core.config import settings

router = APIRouter()
evidence_engine = EvidenceEngine(settings.EVIDENCE_STORAGE_PATH)
classifier = RuleBasedClassifier(DEFAULT_RULES)

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """الحصول على المستخدم الحالي"""
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="توكن غير صالح")
    
    username = payload.get("sub")
    user = db.query(models.User).filter(models.User.username == username).first()
    
    if not user:
        raise HTTPException(status_code=401, detail="المستخدم غير موجود")
    
    return user

@router.post("/create")
def create_case(
    title: str = Form(...),
    description: str = Form(...),
    category: Optional[str] = Form(None),
    priority: str = Form("medium"),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """إنشاء قضية جديدة"""
    
    # توليد معرف فريد للقضية
    case_id = f"CASE-{uuid.uuid4().hex[:8].upper()}"
    
    # تحليل النص وتصنيفه
    classification = classifier.classify_text(description)
    
    # تحديد الفئة بناءً على التحليل
    if not category and classification:
        category = classification[0].category
    
    # إنشاء القضية
    case = models.Case(
        case_id=case_id,
        title=title,
        description=description,
        reporter_id=current_user.id,
        priority=priority,
        category=category or "unknown"
    )
    
    db.add(case)
    db.commit()
    db.refresh(case)
    
    return {
        "message": "تم إنشاء القضية بنجاح",
        "case_id": case.case_id,
        "classification": [c.__dict__ for c in classification]
    }

@router.get("/")
def get_cases(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    category: Optional[str] = None,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """الحصول على القضايا"""
    
    query = db.query(models.Case)
    
    # التصفية حسب الصلاحيات
    if current_user.role in [models.UserRole.VIEWER, models.UserRole.REPORTER]:
        query = query.filter(models.Case.reporter_id == current_user.id)
    
    # تطبيق الفلاتر
    if status:
        query = query.filter(models.Case.status == status)
    if priority:
        query = query.filter(models.Case.priority == priority)
    if category:
        query = query.filter(models.Case.category == category)
    
    cases = query.order_by(models.Case.created_at.desc()).all()
    
    return {"cases": cases}

@router.get("/{case_id}")
def get_case(
    case_id: str,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """الحصول على قضية محددة"""
    
    case = db.query(models.Case).filter(models.Case.case_id == case_id).first()
    
    if not case:
        raise HTTPException(status_code=404, detail="القضية غير موجودة")
    
    # التحقق من الصلاحيات
    if (current_user.role in [models.UserRole.VIEWER, models.UserRole.REPORTER] and 
        case.reporter_id != current_user.id):
        raise HTTPException(status_code=403, detail="غير مصرح لك بالوصول لهذه القضية")
    
    return {"case": case}
