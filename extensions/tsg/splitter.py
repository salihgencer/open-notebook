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

# Şirket ilanı ayraç kalıbı
_ANNOUNCEMENT_SPLIT_PATTERN = re.compile(
    r"(?=T\.C\..*?TİCARET\s+SİCİLİ\s+MÜDÜRLÜĞÜ)",
    re.DOTALL | re.IGNORECASE | re.UNICODE,
)


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
        # Boş veya çok kısa parçaları atla
        if not stripped or len(stripped) < 50:
            continue
        # Gazete başlık bölümünü atla (T.C. ile başlamayan parçalar)
        if not stripped.startswith("T.C."):
            continue
        announcements.append(stripped)
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

    # Arama için ilk 3 kelimeyi al
    search_words = company_name.upper().split()[:3]
    search_prefix = " ".join(search_words)

    for announcement in announcements:
        # "Ticaret Unvanı:" alanını bul
        unvan_match = re.search(
            r"Ticaret\s+Unvanı\s*:\s*(.+?)(?:\n|$)",
            announcement,
            re.IGNORECASE | re.UNICODE,
        )
        if unvan_match:
            unvan = unvan_match.group(1).strip().upper()
            unvan_words = unvan.split()[:3]
            unvan_prefix = " ".join(unvan_words)
            if search_prefix in unvan_prefix or unvan_prefix in search_prefix:
                return announcement
        # Alternatif: genel metin içinde ara
        if search_prefix in announcement.upper():
            return announcement

    return None
