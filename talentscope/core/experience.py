# -*- coding: utf-8 -*-
import re
from datetime import datetime
from typing import List, Optional

def extract_years_from_text(text: str) -> List[int]:
    # 1990 - 2030 arası yılları yakala
    matches = re.findall(r"\b(199\d|20[0-2]\d)\b", text)
    years = [int(m) for m in matches]
    return sorted(list(set(years)))

def extract_explicit_experience(text: str) -> List[float]:
    # "5 years", "3.5 yıl", "10+ years" gibi ifadeleri yakala
    # İngilizce ve Türkçe basit patternler
    patterns = [
        r"(\d+(?:\.\d+)?)\s*\+?\s*(?:years?|yrs?|yıl|senedir)",
        r"(?:experience|tecrübe)\s*:\s*(\d+(?:\.\d+)?)",
    ]
    vals = []
    text_lower = text.lower()
    for pat in patterns:
        for m in re.findall(pat, text_lower):
            try:
                vals.append(float(m))
            except:
                pass
    return vals

def estimate_experience_years(text: str) -> int:
    """
    Estimates total experience years from raw CV text using heuristics.
    1. Looks for explicit mentions (e.g. "5 years experience").
    2. Looks for date ranges (min year vs max year/now).
    3. Returns the maximum reasonable finding.
    """
    # 1. Explicit Mentions
    explicit_years = extract_explicit_experience(text)
    max_explicit = max(explicit_years) if explicit_years else 0.0

    # 2. Date Range Calculation
    years = extract_years_from_text(text)
    range_years = 0
    if years:
        min_year = years[0]
        max_year = years[-1]
        
        # Eğer sadece tek bir yıl varsa ve bu yıl eskiyse, bugüne kadar çalışıyor olabilir mi?
        # Veya mezuniyet yılı olabilir. Tek yıl çok güvenilir değil.
        # Ancak min ve max varsa aradaki farkı alalım.
        
        current_year = datetime.now().year
        # Eğer max_year gelecekteyse veya current'tan büyükse current al
        if max_year > current_year:
            max_year = current_year
            
        # Basit mantık: En son geçen yıl - en ilk geçen yıl.
        # Bu çok kaba bir tahmin (arada boşluklar olabilir), ama bir gösterge.
        diff = max_year - min_year
        
        # Eğer en son tarih günümüze yakınsa (son 2 yıl), adayın hala aktif olduğunu varsayıp
        # başlangıçtan bugüne kadar diyebiliriz.
        if (current_year - max_year) <= 1:
             diff = current_year - min_year
             
        range_years = diff

    # Mantıklı sınırlar (0 - 40 yıl)
    final_est = max(max_explicit, range_years)
    if final_est > 40: 
        final_est = 40 # Hata koruması (telefon numarası vs karışırsa)
        
    return int(round(final_est))
