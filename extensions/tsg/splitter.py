"""TSG Gazete Bölücü — OCR metin dosyalarından şirket ilanlarını ayıklar."""

import hashlib
import re
from typing import Dict, List, Optional

# Türkçe ay adı → ay numarası eşleştirmesi (OCR varyantları dahil)
MONTH_MAP: Dict[str, str] = {
    "OCAK": "01",
    "ŞUBAT": "02",
    "SUBAT": "02",
    "MART": "03",
    "NİSAN": "04",
    "NISAN": "04",
    "MAYIS": "05",
    "HAZİRAN": "06",
    "HAZIRAN": "06",
    "TEMMUZ": "07",
    "AĞUSTOS": "08",
    "AGUSTOS": "08",
    "EYLÜL": "09",
    "EYLUL": "09",
    "EKİM": "10",
    "EKIM": "10",
    "KASIM": "11",
    "ARALIK": "12",
}

# Gazete başlık kalıbı: "21 HAZİRAN 2024 SAYI : 11106"
_DATE_PATTERN = re.compile(
    r"(\d{1,2})\s+(" + "|".join(MONTH_MAP.keys()) + r")\s+(\d{4})",
    re.IGNORECASE | re.UNICODE,
)
_SAYI_PATTERN = re.compile(r"SAYI\s*:\s*(\d+)", re.IGNORECASE)

# Şirket ilanı ayraç kalıbı (T.C. prefix'li ve prefix'siz varyantlar)
_ANNOUNCEMENT_SPLIT_PATTERN = re.compile(
    r"(?=(?:T\.C\.\s+)?[\w\sİÇÖÜĞŞıçöüğş]+?Ticaret\s+Sicil[iİ]\s+Müdürlü[ğg]ü)",
    re.DOTALL | re.IGNORECASE | re.UNICODE,
)

# Agresif OCR normalizasyonu — Türkçe + aksan varyantları + Romen karışmaları
_NORMALIZE_MAP = str.maketrans({
    # Türkçe → ASCII
    'Ğ': 'G', 'ğ': 'g', 'İ': 'I', 'ı': 'i',
    'Ö': 'O', 'ö': 'o', 'Ü': 'U', 'ü': 'u',
    'Ş': 'S', 'ş': 's', 'Ç': 'C', 'ç': 'c',
    # OCR aksan hataları
    'Í': 'I', 'í': 'i', 'Ì': 'I', 'ì': 'i', 'Î': 'I', 'î': 'i',
    'É': 'E', 'é': 'e', 'È': 'E', 'è': 'e', 'Ë': 'E', 'ë': 'e', 'Ê': 'E', 'ê': 'e',
    'Ó': 'O', 'ó': 'o', 'Ò': 'O', 'ò': 'o', 'Ô': 'O', 'ô': 'o',
    'Ú': 'U', 'ú': 'u', 'Ù': 'U', 'ù': 'u', 'Û': 'U', 'û': 'u',
    'Á': 'A', 'á': 'a', 'À': 'A', 'à': 'a', 'Â': 'A', 'â': 'a',
    # Romen karakter karışmaları
    'Ș': 'S', 'ș': 's', 'Ț': 'T', 'ț': 't',
})


def normalize_ocr(text: str) -> str:
    """Türkçe + OCR varyant karakterleri ASCII'ye dönüştür."""
    return text.upper().translate(_NORMALIZE_MAP)


def validate_file_content(text: str) -> bool:
    """Metnin geçerli bir TSG OCR dosyası olup olmadığını kontrol eder.

    Returns:
        True ise geçerli TSG metni, False ise geçersiz.
    """
    if not text or len(text) < 100:
        return False

    indicators = ["TİCARET SİCİLİ", "SAYI", "Ticaret Unvanı"]
    return any(indicator in text for indicator in indicators)


def file_hash(text: str) -> str:
    """Metin içeriğinin MD5 hash değerini döndürür (tekrar tespiti için)."""
    return hashlib.md5(text.encode("utf-8")).hexdigest()


def extract_gazette_metadata(text: str) -> Dict[str, Optional[str]]:
    """Gazete tarih ve numarasını metinden çıkarır.

    Returns:
        {"date": "YYYY-MM-DD", "no": "gazete numarası"}
        Bulunamazsa ilgili değer None olur.
    """
    date_str: Optional[str] = None
    gazette_no: Optional[str] = None

    # Tarih eşleştirme
    date_match = _DATE_PATTERN.search(text)
    if date_match:
        day = date_match.group(1).zfill(2)
        month_name = date_match.group(2).upper()
        year = date_match.group(3)
        month = MONTH_MAP.get(month_name)
        if month:
            date_str = f"{year}-{month}-{day}"

    # Gazete sayı numarası
    sayi_match = _SAYI_PATTERN.search(text)
    if sayi_match:
        gazette_no = sayi_match.group(1)

    return {"date": date_str, "no": gazette_no}


def split_announcements(text: str) -> List[str]:
    """Gazete metnini bireysel şirket ilanlarına böler.

    Returns:
        Her biri bir şirket ilanı olan string listesi (boş olanlar dahil edilmez).
    """
    parts = _ANNOUNCEMENT_SPLIT_PATTERN.split(text)
    announcements = []
    for p in parts:
        stripped = p.strip()
        if not stripped or len(stripped) < 50:
            continue
        # İlan göstergesi var mı kontrol et (T.C. zorunlu değil)
        has_indicator = any(
            kw in stripped.lower()
            for kw in ["ticaret sicil", "ilan sıra", "ilan sira", "ticaret unvanı", "ticaret ünvanı", "mersis"]
        )
        if has_indicator:
            announcements.append(stripped)

    # Hiç ilan bulunamadıysa tüm metni tek ilan olarak ver
    if not announcements and len(text) > 100:
        announcements = [text]

    return announcements


def find_company_announcement(
    announcements: List[str], company_name: str
) -> Optional[str]:
    """Şirket adına göre ilgili ilanı bulur (büyük/küçük harf duyarsız, ilk 3 kelime eşleştirmesi).

    Args:
        announcements: split_announcements() tarafından döndürülen ilan listesi.
        company_name: Aranacak şirket adı.

    Returns:
        Eşleşen ilan metni veya bulunamazsa None.
    """
    if not company_name or not announcements:
        return None

    search_norm = normalize_ocr(company_name)
    # İlk 3 ve ilk 2 kelime varyantları
    search_words = search_norm.split()
    search_3 = " ".join(search_words[:3])
    search_2 = " ".join(search_words[:2])

    for announcement in announcements:
        ann_norm = normalize_ocr(announcement)
        if search_norm in ann_norm:
            return announcement
        if search_3 in ann_norm:
            return announcement

    # Kademe 2: ilk 2 kelime ile daha gevşek arama
    for announcement in announcements:
        ann_norm = normalize_ocr(announcement)
        if search_2 in ann_norm:
            return announcement

    return None
