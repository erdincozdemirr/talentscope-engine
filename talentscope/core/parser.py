# -*- coding: utf-8 -*-
import re
from typing import Any, Dict, List, Optional

class CVParser:
    def __init__(self, text: str):
        self.raw_text = text
        self.clean_text = self._clean_whitespace(text)
        self.lines = [line.strip() for line in self.clean_text.split('\n') if line.strip()]

    def _clean_whitespace(self, text: str) -> str:
        return re.sub(r'\s+', ' ', text).strip()

    def parse(self) -> Dict[str, Any]:
        contact = self.extract_contact_info()
        sections = self.segment_sections()
        
        return {
            "personal": {
                "name": self.extract_name(), # Placeholder logic
                "location": "Unknown", # NLP gerektirir, şimdilik boş
                "email": contact.get("email"),
                "phone": contact.get("phone")
            },
            "education": self.parse_education(sections.get("EDUCATION", "")),
            "experience": self.parse_experience(sections.get("EXPERIENCE", "")),
            "skills": [], # API tarafında matcher.py ile doldurulacak
            "projects": self.parse_projects(sections.get("PROJECTS", "")),
            "certs": self.parse_certs(sections.get("CERTIFICATIONS", "")),
            "links": contact.get("links", {}),
            "salary": None # API tarafında CSV'den doldurulacak
        }

    def extract_contact_info(self) -> Dict[str, Any]:
        email_pattern = r"[\w\.-]+@[\w\.-]+\.\w+"
        phone_pattern = r"(\+90|0)?\s*[0-9]{3}\s*[0-9]{3}\s*[0-9]{2}\s*[0-9]{2}"
        link_pattern = r"(https?://)?(www\.)?([\w-]+\.)+(com|net|org|io)/[\w/-]+"
        
        email = re.search(email_pattern, self.raw_text)
        phone = re.search(phone_pattern, self.raw_text)
        
        links = {"other": []}
        for m in re.finditer(link_pattern, self.raw_text):
            url = m.group(0)
            if "linkedin" in url:
                links["linkedin"] = url
            elif "github" in url:
                links["github"] = url
            else:
                links["other"].append(url)
                
        return {
            "email": email.group(0) if email else None,
            "phone": phone.group(0) if phone else None,
            "links": links
        }

    def extract_name(self) -> str:
        # En basit mantık: İlk satır muhtemelen isimdir.
        # Header olmadığı sürece.
        if not self.lines:
            return "Unknown"
        
        candidate = self.lines[0]
        if len(candidate.split()) < 5: # Çok uzunsa isim değildir
            return candidate
        return "Unknown"

    def segment_sections(self) -> Dict[str, str]:
        # Basit keyword segmentation
        headers = {
            "EDUCATION": ["EDUCATION", "EĞİTİM", "ACADEMIC", "AKADEMİK"],
            "EXPERIENCE": ["EXPERIENCE", "DENEYİM", "WORK HISTORY", "İŞ GEÇMİŞİ", "EMPLOYMENT"],
            "PROJECTS": ["PROJECTS", "PROJELER", "PERSONAL PROJECTS"],
            "SKILLS": ["SKILLS", "YETENEKLER", "TECHNICAL SKILLS", "TEKNİK", "COMPETENCIES"],
            "CERTIFICATIONS": ["CERTIFICATIONS", "SERTİFİKALAR", "COURSES", "KURSLAR"]
        }
        
        map_sections = {}
        current_section = "SUMMARY"
        section_content = []
        
        # Line by line scanning
        for line in self.lines:
            upper_line = line.upper()
            
            # Check if line is a header
            found_header = None
            for key, keywords in headers.items():
                if any(k == upper_line for k in keywords) or any(f"{k}:" == upper_line for k in keywords):
                    found_header = key
                    break
            
            if found_header:
                if section_content:
                    map_sections[current_section] = "\n".join(section_content)
                current_section = found_header
                section_content = []
            else:
                section_content.append(line)
                
        if section_content:
             map_sections[current_section] = "\n".join(section_content)
             
        return map_sections

    def parse_education(self, text: str) -> List[Dict[str, Any]]:
        if not text:
            return []
        
        # Basit yıl ve okul yakalama
        results = []
        # Üniversite kelimesi geçen satırları bulmaya çalış
        lines = text.split('\n')
        current_edu = {}
        
        year_pattern = r"\b(19|20)\d{2}\b"
        
        for line in lines:
            years = re.findall(year_pattern, line)
            
            # Üniversite veya Lise bulursak yeni bir entry açalım
            if "UNIVERSITY" in line.upper() or "ÜNİVERSİTE" in line.upper() or "LİSE" in line.upper() or "COLLEGE" in line.upper():
                if current_edu:
                    results.append(current_edu)
                current_edu = {"school": line.strip(), "year": None, "degree": "Unknown"}
            
            if years and current_edu:
                current_edu["year"] = int(years[-1]) # En son geçen yıl mezuniyet yılıdır varsayımı
                
        if current_edu:
            results.append(current_edu)
            
        return results

    def parse_experience(self, text: str) -> List[Dict[str, Any]]:
        if not text:
            return []
            
        # Experience parsing is hard without NLP. Only capturing text blocks.
        # We can try to split by Date Ranges.
        # Pattern: Jan 2020 - Present, 2019-2021
        date_pattern = r"((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|Ocak|Şubat|Mart|Nisan|Mayıs|Haziran|Temmuz|Ağustos|Eylül|Ekim|Kasım|Aralık)?\s*\d{4})\s*[-–]\s*((?:Present|Current|Now|Devam|Halen)|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|Ocak|Şubat|Mart|Nisan|Mayıs|Haziran|Temmuz|Ağustos|Eylül|Ekim|Kasım|Aralık)?\s*\d{4})"
        
        entries = []
        lines = text.split('\n')
        
        current_exp = None
        
        for line in lines:
            match = re.search(date_pattern, line, re.IGNORECASE)
            if match:
                if current_exp:
                    entries.append(current_exp)
                
                start_date = match.group(1).strip()
                end_date = match.group(2).strip()
                
                # Title ve Company genellikle tarih satırının hemen öncesinde veya aynı satırda olur.
                # Şimdilik satırın geri kalanını title olarak alalım
                title_guess = line.replace(match.group(0), "").strip()
                if not title_guess:
                     title_guess = "Position"
                     
                current_exp = {
                    "title": title_guess,
                    "company": "Unknown", # Zor
                    "start": start_date,
                    "end": end_date,
                    "bullets": []
                }
            elif current_exp:
                # Bullet detection
                if line.strip().startswith(('-', '*', '•')):
                    current_exp["bullets"].append(line.strip().lstrip('-*• '))
                else:
                    # Append to description if not a bullet
                    pass
                    
        if current_exp:
            entries.append(current_exp)
            
        return entries

    def parse_projects(self, text: str) -> List[Dict[str, Any]]:
        # Projeleri ayırmak zor, şimdilik raw line'ları döndüreceğim ama liste formatında
        if not text:
            return []
        
        # Basitçe bullet point'leri proje gibi alabiliriz veya satır satır
        lines = [l for l in text.split('\n') if l.strip()]
        return [{"name": "Project Entry", "desc": l} for l in lines]

    def parse_certs(self, text: str) -> List[str]:
        if not text:
            return []
        return [l.strip() for l in text.split('\n') if l.strip()]
