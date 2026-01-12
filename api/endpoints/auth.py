from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta

from app.database.session import get_db
from app.core import auth as core_auth
from app.database import models
from app.core.config import settings

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@router.post("/register")
def register_user(
    username: str,
    email: str,
    password: str,
    full_name: str = "",
    role: str = "viewer",
    db: Session = Depends(get_db)
):
    """تسجيل مستخدم جديد"""
    
    # التحقق من وجود المستخدم
    existing_user = db.query(models.User).filter(
        (models.User.username == username) | (models.User.email == email)
    ).first()
    
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="اسم المستخدم أو البريد الإلكتروني موجود مسبقًا"
        )
    
    # إنشاء مستخدم جديد
    hashed_password = core_auth.get_password_hash(password)
    
    user = models.User(
        username=username,
        email=email,
        full_name=full_name,
        hashed_password=hashed_password,
        role=models.UserRole(role)
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return {"message": "تم إنشاء الحساب بنجاح", "user_id": user.id}

@router.post("/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """تسجيل الدخول"""
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    
    if not user or not core_auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="اسم المستخدم أو كلمة المرور غير صحيحة",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=400,
            detail="الحساب معطل"
        )
    
    # إنشاء توكن
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = core_auth.create_access_token(
        data={"sub": user.username, "role": user.role.value},
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role.value,
            "full_name": user.full_name
        }
    }
