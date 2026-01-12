import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import uuid

class EvidenceEngine:
    def __init__(self, storage_path: Path):
        self.storage_path = storage_path
        storage_path.mkdir(parents=True, exist_ok=True)
    
    def store_evidence(self, file_content: bytes, case_id: str, evidence_type: str, 
                       source_url: Optional[str] = None) -> Dict[str, Any]:
        """تخزين الأدلة مع توليد البصمة والطابع الزمني"""
        
        # توليد معرف فريد للأدلة
        evidence_id = f"EVID-{uuid.uuid4().hex[:8].upper()}"
        
        # حساب البصمة
        file_hash = hashlib.sha256(file_content).hexdigest()
        
        # إنشاء اسم ملف فريد
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{evidence_id}_{timestamp}.dat"
        file_path = self.storage_path / filename
        
        # حفظ الملف
        file_path.write_bytes(file_content)
        
        # إنشاء البيانات الوصفية
        metadata = {
            "evidence_id": evidence_id,
            "case_id": case_id,
            "type": evidence_type,
            "hash": file_hash,
            "hash_algorithm": "sha256",
            "timestamp": datetime.now().isoformat(),
            "file_size": len(file_content),
            "file_path": str(file_path),
            "source_url": source_url,
            "integrity_verified": False
        }
        
        # حفظ البيانات الوصفية
        meta_path = file_path.with_suffix('.meta.json')
        with open(meta_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        return metadata
    
    def verify_integrity(self, evidence_id: str) -> bool:
        """التحقق من سلامة الدليل"""
        # البحث عن ملف الأدلة
        for file in self.storage_path.glob(f"*{evidence_id}*.dat"):
            meta_file = file.with_suffix('.meta.json')
            if meta_file.exists():
                with open(meta_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                
                # حساب البصمة الحالية
                current_content = file.read_bytes()
                current_hash = hashlib.sha256(current_content).hexdigest()
                
                # المقارنة
                if current_hash == metadata['hash']:
                    metadata['integrity_verified'] = True
                    with open(meta_file, 'w', encoding='utf-8') as f:
                        json.dump(metadata, f, ensure_ascii=False, indent=2)
                    return True
                else:
                    return False
        return False
