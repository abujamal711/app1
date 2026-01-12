import re
from typing import Dict, List, Tuple
from dataclasses import dataclass

@dataclass
class ClassificationResult:
    category: str
    confidence: float
    flags: List[str]

class RuleBasedClassifier:
    def __init__(self, rules: Dict):
        self.rules = rules
        
    def classify_text(self, text: str) -> List[ClassificationResult]:
        """تصنيف النص بناءً على القواعد"""
        results = []
        
        for category, patterns in self.rules.items():
            confidence, flags = self._evaluate_patterns(text, patterns)
            if confidence > 0:
                results.append(
                    ClassificationResult(
                        category=category,
                        confidence=confidence,
                        flags=flags
                    )
                )
        
        # ترتيب النتائج حسب درجة الثقة
        results.sort(key=lambda x: x.confidence, reverse=True)
        return results
    
    def _evaluate_patterns(self, text: str, patterns: Dict) -> Tuple[float, List[str]]:
        """تقييم النص مقابل الأنماط"""
        confidence = 0.0
        flags = []
        
        # فحص الكلمات المفتاحية
        for keyword in patterns.get("keywords", []):
            if keyword.lower() in text.lower():
                confidence += 0.2
                flags.append(f"الكلمة المفتاحية: {keyword}")
        
        # فحص التعبيرات النمطية
        for pattern in patterns.get("regex_patterns", []):
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                confidence += 0.3 * len(matches)
                flags.append(f"النمط: {pattern}")
        
        # الحد الأقصى للثقة هو 1.0
        confidence = min(confidence, 1.0)
        
        return confidence, flags

# قواعد التصنيف
DEFAULT_RULES = {
    "privacy_violation": {
        "keywords": ["خاص", "خصوصية", "صور خاصة", "مقاطع خاصة", "تسريب", "فضيحة"],
        "regex_patterns": [r"خاص[ة]?", r"سر[ي]?"]
    },
    "extortion": {
        "keywords": ["ابتزاز", "تهديد", "فدية", "دفع مبلغ", "إفلاس", "فضيحة"],
        "regex_patterns": [r"ابتزاز", r"تهديد", r"فدية"]
    },
    "hate_speech": {
        "keywords": ["كراهية", "عنصرية", "طائفي", "تحريض", "إهانة", "سب"],
        "regex_patterns": [r"كراهي[ة]?", r"عنصري[ة]?", r"طائفي[ة]?"]
    },
    "terrorism": {
        "keywords": ["تنظيم", "إرهاب", "تخريب", "تفجير", "سلاح", "قتل"],
        "regex_patterns": [r"تنظيم", r"إرهاب", r"تفجير"]
    },
    "copyright_violation": {
        "keywords": ["حقوق نشر", "محتوى مسروق", "انتحال", "نسخ", "سرقة أدبية"],
        "regex_patterns": [r"حقوق نشر", r"مسروق[ة]?"]
    }
}
