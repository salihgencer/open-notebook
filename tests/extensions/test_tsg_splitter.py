"""TSG Gazete Bölücü testleri."""

import pytest

from extensions.tsg.splitter import (
    validate_file_content,
    file_hash,
    extract_gazette_metadata,
    split_announcements,
    find_company_announcement,
)

# ---------------------------------------------------------------------------
# Örnek gazete metni — 2 şirket ilanı içeriyor
# ---------------------------------------------------------------------------

SAMPLE_GAZETTE = """=== STRUCTURED CONTENT ===
## text_blocks

21 HAZİRAN 2024 SAYI : 11106

T.C.
İSTANBUL TİCARET SİCİLİ MÜDÜRLÜĞÜ'NDEN

İlan Sıra No: 1
Ticaret Unvanı: ALFA TEKNOLOJİ ANONİM ŞİRKETİ
Mersis No: 0123456789012345
Tescil Tarihi: 15.06.2024

Şirketimizin ana sözleşmesinin 5. maddesi değiştirilmiştir. (20229115)
Yeni sermaye 1.000.000 TL olarak belirlenmiştir.
İlan olunur.

T.C.
ANKARA TİCARET SİCİLİ MÜDÜRLÜĞÜ'NDEN

İlan Sıra No: 2
Ticaret Unvanı: BETA YAZILIM LİMİTED ŞİRKETİ
Mersis No: 9876543210987654
Tescil Tarihi: 18.06.2024

Şirketimizin yönetim kurulu değişikliği tescil edilmiştir. (20229116)
Genel Kurul toplantısı yapılmış olup kararlar tescil edilmiştir.
İlan olunur.
"""

# ---------------------------------------------------------------------------
# validate_file_content testleri
# ---------------------------------------------------------------------------


def test_validate_valid_gazette():
    """Geçerli gazete metni True döndürmeli."""
    assert validate_file_content(SAMPLE_GAZETTE) is True


def test_validate_invalid_content():
    """TSG göstergesi olmayan metin False döndürmeli."""
    assert validate_file_content("Bu rastgele bir metin olup gazete içeriği değildir.") is False


def test_validate_too_short_content():
    """100 karakterden kısa metin False döndürmeli."""
    assert validate_file_content("TİCARET SİCİLİ") is False


def test_validate_empty_string():
    """Boş string False döndürmeli."""
    assert validate_file_content("") is False


# ---------------------------------------------------------------------------
# file_hash testleri
# ---------------------------------------------------------------------------


def test_file_hash_returns_string():
    """file_hash string döndürmeli."""
    result = file_hash(SAMPLE_GAZETTE)
    assert isinstance(result, str)


def test_file_hash_length():
    """MD5 hash 32 karakter uzunluğunda olmalı."""
    result = file_hash(SAMPLE_GAZETTE)
    assert len(result) == 32


def test_file_hash_deterministic():
    """Aynı metin için aynı hash üretilmeli."""
    assert file_hash(SAMPLE_GAZETTE) == file_hash(SAMPLE_GAZETTE)


def test_file_hash_different_texts():
    """Farklı metinler için farklı hash üretilmeli."""
    assert file_hash(SAMPLE_GAZETTE) != file_hash("farklı metin")


# ---------------------------------------------------------------------------
# extract_gazette_metadata testleri
# ---------------------------------------------------------------------------


def test_extract_metadata_date():
    """Gazete tarihi doğru formatta çıkarılmalı."""
    metadata = extract_gazette_metadata(SAMPLE_GAZETTE)
    assert metadata["date"] == "2024-06-21"


def test_extract_metadata_no():
    """Gazete numarası doğru çıkarılmalı."""
    metadata = extract_gazette_metadata(SAMPLE_GAZETTE)
    assert metadata["no"] == "11106"


def test_extract_metadata_ocr_variant():
    """OCR varyantı (AGUSTOS) doğru işlenmeli."""
    text = "15 AGUSTOS 2024 SAYI : 11200\nTİCARET SİCİLİ\nTicaret Unvanı: Test"
    metadata = extract_gazette_metadata(text)
    assert metadata["date"] == "2024-08-15"


def test_extract_metadata_missing_date():
    """Tarih olmayan metin için None döndürmeli."""
    text = "SAYI : 9999\nTİCARET SİCİLİ MÜDÜRLÜĞÜ"
    metadata = extract_gazette_metadata(text)
    assert metadata["date"] is None
    assert metadata["no"] == "9999"


def test_extract_metadata_returns_dict():
    """Sonuç her zaman dict olmalı."""
    metadata = extract_gazette_metadata("")
    assert isinstance(metadata, dict)
    assert "date" in metadata
    assert "no" in metadata


# ---------------------------------------------------------------------------
# split_announcements testleri
# ---------------------------------------------------------------------------


def test_split_returns_list():
    """split_announcements liste döndürmeli."""
    result = split_announcements(SAMPLE_GAZETTE)
    assert isinstance(result, list)


def test_split_correct_count():
    """Örnek gazete 2 ilan içermeli."""
    result = split_announcements(SAMPLE_GAZETTE)
    assert len(result) == 2


def test_split_announcements_contain_company_names():
    """Her ilan kendi şirket adını içermeli."""
    result = split_announcements(SAMPLE_GAZETTE)
    all_text = "\n".join(result)
    assert "ALFA TEKNOLOJİ" in all_text
    assert "BETA YAZILIM" in all_text


def test_split_empty_text():
    """Boş metin için boş liste döndürmeli."""
    result = split_announcements("")
    assert result == []


# ---------------------------------------------------------------------------
# find_company_announcement testleri
# ---------------------------------------------------------------------------


def test_find_company_found():
    """Şirket adıyla eşleşen ilan bulunmalı."""
    announcements = split_announcements(SAMPLE_GAZETTE)
    result = find_company_announcement(announcements, "ALFA TEKNOLOJİ")
    assert result is not None
    assert "ALFA TEKNOLOJİ" in result


def test_find_company_partial_match():
    """Kısmi şirket adıyla da ilan bulunabilmeli."""
    announcements = split_announcements(SAMPLE_GAZETTE)
    result = find_company_announcement(announcements, "BETA YAZILIM")
    assert result is not None
    assert "BETA YAZILIM" in result


def test_find_company_not_found():
    """Olmayan şirket için None döndürmeli."""
    announcements = split_announcements(SAMPLE_GAZETTE)
    result = find_company_announcement(announcements, "GAMMA HOLDİNG")
    assert result is None


def test_find_company_empty_announcements():
    """Boş liste için None döndürmeli."""
    result = find_company_announcement([], "ALFA TEKNOLOJİ")
    assert result is None


def test_find_company_empty_name():
    """Boş şirket adı için None döndürmeli."""
    announcements = split_announcements(SAMPLE_GAZETTE)
    result = find_company_announcement(announcements, "")
    assert result is None
