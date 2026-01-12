from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
import aiofiles

from app.database.session import get_db
from app.database import models
from app.core.auth import verify_token, oauth2_scheme
from app.evidence.engine import EvidenceEngine
from app.core.config import settings

router = APIRouter()
evidence_engine = EvidenceEngine(settings.EVIDENCE_STORAGE_PATH)

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

@router.post("/upload")
async def upload_evidence(
    case_id: str = Form(...),
    evidence_type: str = Form(...),
    source_url: Optional[str] = Form(None),
    file: UploadFile = File(...),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """رفع أدلة جديدة"""
    
    # التحقق من وجود القضية
    case = db.query(models.Case).filter(models.Case.case_id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="القضية غير موجودة")
    
    # التحقق من الصلاحيات
    if current_user.role in [models.UserRole.VIEWER, models.UserRole.REPORTER]:
        if case.reporter_id != current_user.id:
            raise HTTPException(status_code=403, detail="غير مصرح لك بإضافة أدلة لهذه القضية")
    
    # قراءة الملف
    content = await file.read()
    
    # التحقق من حجم الملف
    if len(content) > settings.MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="حجم الملف يتجاوز الحد المسموح")
    
    # تخزين الدليل
    metadata = evidence_engine.store_evidence(
        file_content=content,
        case_id=case_id,
        evidence_type=evidence_type,
        source_url=source_url
    )
    
    # حفظ في قاعدة البيانات
    evidence = models.Evidence(
        evidence_id=metadata["evidence_id"],
        case_id=case.id,
        type=evidence_type,
        file_hash=metadata["hash"],
        file_path=metadata["file_path"],
        source_url=source_url,
        metadata=metadata
    )
    
    db.add(evidence)
    db.commit()
    
    return {
        "message": "تم رفع الدليل بنجاح",
        "evidence_id": metadata["evidence_id"],
        "hash": metadata["hash"]
    }

@router.get("/{evidence_id}/verify")
def verify_evidence(
    evidence_id: str,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """التحقق من سلامة الدليل"""
    
    evidence = db.query(models.Evidence).filter(models.Evidence.evidence_id == evidence_id).first()
    if not evidence:
        raise HTTPException(status_code=404, detail="الدليل غير موجود")
    
    # التحقق من الصلاحيات
    case = evidence.case
    if current_user.role in [models.UserRole.VIEWER, models.UserRole.REPORTER]:
        if case.reporter_id != current_user.id:
            raise HTTPException(status_code=403, detail="غير مصرح لك بالوصول لهذا الدليل")
    
    # التحقق من السلامة
    is_valid = evidence_engine.verify_integrity(evidence_id)
    
    # تحديث حالة التحقق في قاعدة البيانات
    evidence.integrity_verified = is_valid
    db.commit()
    
    return {
        "evidence_id": evidence_id,
        "integrity_verified": is_valid,
        "hash": evidence.file_hash
    }
