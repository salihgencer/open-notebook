# TSG Intelligence MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 36 şirketin 512 TSG dosyasını otomatik işleyip yapılandırılmış veritabanına yükleyen, chat ile güncel bilgiyi sorgulatan bir sistem.

**Architecture:** open-notebook'un mevcut extension altyapısı üzerine `extensions/tsg/` modülü eklenir. SurrealDB migration ile 8 yeni tablo oluşturulur. Extraction pipeline Gemma 4 ile iki aşamalı (triage + detay) çalışır. Chat router faktüel sorularda DB'den, analitik sorularda RAG'den cevap verir.

**Tech Stack:** Python 3.12, FastAPI, SurrealDB v2, Gemma 4 (uzak H100), Google Gemini Embedding 2, pytest

---

## File Map

### Backend — extensions/tsg/

| File | Responsibility |
|---|---|
| `extensions/tsg/__init__.py` | TSG package init |
| `extensions/tsg/models.py` | Pydantic models: Company, CompanyField, CompanyPerson, CompanyEvent, CompanyArticle, ArticleHistory, CompanyBranch, AuthorityMatrix |
| `extensions/tsg/migration.py` | SurrealDB migration: 8 ext_ tablo oluşturma |
| `extensions/tsg/splitter.py` | Gazete dosyasındaki ilanları ayırma |
| `extensions/tsg/extractor.py` | LLM ile yapılandırılmış veri çıkarma (triage + detay) |
| `extensions/tsg/state_manager.py` | Şirket güncel durumunu güncelleme (field, person, event, article) |
| `extensions/tsg/pipeline.py` | Tam extraction pipeline: doğrulama → bölme → eşleştirme → extraction → kaydetme |
| `extensions/tsg/bulk_loader.py` | Klasörden toplu yükleme scripti |
| `extensions/tsg/chat_router.py` | Hibrit sorgulama: faktüel/kronoloji/analitik/karşılaştırma yönlendirici |
| `extensions/tsg/report_router.py` | Rapor API'leri: şirket kartı, yönetim, sermaye, kronoloji |
| `extensions/tsg/prompts/triage.yaml` | Triage extraction prompt şablonu |
| `extensions/tsg/prompts/kurulus.yaml` | Kuruluş extraction prompt |
| `extensions/tsg/prompts/yonetim.yaml` | Yönetim değişikliği extraction prompt |
| `extensions/tsg/prompts/sermaye.yaml` | Sermaye değişikliği extraction prompt |
| `extensions/tsg/prompts/genel.yaml` | Genel/diğer işlem türleri extraction prompt |
| `extensions/tsg/prompts/chat_system.yaml` | Chat sistem prompt'u |

### Tests

| File | Responsibility |
|---|---|
| `tests/extensions/test_tsg_models.py` | Model unit tests |
| `tests/extensions/test_tsg_splitter.py` | İlan ayırma tests |
| `tests/extensions/test_tsg_extractor.py` | Extraction tests |
| `tests/extensions/test_tsg_state_manager.py` | State güncelleme tests |
| `tests/extensions/test_tsg_pipeline.py` | Pipeline integration tests |
| `tests/extensions/test_tsg_chat_router.py` | Chat router tests |
| `tests/extensions/test_tsg_report_router.py` | Report API tests |

---

## Task 1: DB Migration — 8 ext_ Tablo

**Files:**
- Create: `extensions/tsg/__init__.py`
- Create: `extensions/tsg/migration.py`
- Create: `tests/extensions/test_tsg_models.py`

- [ ] **Step 1: Write failing test for migration**

```python
# tests/extensions/test_tsg_models.py
import pytest
from extensions.tsg.migration import TSG_MIGRATION_SQL


def test_migration_sql_defines_all_tables():
    sql = TSG_MIGRATION_SQL
    assert "ext_company" in sql
    assert "ext_company_field" in sql
    assert "ext_company_person" in sql
    assert "ext_company_event" in sql
    assert "ext_company_article" in sql
    assert "ext_article_history" in sql
    assert "ext_company_branch" in sql
    assert "ext_authority_matrix" in sql


def test_migration_sql_defines_indexes():
    sql = TSG_MIGRATION_SQL
    assert "idx_company_mersis" in sql
    assert "idx_field_company" in sql
    assert "idx_person_company" in sql
    assert "idx_event_company" in sql
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run python -m pytest tests/extensions/test_tsg_models.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'extensions.tsg'`

- [ ] **Step 3: Implement migration**

Create `extensions/tsg/__init__.py`:

```python
"""TSG Intelligence — Ticaret Sicil Gazetesi akıllı analiz sistemi."""
```

Create `extensions/tsg/migration.py`:

```python
"""SurrealDB migration for TSG Intelligence tables."""

TSG_MIGRATION_SQL = """
-- ext_company: Şirket Ana Kaydı
DEFINE TABLE IF NOT EXISTS ext_company SCHEMAFULL;
DEFINE FIELD IF NOT EXISTS notebook_id ON ext_company TYPE option<string>;
DEFINE FIELD IF NOT EXISTS name ON ext_company TYPE string;
DEFINE FIELD IF NOT EXISTS old_names ON ext_company TYPE option<array>;
DEFINE FIELD IF NOT EXISTS short_name ON ext_company TYPE option<string>;
DEFINE FIELD IF NOT EXISTS mersis_no ON ext_company TYPE option<string>;
DEFINE FIELD IF NOT EXISTS ticaret_sicil_no ON ext_company TYPE option<string>;
DEFINE FIELD IF NOT EXISTS ticaret_sicil_mudurlugu ON ext_company TYPE option<string>;
DEFINE FIELD IF NOT EXISTS company_type ON ext_company TYPE option<string>;
DEFINE FIELD IF NOT EXISTS sector ON ext_company TYPE option<string>;
DEFINE FIELD IF NOT EXISTS status ON ext_company TYPE string DEFAULT "aktif";
DEFINE FIELD IF NOT EXISTS gazette_count ON ext_company TYPE int DEFAULT 0;
DEFINE FIELD IF NOT EXISTS last_gazette_date ON ext_company TYPE option<string>;
DEFINE FIELD IF NOT EXISTS last_gazette_no ON ext_company TYPE option<string>;
DEFINE FIELD IF NOT EXISTS created ON ext_company TYPE option<datetime>;
DEFINE FIELD IF NOT EXISTS updated ON ext_company TYPE option<datetime>;
DEFINE INDEX IF NOT EXISTS idx_company_mersis ON ext_company FIELDS mersis_no UNIQUE;
DEFINE INDEX IF NOT EXISTS idx_company_name ON ext_company FIELDS name;

-- ext_company_field: Güncel Durum Alanları
DEFINE TABLE IF NOT EXISTS ext_company_field SCHEMAFULL;
DEFINE FIELD IF NOT EXISTS company_id ON ext_company_field TYPE string;
DEFINE FIELD IF NOT EXISTS field_type ON ext_company_field TYPE string;
DEFINE FIELD IF NOT EXISTS value ON ext_company_field TYPE string;
DEFINE FIELD IF NOT EXISTS gazette_date ON ext_company_field TYPE option<string>;
DEFINE FIELD IF NOT EXISTS gazette_no ON ext_company_field TYPE option<string>;
DEFINE FIELD IF NOT EXISTS ilan_kodu ON ext_company_field TYPE option<string>;
DEFINE FIELD IF NOT EXISTS source_id ON ext_company_field TYPE option<string>;
DEFINE FIELD IF NOT EXISTS created ON ext_company_field TYPE option<datetime>;
DEFINE FIELD IF NOT EXISTS updated ON ext_company_field TYPE option<datetime>;
DEFINE INDEX IF NOT EXISTS idx_field_company ON ext_company_field FIELDS company_id;
DEFINE INDEX IF NOT EXISTS idx_field_type ON ext_company_field FIELDS company_id, field_type;

-- ext_company_person: Kişiler
DEFINE TABLE IF NOT EXISTS ext_company_person SCHEMAFULL;
DEFINE FIELD IF NOT EXISTS company_id ON ext_company_person TYPE string;
DEFINE FIELD IF NOT EXISTS person_type ON ext_company_person TYPE string;
DEFINE FIELD IF NOT EXISTS entity_type ON ext_company_person TYPE string DEFAULT "gercek_kisi";
DEFINE FIELD IF NOT EXISTS name ON ext_company_person TYPE string;
DEFINE FIELD IF NOT EXISTS role ON ext_company_person TYPE option<string>;
DEFINE FIELD IF NOT EXISTS tc_no ON ext_company_person TYPE option<string>;
DEFINE FIELD IF NOT EXISTS uyruk ON ext_company_person TYPE option<string>;
DEFINE FIELD IF NOT EXISTS temsilci_name ON ext_company_person TYPE option<string>;
DEFINE FIELD IF NOT EXISTS pay_amount ON ext_company_person TYPE option<string>;
DEFINE FIELD IF NOT EXISTS pay_ratio ON ext_company_person TYPE option<string>;
DEFINE FIELD IF NOT EXISTS imza_derecesi ON ext_company_person TYPE option<int>;
DEFINE FIELD IF NOT EXISTS imza_sekli ON ext_company_person TYPE option<string>;
DEFINE FIELD IF NOT EXISTS imza_grubu ON ext_company_person TYPE option<string>;
DEFINE FIELD IF NOT EXISTS gorev_baslangic ON ext_company_person TYPE option<string>;
DEFINE FIELD IF NOT EXISTS gorev_bitis ON ext_company_person TYPE option<string>;
DEFINE FIELD IF NOT EXISTS is_active ON ext_company_person TYPE bool DEFAULT true;
DEFINE FIELD IF NOT EXISTS gazette_date ON ext_company_person TYPE option<string>;
DEFINE FIELD IF NOT EXISTS source_id ON ext_company_person TYPE option<string>;
DEFINE FIELD IF NOT EXISTS created ON ext_company_person TYPE option<datetime>;
DEFINE FIELD IF NOT EXISTS updated ON ext_company_person TYPE option<datetime>;
DEFINE INDEX IF NOT EXISTS idx_person_company ON ext_company_person FIELDS company_id;
DEFINE INDEX IF NOT EXISTS idx_person_name ON ext_company_person FIELDS name;

-- ext_company_event: Kronoloji
DEFINE TABLE IF NOT EXISTS ext_company_event SCHEMAFULL;
DEFINE FIELD IF NOT EXISTS company_id ON ext_company_event TYPE string;
DEFINE FIELD IF NOT EXISTS source_id ON ext_company_event TYPE option<string>;
DEFINE FIELD IF NOT EXISTS gazette_date ON ext_company_event TYPE option<string>;
DEFINE FIELD IF NOT EXISTS gazette_no ON ext_company_event TYPE option<string>;
DEFINE FIELD IF NOT EXISTS ilan_kodu ON ext_company_event TYPE option<string>;
DEFINE FIELD IF NOT EXISTS event_type ON ext_company_event TYPE string;
DEFINE FIELD IF NOT EXISTS summary ON ext_company_event TYPE option<string>;
DEFINE FIELD IF NOT EXISTS old_value ON ext_company_event TYPE option<string>;
DEFINE FIELD IF NOT EXISTS new_value ON ext_company_event TYPE option<string>;
DEFINE FIELD IF NOT EXISTS delil_belgesi ON ext_company_event TYPE option<object>;
DEFINE FIELD IF NOT EXISTS raw_extraction ON ext_company_event TYPE option<object>;
DEFINE FIELD IF NOT EXISTS created ON ext_company_event TYPE option<datetime>;
DEFINE INDEX IF NOT EXISTS idx_event_company ON ext_company_event FIELDS company_id;
DEFINE INDEX IF NOT EXISTS idx_event_date ON ext_company_event FIELDS company_id, gazette_date;

-- ext_company_article: Esas Sözleşme Maddeleri
DEFINE TABLE IF NOT EXISTS ext_company_article SCHEMAFULL;
DEFINE FIELD IF NOT EXISTS company_id ON ext_company_article TYPE string;
DEFINE FIELD IF NOT EXISTS article_no ON ext_company_article TYPE int;
DEFINE FIELD IF NOT EXISTS article_title ON ext_company_article TYPE option<string>;
DEFINE FIELD IF NOT EXISTS current_text ON ext_company_article TYPE option<string>;
DEFINE FIELD IF NOT EXISTS gazette_date ON ext_company_article TYPE option<string>;
DEFINE FIELD IF NOT EXISTS gazette_no ON ext_company_article TYPE option<string>;
DEFINE FIELD IF NOT EXISTS source_id ON ext_company_article TYPE option<string>;
DEFINE FIELD IF NOT EXISTS version ON ext_company_article TYPE int DEFAULT 1;
DEFINE FIELD IF NOT EXISTS created ON ext_company_article TYPE option<datetime>;
DEFINE FIELD IF NOT EXISTS updated ON ext_company_article TYPE option<datetime>;
DEFINE INDEX IF NOT EXISTS idx_article_company ON ext_company_article FIELDS company_id;

-- ext_article_history: Sözleşme Değişiklik Geçmişi
DEFINE TABLE IF NOT EXISTS ext_article_history SCHEMAFULL;
DEFINE FIELD IF NOT EXISTS article_id ON ext_article_history TYPE string;
DEFINE FIELD IF NOT EXISTS company_id ON ext_article_history TYPE string;
DEFINE FIELD IF NOT EXISTS article_no ON ext_article_history TYPE int;
DEFINE FIELD IF NOT EXISTS article_title ON ext_article_history TYPE option<string>;
DEFINE FIELD IF NOT EXISTS old_text ON ext_article_history TYPE option<string>;
DEFINE FIELD IF NOT EXISTS new_text ON ext_article_history TYPE option<string>;
DEFINE FIELD IF NOT EXISTS change_summary ON ext_article_history TYPE option<string>;
DEFINE FIELD IF NOT EXISTS gazette_date ON ext_article_history TYPE option<string>;
DEFINE FIELD IF NOT EXISTS gazette_no ON ext_company_article TYPE option<string>;
DEFINE FIELD IF NOT EXISTS source_id ON ext_article_history TYPE option<string>;
DEFINE FIELD IF NOT EXISTS version ON ext_article_history TYPE int;
DEFINE FIELD IF NOT EXISTS created ON ext_article_history TYPE option<datetime>;

-- ext_company_branch: Şubeler
DEFINE TABLE IF NOT EXISTS ext_company_branch SCHEMAFULL;
DEFINE FIELD IF NOT EXISTS company_id ON ext_company_branch TYPE string;
DEFINE FIELD IF NOT EXISTS branch_name ON ext_company_branch TYPE option<string>;
DEFINE FIELD IF NOT EXISTS branch_address ON ext_company_branch TYPE option<string>;
DEFINE FIELD IF NOT EXISTS branch_sicil_no ON ext_company_branch TYPE option<string>;
DEFINE FIELD IF NOT EXISTS branch_mersis_no ON ext_company_branch TYPE option<string>;
DEFINE FIELD IF NOT EXISTS status ON ext_company_branch TYPE string DEFAULT "aktif";
DEFINE FIELD IF NOT EXISTS gazette_date ON ext_company_branch TYPE option<string>;
DEFINE FIELD IF NOT EXISTS source_id ON ext_company_branch TYPE option<string>;
DEFINE FIELD IF NOT EXISTS created ON ext_company_branch TYPE option<datetime>;
DEFINE FIELD IF NOT EXISTS updated ON ext_company_branch TYPE option<datetime>;

-- ext_authority_matrix: İmza Yetki Matrisi
DEFINE TABLE IF NOT EXISTS ext_authority_matrix SCHEMAFULL;
DEFINE FIELD IF NOT EXISTS company_id ON ext_authority_matrix TYPE string;
DEFINE FIELD IF NOT EXISTS scope ON ext_authority_matrix TYPE string DEFAULT "merkez";
DEFINE FIELD IF NOT EXISTS rule_no ON ext_authority_matrix TYPE option<string>;
DEFINE FIELD IF NOT EXISTS description ON ext_authority_matrix TYPE option<string>;
DEFINE FIELD IF NOT EXISTS monetary_limit ON ext_authority_matrix TYPE option<string>;
DEFINE FIELD IF NOT EXISTS required_signers ON ext_authority_matrix TYPE option<string>;
DEFINE FIELD IF NOT EXISTS min_degree ON ext_authority_matrix TYPE option<int>;
DEFINE FIELD IF NOT EXISTS signing_type ON ext_authority_matrix TYPE option<string>;
DEFINE FIELD IF NOT EXISTS notes ON ext_authority_matrix TYPE option<string>;
DEFINE FIELD IF NOT EXISTS ic_yonerge_ttsg_date ON ext_authority_matrix TYPE option<string>;
DEFINE FIELD IF NOT EXISTS ic_yonerge_ttsg_no ON ext_authority_matrix TYPE option<string>;
DEFINE FIELD IF NOT EXISTS gazette_date ON ext_authority_matrix TYPE option<string>;
DEFINE FIELD IF NOT EXISTS source_id ON ext_authority_matrix TYPE option<string>;
DEFINE FIELD IF NOT EXISTS created ON ext_authority_matrix TYPE option<datetime>;
DEFINE FIELD IF NOT EXISTS updated ON ext_authority_matrix TYPE option<datetime>;
DEFINE INDEX IF NOT EXISTS idx_authority_company ON ext_authority_matrix FIELDS company_id;
"""


async def run_tsg_migration() -> None:
    """Run TSG Intelligence migration on startup."""
    from open_notebook.database.repository import repo_query
    from loguru import logger

    try:
        await repo_query(TSG_MIGRATION_SQL)
        logger.success("TSG Intelligence migration completed")
    except Exception as e:
        logger.error(f"TSG migration failed: {e}")
        raise
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run python -m pytest tests/extensions/test_tsg_models.py -v`
Expected: All 2 tests PASS

- [ ] **Step 5: Commit**

```bash
git add extensions/tsg/ tests/extensions/test_tsg_models.py
git commit -m "feat(tsg): add SurrealDB migration for 8 ext_ tables"
```

---

## Task 2: Pydantic Models

**Files:**
- Create: `extensions/tsg/models.py`
- Modify: `tests/extensions/test_tsg_models.py`

- [ ] **Step 1: Write failing tests for models**

Add to `tests/extensions/test_tsg_models.py`:

```python
from extensions.tsg.models import (
    Company, CompanyField, CompanyPerson, CompanyEvent,
    CompanyArticle, ArticleHistory, CompanyBranch, AuthorityMatrix,
    FIELD_TYPES, EVENT_TYPES, PERSON_TYPES,
)


def test_company_creation():
    c = Company(name="AYDIN HOLDİNG A.Ş.", company_type="A.Ş.")
    assert c.name == "AYDIN HOLDİNG A.Ş."
    assert c.status == "aktif"
    assert c.gazette_count == 0


def test_company_field_creation():
    f = CompanyField(
        company_id="ext_company:abc",
        field_type="sermaye",
        value="50.000.000 TL",
        gazette_date="2024-06-21",
    )
    assert f.field_type == "sermaye"
    assert f.value == "50.000.000 TL"


def test_company_field_rejects_invalid_type():
    import pytest
    with pytest.raises(ValueError):
        CompanyField(
            company_id="ext_company:abc",
            field_type="invalid_type",
            value="test",
        )


def test_company_person_creation():
    p = CompanyPerson(
        company_id="ext_company:abc",
        person_type="yonetim",
        name="Turgut Aydın",
        role="YK Başkanı",
        imza_derecesi=1,
        imza_sekli="musterek",
    )
    assert p.is_active is True
    assert p.entity_type == "gercek_kisi"


def test_company_event_creation():
    e = CompanyEvent(
        company_id="ext_company:abc",
        event_type="yonetim",
        summary="YK yeniden belirlendi",
        gazette_date="2024-06-21",
    )
    assert e.event_type == "yonetim"


def test_field_types_constant():
    assert "sermaye" in FIELD_TYPES
    assert "adres" in FIELD_TYPES
    assert "faaliyet" in FIELD_TYPES


def test_event_types_constant():
    assert "kurulus" in EVENT_TYPES
    assert "sermaye" in EVENT_TYPES
    assert "yonetim" in EVENT_TYPES
    assert "tasfiye" in EVENT_TYPES
    assert "konkordato" in EVENT_TYPES


def test_person_types_constant():
    assert "yonetim" in PERSON_TYPES
    assert "ortak" in PERSON_TYPES
    assert "denetci" in PERSON_TYPES
    assert "tasfiye_memuru" in PERSON_TYPES
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run python -m pytest tests/extensions/test_tsg_models.py -v`
Expected: FAIL — `ImportError: cannot import name 'Company'`

- [ ] **Step 3: Implement models**

Create `extensions/tsg/models.py`:

```python
"""Pydantic models for TSG Intelligence."""

from typing import ClassVar, Dict, List, Literal, Optional
from pydantic import field_validator
from open_notebook.domain.base import ObjectModel

FIELD_TYPES = (
    "sermaye", "adres", "faaliyet", "temsil", "denetci", "sure", "hesap_donemi",
)

EVENT_TYPES = (
    "kurulus", "sermaye", "yonetim", "adres", "unvan", "faaliyet", "temsil",
    "denetci", "pay_devri", "ana_sozlesme_tadili", "ic_yonerge",
    "sube_acilis", "sube_kapanis", "merkez_nakli", "tasfiye", "terkin",
    "konkordato", "bolunme", "ek_tasfiye", "ttk198", "acentelik", "diger",
)

PERSON_TYPES = (
    "yonetim", "ortak", "denetci", "tasfiye_memuru", "konkordato_komiseri",
)


class Company(ObjectModel):
    table_name: ClassVar[str] = "ext_company"
    notebook_id: Optional[str] = None
    name: str
    old_names: Optional[List[str]] = None
    short_name: Optional[str] = None
    mersis_no: Optional[str] = None
    ticaret_sicil_no: Optional[str] = None
    ticaret_sicil_mudurlugu: Optional[str] = None
    company_type: Optional[str] = None
    sector: Optional[str] = None
    status: str = "aktif"
    gazette_count: int = 0
    last_gazette_date: Optional[str] = None
    last_gazette_no: Optional[str] = None


class CompanyField(ObjectModel):
    table_name: ClassVar[str] = "ext_company_field"
    company_id: str
    field_type: str
    value: str
    gazette_date: Optional[str] = None
    gazette_no: Optional[str] = None
    ilan_kodu: Optional[str] = None
    source_id: Optional[str] = None

    @field_validator("field_type")
    @classmethod
    def validate_field_type(cls, v):
        if v not in FIELD_TYPES:
            raise ValueError(f"Invalid field_type: {v}. Must be one of {FIELD_TYPES}")
        return v


class CompanyPerson(ObjectModel):
    table_name: ClassVar[str] = "ext_company_person"
    company_id: str
    person_type: str
    entity_type: str = "gercek_kisi"
    name: str
    role: Optional[str] = None
    tc_no: Optional[str] = None
    uyruk: Optional[str] = None
    temsilci_name: Optional[str] = None
    pay_amount: Optional[str] = None
    pay_ratio: Optional[str] = None
    imza_derecesi: Optional[int] = None
    imza_sekli: Optional[str] = None
    imza_grubu: Optional[str] = None
    gorev_baslangic: Optional[str] = None
    gorev_bitis: Optional[str] = None
    is_active: bool = True
    gazette_date: Optional[str] = None
    source_id: Optional[str] = None


class CompanyEvent(ObjectModel):
    table_name: ClassVar[str] = "ext_company_event"
    company_id: str
    source_id: Optional[str] = None
    gazette_date: Optional[str] = None
    gazette_no: Optional[str] = None
    ilan_kodu: Optional[str] = None
    event_type: str
    summary: Optional[str] = None
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    delil_belgesi: Optional[Dict] = None
    raw_extraction: Optional[Dict] = None

    @field_validator("event_type")
    @classmethod
    def validate_event_type(cls, v):
        if v not in EVENT_TYPES:
            raise ValueError(f"Invalid event_type: {v}. Must be one of {EVENT_TYPES}")
        return v


class CompanyArticle(ObjectModel):
    table_name: ClassVar[str] = "ext_company_article"
    company_id: str
    article_no: int
    article_title: Optional[str] = None
    current_text: Optional[str] = None
    gazette_date: Optional[str] = None
    gazette_no: Optional[str] = None
    source_id: Optional[str] = None
    version: int = 1


class ArticleHistory(ObjectModel):
    table_name: ClassVar[str] = "ext_article_history"
    article_id: str
    company_id: str
    article_no: int
    article_title: Optional[str] = None
    old_text: Optional[str] = None
    new_text: Optional[str] = None
    change_summary: Optional[str] = None
    gazette_date: Optional[str] = None
    gazette_no: Optional[str] = None
    source_id: Optional[str] = None
    version: int = 0


class CompanyBranch(ObjectModel):
    table_name: ClassVar[str] = "ext_company_branch"
    company_id: str
    branch_name: Optional[str] = None
    branch_address: Optional[str] = None
    branch_sicil_no: Optional[str] = None
    branch_mersis_no: Optional[str] = None
    status: str = "aktif"
    gazette_date: Optional[str] = None
    source_id: Optional[str] = None


class AuthorityMatrix(ObjectModel):
    table_name: ClassVar[str] = "ext_authority_matrix"
    company_id: str
    scope: str = "merkez"
    rule_no: Optional[str] = None
    description: Optional[str] = None
    monetary_limit: Optional[str] = None
    required_signers: Optional[str] = None
    min_degree: Optional[int] = None
    signing_type: Optional[str] = None
    notes: Optional[str] = None
    ic_yonerge_ttsg_date: Optional[str] = None
    ic_yonerge_ttsg_no: Optional[str] = None
    gazette_date: Optional[str] = None
    source_id: Optional[str] = None
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run python -m pytest tests/extensions/test_tsg_models.py -v`
Expected: All 10 tests PASS

- [ ] **Step 5: Commit**

```bash
git add extensions/tsg/models.py tests/extensions/test_tsg_models.py
git commit -m "feat(tsg): add Pydantic models for 8 TSG tables"
```

---

## Task 3: Gazette Splitter

**Files:**
- Create: `extensions/tsg/splitter.py`
- Create: `tests/extensions/test_tsg_splitter.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/extensions/test_tsg_splitter.py
import pytest
from extensions.tsg.splitter import (
    extract_gazette_metadata,
    split_announcements,
    find_company_announcement,
    validate_file_content,
)


SAMPLE_GAZETTE = """=== STRUCTURED CONTENT ===

## text_blocks
- 21 HAZİRAN 2024 SAYI : 11106
- TÜRKİYE TİCARET SİCİLİ GAZETESİ
- SAYFA 890
- T.C. İSTANBUL TİCARET SİCİLİ MÜDÜRLÜĞÜ'NDEN
- İlan Sıra No: 45678 Mersis No: 0313060094100018 Ticaret Sicil/Dosya No: 123456
- Ticaret Unvanı: DREAM DERİCİLİK TEKSTİL LTD. ŞTİ.
- Adres: Ilica Mah. No:11 Manavgat/Antalya
- Tescil edilen hususlar: Yeni şube açılışı
- (20229115)
- T.C. İSTANBUL TİCARET SİCİLİ MÜDÜRLÜĞÜ'NDEN
- İlan Sıra No: 45679 Mersis No: 0115148655300001 Ticaret Sicil/Dosya No: 202494-5
- Ticaret Unvanı: AYDIN HOLDİNG ANONİM ŞİRKETİ
- Adres: Saray Mah. Naya Sk. Ümraniye/İstanbul
- Tescil edilen hususlar: Yönetim kurulu değişikliği
- (20229116)
"""


def test_validate_file_content_valid():
    assert validate_file_content(SAMPLE_GAZETTE) is True


def test_validate_file_content_too_short():
    assert validate_file_content("kısa") is False


def test_validate_file_content_not_gazette():
    assert validate_file_content("This is an LLM prompt template for..." * 10) is False


def test_extract_gazette_metadata():
    meta = extract_gazette_metadata(SAMPLE_GAZETTE)
    assert meta["date"] == "2024-06-21"
    assert meta["no"] == "11106"


def test_split_announcements():
    announcements = split_announcements(SAMPLE_GAZETTE)
    assert len(announcements) >= 2


def test_find_company_announcement():
    announcements = split_announcements(SAMPLE_GAZETTE)
    result = find_company_announcement(announcements, "AYDIN HOLDİNG")
    assert result is not None
    assert "AYDIN HOLDİNG" in result


def test_find_company_not_found():
    announcements = split_announcements(SAMPLE_GAZETTE)
    result = find_company_announcement(announcements, "NONEXISTENT ŞİRKET")
    assert result is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run python -m pytest tests/extensions/test_tsg_splitter.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement splitter**

Create `extensions/tsg/splitter.py`:

```python
"""Gazete dosyasındaki ilanları ayırma ve metadata çıkarma."""

import hashlib
import re
from typing import Dict, List, Optional

from loguru import logger

# Gazete tarih formatları
DATE_PATTERNS = [
    r"(\d{1,2})\s+(OCAK|ŞUBAT|MART|NİSAN|MAYIS|HAZİRAN|TEMMUZ|AĞUSTOS|EYLÜL|EKİM|KASIM|ARALIK)\s+(\d{4})\s+SAYI\s*:\s*(\d+)",
    r"(\d{1,2})\s+(AGUSTOS|HAZIRAN|ARALIK|KASIM|EKIM|EYLUL|TEMMUZ|NISAN|SUBAT|OCAK|MART|MAYIS)\s+(\d{4})\s+SAYI\s*:\s*(\d+)",
]

MONTH_MAP = {
    "OCAK": "01", "ŞUBAT": "02", "MART": "03", "NİSAN": "04",
    "MAYIS": "05", "HAZİRAN": "06", "TEMMUZ": "07", "AĞUSTOS": "08",
    "EYLÜL": "09", "EKİM": "10", "KASIM": "11", "ARALIK": "12",
    # OCR hatalı versiyonlar
    "AGUSTOS": "08", "HAZIRAN": "06", "EYLUL": "09", "SUBAT": "02",
    "NISAN": "04",
}

# İlan ayırıcılar
ANNOUNCEMENT_SEPARATORS = [
    r"T\.C\.\s+[\w\s/İÇÖÜĞŞ]+TİCARET SİCİLİ MÜDÜRLÜĞÜ",
    r"İlan Sıra No\s*:",
]

MIN_CONTENT_LENGTH = 100


def validate_file_content(text: str) -> bool:
    """Dosyanın geçerli TSG OCR içeriği olup olmadığını kontrol et."""
    if len(text) < MIN_CONTENT_LENGTH:
        return False
    gazette_indicators = ["TİCARET SİCİLİ", "SAYI", "SAYFA", "Ticaret Unvanı", "Tescil"]
    matches = sum(1 for indicator in gazette_indicators if indicator.lower() in text.lower())
    return matches >= 2


def file_hash(text: str) -> str:
    """Dosya içeriğinden hash üret (duplicate tespiti için)."""
    return hashlib.md5(text.encode("utf-8")).hexdigest()


def extract_gazette_metadata(text: str) -> Dict[str, Optional[str]]:
    """Gazete tarih ve sayısını çıkar."""
    for pattern in DATE_PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            day = match.group(1).zfill(2)
            month_name = match.group(2).upper()
            year = match.group(3)
            gazette_no = match.group(4)
            month = MONTH_MAP.get(month_name, "01")
            return {
                "date": f"{year}-{month}-{day}",
                "no": gazette_no,
            }
    return {"date": None, "no": None}


def split_announcements(text: str) -> List[str]:
    """Dosyadaki ilanları ayır."""
    combined_pattern = "|".join(f"({p})" for p in ANNOUNCEMENT_SEPARATORS)
    parts = re.split(combined_pattern, text, flags=re.IGNORECASE)

    announcements = []
    current = ""
    for part in parts:
        if part is None:
            continue
        is_separator = any(
            re.match(p, part.strip(), re.IGNORECASE)
            for p in ANNOUNCEMENT_SEPARATORS
        )
        if is_separator and current.strip():
            announcements.append(current.strip())
            current = part
        else:
            current += part

    if current.strip():
        announcements.append(current.strip())

    # İlk parçayı atla (genellikle gazete başlığı)
    if announcements and not any(
        kw in announcements[0].lower()
        for kw in ["ticaret unvanı", "mersis", "ilan sıra"]
    ):
        announcements = announcements[1:] if len(announcements) > 1 else announcements

    return announcements


def find_company_announcement(
    announcements: List[str], company_name: str
) -> Optional[str]:
    """İlanlar arasından hedef şirkete ait olanı bul."""
    # Normalize: büyük harf, gereksiz boşlukları sil
    normalized_target = company_name.upper().strip()
    # Kısa eşleşme (ilk 3 kelime)
    target_words = normalized_target.split()[:3]
    short_target = " ".join(target_words)

    for announcement in announcements:
        upper = announcement.upper()
        if normalized_target in upper or short_target in upper:
            return announcement

    return None
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run python -m pytest tests/extensions/test_tsg_splitter.py -v`
Expected: All 7 tests PASS

- [ ] **Step 5: Commit**

```bash
git add extensions/tsg/splitter.py tests/extensions/test_tsg_splitter.py
git commit -m "feat(tsg): add gazette splitter with metadata extraction"
```

---

## Task 4: LLM Extractor (Triage + Detail)

**Files:**
- Create: `extensions/tsg/extractor.py`
- Create: `extensions/tsg/prompts/triage.yaml`
- Create: `extensions/tsg/prompts/genel.yaml`
- Create: `tests/extensions/test_tsg_extractor.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/extensions/test_tsg_extractor.py
import pytest
import json
from unittest.mock import AsyncMock, patch
from extensions.tsg.extractor import triage_extract, detail_extract, load_prompt


def test_load_prompt_triage():
    prompt = load_prompt("triage")
    assert "islem_turu" in prompt
    assert "gazette_date" in prompt


def test_load_prompt_genel():
    prompt = load_prompt("genel")
    assert len(prompt) > 0


MOCK_TRIAGE_RESPONSE = json.dumps({
    "islem_turu": "yonetim",
    "gazette_date": "2024-06-21",
    "gazette_no": "11106",
    "ilan_kodu": "20229116",
    "sirket_unvani": "AYDIN HOLDİNG ANONİM ŞİRKETİ",
    "mersis_no": "0115148655300001",
})

MOCK_DETAIL_RESPONSE = json.dumps({
    "islem_turu": "yonetim",
    "fields": {},
    "persons": [
        {"name": "Turgut Aydın", "role": "YK Başkanı", "person_type": "yonetim", "imza_derecesi": 1}
    ],
    "events": [
        {"event_type": "yonetim", "summary": "Yönetim kurulu yeniden belirlendi"}
    ],
})


@pytest.mark.asyncio
@patch("extensions.tsg.extractor.call_llm", new_callable=AsyncMock)
async def test_triage_extract(mock_llm):
    mock_llm.return_value = MOCK_TRIAGE_RESPONSE
    result = await triage_extract("ilan metni burada")
    assert result["islem_turu"] == "yonetim"
    assert result["gazette_date"] == "2024-06-21"
    assert result["mersis_no"] == "0115148655300001"


@pytest.mark.asyncio
@patch("extensions.tsg.extractor.call_llm", new_callable=AsyncMock)
async def test_detail_extract(mock_llm):
    mock_llm.return_value = MOCK_DETAIL_RESPONSE
    result = await detail_extract("ilan metni burada", "yonetim")
    assert len(result["persons"]) == 1
    assert result["persons"][0]["name"] == "Turgut Aydın"
    assert len(result["events"]) == 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run python -m pytest tests/extensions/test_tsg_extractor.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Create prompt templates**

Create `extensions/tsg/prompts/triage.yaml`:

```yaml
name: triage
description: "TSG ilanından temel bilgileri hızlıca çıkarır"
prompt: |
  Bu bir Türkiye Ticaret Sicil Gazetesi ilanıdır. Aşağıdaki bilgileri JSON olarak çıkar:

  İLAN METNİ:
  {text}

  SADECE şu alanları içeren JSON döndür (başka metin ekleme):
  {{
    "islem_turu": "kurulus|sermaye|yonetim|adres|unvan|faaliyet|temsil|denetci|pay_devri|ana_sozlesme_tadili|ic_yonerge|sube_acilis|sube_kapanis|merkez_nakli|tasfiye|terkin|konkordato|bolunme|ek_tasfiye|ttk198|acentelik|diger",
    "gazette_date": "YYYY-MM-DD",
    "gazette_no": "sayı",
    "ilan_kodu": "parantez içindeki kod",
    "sirket_unvani": "tam ünvan",
    "mersis_no": "varsa"
  }}
```

Create `extensions/tsg/prompts/genel.yaml`:

```yaml
name: genel
description: "TSG ilanından detaylı yapılandırılmış veri çıkarır"
prompt: |
  Bu bir Türkiye Ticaret Sicil Gazetesi ilanıdır. İşlem türü: {islem_turu}

  İLAN METNİ:
  {text}

  Aşağıdaki JSON yapısında çıkar. Mevcut olmayan alanları boş bırak.

  {{
    "islem_turu": "{islem_turu}",
    "fields": {{
      "sermaye": {{"value": "tutar", "detail": "pay bilgisi"}},
      "adres": {{"value": "tam adres"}},
      "faaliyet": {{"value": "kısa özet"}},
      "temsil": {{"value": "temsil şekli açıklaması"}}
    }},
    "persons": [
      {{
        "name": "Ad Soyad",
        "person_type": "yonetim|ortak|denetci|tasfiye_memuru",
        "entity_type": "gercek_kisi|tuzel_kisi",
        "role": "görev",
        "tc_no": "varsa",
        "uyruk": "varsa",
        "temsilci_name": "tüzel kişi temsilcisi varsa",
        "pay_amount": "pay tutarı varsa",
        "pay_ratio": "yüzde varsa",
        "imza_derecesi": null,
        "imza_sekli": "munferit|musterek|null",
        "gorev_baslangic": "varsa",
        "gorev_bitis": "varsa"
      }}
    ],
    "articles": [
      {{
        "article_no": 1,
        "article_title": "madde başlığı",
        "text": "madde metni"
      }}
    ],
    "events": [
      {{
        "event_type": "işlem türü",
        "summary": "1-2 cümle Türkçe özet",
        "old_value": "eski durum varsa",
        "new_value": "yeni durum"
      }}
    ],
    "delil_belgesi": {{
      "noter_adi": "varsa",
      "noter_tarihi": "varsa",
      "yevmiye_no": "varsa",
      "karar_turu": "GK kararı|YK kararı|mahkeme kararı"
    }}
  }}

  KURALLAR:
  - OCR hatalarını düzelt (Sirket→Şirket, Ünvani→Ünvanı vb.)
  - Sadece ilandan çıkarılabilecek bilgileri yaz
  - JSON dışında metin ekleme
```

- [ ] **Step 4: Implement extractor**

Create `extensions/tsg/extractor.py`:

```python
"""LLM ile gazete ilanından yapılandırılmış veri çıkarma."""

import json
import os
from typing import Any, Dict, Optional

import yaml
from loguru import logger


def load_prompt(prompt_name: str) -> str:
    """Prompt şablonunu yükle."""
    prompt_dir = os.path.join(os.path.dirname(__file__), "prompts")
    filepath = os.path.join(prompt_dir, f"{prompt_name}.yaml")
    with open(filepath, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data["prompt"]


async def call_llm(prompt: str, model_id: Optional[str] = None) -> str:
    """LLM çağrısı — open-notebook'un mevcut altyapısını kullanır."""
    from open_notebook.ai.models import model_manager
    model = await model_manager.get_default_model("chat")
    if model is None:
        raise RuntimeError("No default chat model configured")
    response = await model.achat([{"role": "user", "content": prompt}])
    return response.text


def parse_json_response(text: str) -> Dict[str, Any]:
    """LLM yanıtından JSON çıkar (markdown code block varsa temizle)."""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        cleaned = "\n".join(lines)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        # JSON bloğunu bul
        start = cleaned.find("{")
        end = cleaned.rfind("}") + 1
        if start >= 0 and end > start:
            return json.loads(cleaned[start:end])
        raise ValueError(f"Could not parse JSON from LLM response: {cleaned[:200]}")


async def triage_extract(announcement_text: str) -> Dict[str, Any]:
    """Aşama 4a: Hızlı triage — işlem türü ve temel metadata çıkar."""
    template = load_prompt("triage")
    prompt = template.replace("{text}", announcement_text[:3000])
    response = await call_llm(prompt)
    return parse_json_response(response)


async def detail_extract(
    announcement_text: str, islem_turu: str
) -> Dict[str, Any]:
    """Aşama 4b: Detaylı extraction — işlem türüne göre."""
    # İşlem türüne özel prompt varsa onu kullan, yoksa genel
    prompt_name = islem_turu if os.path.exists(
        os.path.join(os.path.dirname(__file__), "prompts", f"{islem_turu}.yaml")
    ) else "genel"
    template = load_prompt(prompt_name)
    prompt = template.replace("{text}", announcement_text).replace("{islem_turu}", islem_turu)
    response = await call_llm(prompt)
    return parse_json_response(response)
```

- [ ] **Step 5: Run test to verify it passes**

Run: `uv run python -m pytest tests/extensions/test_tsg_extractor.py -v`
Expected: All 4 tests PASS

- [ ] **Step 6: Commit**

```bash
git add extensions/tsg/extractor.py extensions/tsg/prompts/ tests/extensions/test_tsg_extractor.py
git commit -m "feat(tsg): add LLM extractor with triage + detail prompts"
```

---

## Task 5: State Manager (DB Güncelleme)

**Files:**
- Create: `extensions/tsg/state_manager.py`
- Create: `tests/extensions/test_tsg_state_manager.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/extensions/test_tsg_state_manager.py
import pytest
from unittest.mock import AsyncMock, patch
from extensions.tsg.state_manager import (
    find_or_create_company,
    update_company_fields,
    update_company_persons,
    add_company_event,
)


@pytest.mark.asyncio
@patch("extensions.tsg.state_manager.repo_query", new_callable=AsyncMock)
@patch("extensions.tsg.state_manager.repo_create", new_callable=AsyncMock)
async def test_find_or_create_company_creates_new(mock_create, mock_query):
    mock_query.return_value = []
    mock_create.return_value = [{"id": "ext_company:abc", "name": "TEST A.Ş.", "status": "aktif", "gazette_count": 0}]
    company_id = await find_or_create_company("TEST A.Ş.", mersis_no="123")
    assert company_id == "ext_company:abc"
    mock_create.assert_called_once()


@pytest.mark.asyncio
@patch("extensions.tsg.state_manager.repo_query", new_callable=AsyncMock)
async def test_find_or_create_company_finds_existing(mock_query):
    mock_query.return_value = [{"id": "ext_company:existing", "name": "TEST A.Ş."}]
    company_id = await find_or_create_company("TEST A.Ş.", mersis_no="123")
    assert company_id == "ext_company:existing"


@pytest.mark.asyncio
@patch("extensions.tsg.state_manager.repo_query", new_callable=AsyncMock)
@patch("extensions.tsg.state_manager.repo_create", new_callable=AsyncMock)
@patch("extensions.tsg.state_manager.repo_update", new_callable=AsyncMock)
async def test_update_company_fields_new_field(mock_update, mock_create, mock_query):
    mock_query.return_value = []  # field yok
    mock_create.return_value = [{"id": "ext_company_field:new"}]
    await update_company_fields(
        company_id="ext_company:abc",
        fields={"sermaye": {"value": "50.000.000 TL"}},
        gazette_date="2024-06-21",
        source_id="source:xyz",
    )
    mock_create.assert_called_once()


@pytest.mark.asyncio
@patch("extensions.tsg.state_manager.repo_query", new_callable=AsyncMock)
@patch("extensions.tsg.state_manager.repo_update", new_callable=AsyncMock)
async def test_update_company_fields_newer_date(mock_update, mock_query):
    mock_query.return_value = [{"id": "ext_company_field:old", "gazette_date": "2023-01-01", "value": "10M TL"}]
    await update_company_fields(
        company_id="ext_company:abc",
        fields={"sermaye": {"value": "50M TL"}},
        gazette_date="2024-06-21",
        source_id="source:xyz",
    )
    mock_update.assert_called_once()


@pytest.mark.asyncio
@patch("extensions.tsg.state_manager.repo_query", new_callable=AsyncMock)
async def test_update_company_fields_older_date_skips(mock_query):
    mock_query.return_value = [{"id": "ext_company_field:new", "gazette_date": "2025-01-01", "value": "100M TL"}]
    # gazette_date 2024 < existing 2025 → skip
    await update_company_fields(
        company_id="ext_company:abc",
        fields={"sermaye": {"value": "50M TL"}},
        gazette_date="2024-06-21",
        source_id="source:xyz",
    )
    # repo_update çağrılmamalı


@pytest.mark.asyncio
@patch("extensions.tsg.state_manager.repo_create", new_callable=AsyncMock)
async def test_add_company_event(mock_create):
    mock_create.return_value = [{"id": "ext_company_event:new"}]
    await add_company_event(
        company_id="ext_company:abc",
        event_type="yonetim",
        summary="YK değişti",
        gazette_date="2024-06-21",
        source_id="source:xyz",
    )
    mock_create.assert_called_once()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run python -m pytest tests/extensions/test_tsg_state_manager.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement state manager**

Create `extensions/tsg/state_manager.py`:

```python
"""Şirket güncel durumunu güncelleyen modül."""

from typing import Any, Dict, List, Optional

from loguru import logger

from open_notebook.database.repository import (
    repo_create,
    repo_query,
    repo_update,
)


async def find_or_create_company(
    name: str,
    mersis_no: Optional[str] = None,
    **kwargs,
) -> str:
    """Şirketi bul veya oluştur. ID döndürür."""
    # Önce mersis_no ile ara
    if mersis_no:
        results = await repo_query(
            "SELECT id, name FROM ext_company WHERE mersis_no = $mersis_no",
            {"mersis_no": mersis_no},
        )
        if results:
            return results[0]["id"]

    # İsimle ara
    results = await repo_query(
        "SELECT id, name FROM ext_company WHERE name = $name",
        {"name": name},
    )
    if results:
        return results[0]["id"]

    # Yeni oluştur
    data = {"name": name, "status": "aktif", "gazette_count": 0}
    if mersis_no:
        data["mersis_no"] = mersis_no
    data.update(kwargs)
    result = await repo_create("ext_company", data)
    created = result[0] if isinstance(result, list) else result
    logger.info(f"New company created: {name} → {created['id']}")
    return created["id"]


async def update_company_meta(
    company_id: str,
    gazette_date: Optional[str] = None,
    gazette_no: Optional[str] = None,
    **kwargs,
) -> None:
    """Şirket meta bilgilerini güncelle (gazette_count, last_gazette_date vb.)."""
    data = {}
    if gazette_date:
        data["last_gazette_date"] = gazette_date
    if gazette_no:
        data["last_gazette_no"] = gazette_no
    data.update(kwargs)

    # gazette_count artır
    await repo_query(
        "UPDATE $company_id SET gazette_count += 1",
        {"company_id": company_id},
    )
    if data:
        await repo_update("ext_company", company_id, data)


async def update_company_fields(
    company_id: str,
    fields: Dict[str, Dict[str, Any]],
    gazette_date: str,
    source_id: Optional[str] = None,
    gazette_no: Optional[str] = None,
    ilan_kodu: Optional[str] = None,
) -> None:
    """Şirket alanlarını güncelle — sadece daha yeni tarihli kayıtlar geçerli."""
    for field_type, field_data in fields.items():
        value = field_data.get("value")
        if not value:
            continue

        # Mevcut alanı kontrol et
        existing = await repo_query(
            "SELECT id, gazette_date, value FROM ext_company_field WHERE company_id = $cid AND field_type = $ft",
            {"cid": company_id, "ft": field_type},
        )

        if existing:
            existing_date = existing[0].get("gazette_date", "")
            if gazette_date and existing_date and gazette_date <= existing_date:
                logger.debug(f"Skipping field {field_type}: existing date {existing_date} >= {gazette_date}")
                continue
            await repo_update(
                "ext_company_field",
                existing[0]["id"],
                {
                    "value": value,
                    "gazette_date": gazette_date,
                    "gazette_no": gazette_no,
                    "ilan_kodu": ilan_kodu,
                    "source_id": source_id,
                },
            )
        else:
            await repo_create(
                "ext_company_field",
                {
                    "company_id": company_id,
                    "field_type": field_type,
                    "value": value,
                    "gazette_date": gazette_date,
                    "gazette_no": gazette_no,
                    "ilan_kodu": ilan_kodu,
                    "source_id": source_id,
                },
            )


async def update_company_persons(
    company_id: str,
    persons: List[Dict[str, Any]],
    gazette_date: str,
    source_id: Optional[str] = None,
) -> None:
    """Kişi listesini güncelle."""
    for person_data in persons:
        name = person_data.get("name")
        person_type = person_data.get("person_type", "yonetim")
        if not name:
            continue

        await repo_create(
            "ext_company_person",
            {
                "company_id": company_id,
                "person_type": person_type,
                "entity_type": person_data.get("entity_type", "gercek_kisi"),
                "name": name,
                "role": person_data.get("role"),
                "tc_no": person_data.get("tc_no"),
                "uyruk": person_data.get("uyruk"),
                "temsilci_name": person_data.get("temsilci_name"),
                "pay_amount": person_data.get("pay_amount"),
                "pay_ratio": person_data.get("pay_ratio"),
                "imza_derecesi": person_data.get("imza_derecesi"),
                "imza_sekli": person_data.get("imza_sekli"),
                "imza_grubu": person_data.get("imza_grubu"),
                "gorev_baslangic": person_data.get("gorev_baslangic"),
                "gorev_bitis": person_data.get("gorev_bitis"),
                "is_active": True,
                "gazette_date": gazette_date,
                "source_id": source_id,
            },
        )


async def add_company_event(
    company_id: str,
    event_type: str,
    summary: str,
    gazette_date: Optional[str] = None,
    gazette_no: Optional[str] = None,
    ilan_kodu: Optional[str] = None,
    source_id: Optional[str] = None,
    old_value: Optional[str] = None,
    new_value: Optional[str] = None,
    delil_belgesi: Optional[Dict] = None,
    raw_extraction: Optional[Dict] = None,
) -> str:
    """Kronoloji kaydı ekle."""
    result = await repo_create(
        "ext_company_event",
        {
            "company_id": company_id,
            "source_id": source_id,
            "gazette_date": gazette_date,
            "gazette_no": gazette_no,
            "ilan_kodu": ilan_kodu,
            "event_type": event_type,
            "summary": summary,
            "old_value": old_value,
            "new_value": new_value,
            "delil_belgesi": delil_belgesi,
            "raw_extraction": raw_extraction,
        },
    )
    created = result[0] if isinstance(result, list) else result
    return created["id"]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run python -m pytest tests/extensions/test_tsg_state_manager.py -v`
Expected: All 6 tests PASS

- [ ] **Step 5: Commit**

```bash
git add extensions/tsg/state_manager.py tests/extensions/test_tsg_state_manager.py
git commit -m "feat(tsg): add state manager for company data updates"
```

---

## Task 6: Full Pipeline

**Files:**
- Create: `extensions/tsg/pipeline.py`
- Create: `tests/extensions/test_tsg_pipeline.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/extensions/test_tsg_pipeline.py
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from extensions.tsg.pipeline import process_gazette_file


SAMPLE_TEXT = """=== STRUCTURED CONTENT ===
## text_blocks
- 21 HAZİRAN 2024 SAYI : 11106
- TÜRKİYE TİCARET SİCİLİ GAZETESİ
- T.C. İSTANBUL TİCARET SİCİLİ MÜDÜRLÜĞÜ'NDEN
- İlan Sıra No: 12345
- Ticaret Unvanı: TEST HOLDİNG ANONİM ŞİRKETİ
- Sermaye artırımı tescil edilmiştir.
- (20240001)
"""


@pytest.mark.asyncio
@patch("extensions.tsg.pipeline.detail_extract", new_callable=AsyncMock)
@patch("extensions.tsg.pipeline.triage_extract", new_callable=AsyncMock)
@patch("extensions.tsg.pipeline.add_company_event", new_callable=AsyncMock)
@patch("extensions.tsg.pipeline.update_company_fields", new_callable=AsyncMock)
@patch("extensions.tsg.pipeline.update_company_persons", new_callable=AsyncMock)
@patch("extensions.tsg.pipeline.update_company_meta", new_callable=AsyncMock)
@patch("extensions.tsg.pipeline.find_or_create_company", new_callable=AsyncMock)
async def test_process_gazette_file(
    mock_find, mock_meta, mock_persons, mock_fields, mock_event,
    mock_triage, mock_detail
):
    mock_find.return_value = "ext_company:abc"
    mock_triage.return_value = {
        "islem_turu": "sermaye",
        "gazette_date": "2024-06-21",
        "gazette_no": "11106",
        "ilan_kodu": "20240001",
        "sirket_unvani": "TEST HOLDİNG ANONİM ŞİRKETİ",
        "mersis_no": "123",
    }
    mock_detail.return_value = {
        "fields": {"sermaye": {"value": "50M TL"}},
        "persons": [],
        "events": [{"event_type": "sermaye", "summary": "Sermaye artırıldı"}],
    }
    mock_event.return_value = "ext_company_event:new"

    result = await process_gazette_file(SAMPLE_TEXT, "TEST HOLDİNG")
    assert result["company_id"] == "ext_company:abc"
    assert result["success"] is True
    mock_find.assert_called_once()
    mock_fields.assert_called_once()
    mock_event.assert_called_once()


@pytest.mark.asyncio
async def test_process_gazette_file_invalid_content():
    result = await process_gazette_file("too short", "TEST")
    assert result["success"] is False
    assert "invalid" in result["error"].lower() or "geçersiz" in result["error"].lower()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run python -m pytest tests/extensions/test_tsg_pipeline.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement pipeline**

Create `extensions/tsg/pipeline.py`:

```python
"""Tam extraction pipeline: doğrulama → bölme → eşleştirme → extraction → kaydetme."""

from typing import Any, Dict, Optional

from loguru import logger

from extensions.tsg.splitter import (
    extract_gazette_metadata,
    find_company_announcement,
    split_announcements,
    validate_file_content,
    file_hash,
)
from extensions.tsg.extractor import triage_extract, detail_extract
from extensions.tsg.state_manager import (
    add_company_event,
    find_or_create_company,
    update_company_fields,
    update_company_meta,
    update_company_persons,
)


# İşlenmiş dosya hash'leri (duplicate tespiti)
_processed_hashes: set = set()


async def process_gazette_file(
    text: str,
    company_name: str,
    source_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Tek gazete dosyasını işle.

    Returns:
        {"success": True, "company_id": "...", "event_type": "...", ...}
        veya {"success": False, "error": "..."}
    """
    # Aşama 1: Doğrulama
    if not validate_file_content(text):
        return {"success": False, "error": "Geçersiz dosya içeriği"}

    # Duplicate kontrolü
    content_hash = file_hash(text)
    if content_hash in _processed_hashes:
        return {"success": False, "error": "Duplicate dosya (zaten işlendi)"}
    _processed_hashes.add(content_hash)

    try:
        # Aşama 2: Bölme
        gazette_meta = extract_gazette_metadata(text)
        announcements = split_announcements(text)

        if not announcements:
            return {"success": False, "error": "İlan bulunamadı"}

        # Aşama 3: Eşleştirme
        announcement = find_company_announcement(announcements, company_name)
        if not announcement:
            # Tüm metni dene (bazen splitter hata yapabilir)
            announcement = text if company_name.upper().split()[0] in text.upper() else None
        if not announcement:
            return {"success": False, "error": f"Şirket ilanı bulunamadı: {company_name}"}

        # Aşama 4a: Triage
        triage = await triage_extract(announcement)
        islem_turu = triage.get("islem_turu", "diger")
        gazette_date = triage.get("gazette_date") or gazette_meta.get("date")
        gazette_no = triage.get("gazette_no") or gazette_meta.get("no")
        ilan_kodu = triage.get("ilan_kodu")
        mersis_no = triage.get("mersis_no")

        # Aşama 4b: Detay
        detail = await detail_extract(announcement, islem_turu)

        # Aşama 5: Kaydetme
        company_id = await find_or_create_company(
            name=triage.get("sirket_unvani", company_name),
            mersis_no=mersis_no,
        )

        # Meta güncelle
        await update_company_meta(
            company_id=company_id,
            gazette_date=gazette_date,
            gazette_no=gazette_no,
        )

        # Field'ları güncelle
        fields = detail.get("fields", {})
        if fields:
            await update_company_fields(
                company_id=company_id,
                fields=fields,
                gazette_date=gazette_date,
                source_id=source_id,
                gazette_no=gazette_no,
                ilan_kodu=ilan_kodu,
            )

        # Person'ları güncelle
        persons = detail.get("persons", [])
        if persons:
            await update_company_persons(
                company_id=company_id,
                persons=persons,
                gazette_date=gazette_date,
                source_id=source_id,
            )

        # Event ekle
        events = detail.get("events", [])
        for event in events:
            await add_company_event(
                company_id=company_id,
                event_type=event.get("event_type", islem_turu),
                summary=event.get("summary", ""),
                gazette_date=gazette_date,
                gazette_no=gazette_no,
                ilan_kodu=ilan_kodu,
                source_id=source_id,
                old_value=event.get("old_value"),
                new_value=event.get("new_value"),
                delil_belgesi=detail.get("delil_belgesi"),
                raw_extraction=detail,
            )

        logger.info(f"✅ Processed: {company_name} — {islem_turu} ({gazette_date})")

        return {
            "success": True,
            "company_id": company_id,
            "event_type": islem_turu,
            "gazette_date": gazette_date,
            "gazette_no": gazette_no,
        }

    except Exception as e:
        logger.error(f"Pipeline error for {company_name}: {e}")
        return {"success": False, "error": str(e)}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run python -m pytest tests/extensions/test_tsg_pipeline.py -v`
Expected: All 2 tests PASS

- [ ] **Step 5: Commit**

```bash
git add extensions/tsg/pipeline.py tests/extensions/test_tsg_pipeline.py
git commit -m "feat(tsg): add full extraction pipeline (validate→split→extract→save)"
```

---

## Task 7: Bulk Loader Script

**Files:**
- Create: `extensions/tsg/bulk_loader.py`

- [ ] **Step 1: Implement bulk loader**

Create `extensions/tsg/bulk_loader.py`:

```python
"""Klasörden toplu gazete yükleme scripti."""

import asyncio
import os
import sys
from pathlib import Path
from typing import Dict, List

from loguru import logger

from extensions.tsg.pipeline import process_gazette_file
from extensions.tsg.migration import run_tsg_migration


async def load_company_folder(
    folder_path: str,
    company_name: str,
) -> Dict[str, int]:
    """Tek şirket klasöründeki tüm dosyaları işle."""
    stats = {"total": 0, "success": 0, "skipped": 0, "error": 0}

    txt_files = sorted(Path(folder_path).glob("*.txt"))
    stats["total"] = len(txt_files)

    for txt_file in txt_files:
        text = txt_file.read_text(encoding="utf-8")
        result = await process_gazette_file(text, company_name)

        if result["success"]:
            stats["success"] += 1
        elif "duplicate" in result.get("error", "").lower():
            stats["skipped"] += 1
        else:
            stats["error"] += 1
            logger.warning(f"  ⚠ {txt_file.name}: {result.get('error', 'unknown')}")

    return stats


async def load_all_companies(base_dir: str) -> None:
    """Tüm şirket klasörlerini işle."""
    logger.info(f"Starting bulk load from: {base_dir}")

    # Migration çalıştır
    await run_tsg_migration()

    folders = sorted([
        d for d in Path(base_dir).iterdir()
        if d.is_dir() and not d.name.startswith(".")
    ])

    total_stats = {"companies": 0, "files": 0, "success": 0, "skipped": 0, "error": 0}

    for folder in folders:
        company_name = folder.name
        logger.info(f"📁 {company_name}")

        stats = await load_company_folder(str(folder), company_name)
        total_stats["companies"] += 1
        total_stats["files"] += stats["total"]
        total_stats["success"] += stats["success"]
        total_stats["skipped"] += stats["skipped"]
        total_stats["error"] += stats["error"]

        logger.info(
            f"   → {stats['success']}/{stats['total']} başarılı"
            f" ({stats['skipped']} atlandı, {stats['error']} hata)"
        )

    logger.success(
        f"\n{'='*50}\n"
        f"TOPLAM: {total_stats['companies']} şirket, {total_stats['files']} dosya\n"
        f"  ✅ Başarılı: {total_stats['success']}\n"
        f"  ⏭ Atlandı: {total_stats['skipped']}\n"
        f"  ❌ Hata: {total_stats['error']}\n"
        f"{'='*50}"
    )


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m extensions.tsg.bulk_loader <base_dir>")
        sys.exit(1)

    base_dir = sys.argv[1]
    if not os.path.isdir(base_dir):
        print(f"Directory not found: {base_dir}")
        sys.exit(1)

    asyncio.run(load_all_companies(base_dir))
```

- [ ] **Step 2: Commit**

```bash
git add extensions/tsg/bulk_loader.py
git commit -m "feat(tsg): add bulk loader for company gazette folders"
```

---

## Task 8: Report API Router

**Files:**
- Create: `extensions/tsg/report_router.py`
- Create: `tests/extensions/test_tsg_report_router.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/extensions/test_tsg_report_router.py
import pytest
from unittest.mock import AsyncMock, patch
from fastapi import FastAPI
from fastapi.testclient import TestClient

from extensions.tsg.report_router import create_tsg_report_router


@pytest.fixture
def app():
    app = FastAPI()
    router = create_tsg_report_router()
    app.include_router(router, prefix="/api/ext/tsg")
    return app


@pytest.fixture
def client(app):
    return TestClient(app)


@patch("extensions.tsg.report_router.repo_query", new_callable=AsyncMock)
def test_list_companies(mock_query, client):
    mock_query.return_value = [
        {"id": "ext_company:1", "name": "TEST A.Ş.", "status": "aktif", "gazette_count": 5}
    ]
    resp = client.get("/api/ext/tsg/companies")
    assert resp.status_code == 200
    assert len(resp.json()) == 1
    assert resp.json()[0]["name"] == "TEST A.Ş."


@patch("extensions.tsg.report_router.repo_query", new_callable=AsyncMock)
def test_get_company_card(mock_query, client):
    mock_query.side_effect = [
        [{"id": "ext_company:1", "name": "TEST A.Ş.", "mersis_no": "123", "status": "aktif", "gazette_count": 5, "last_gazette_date": "2024-06-21"}],
        [{"field_type": "sermaye", "value": "50M TL", "gazette_date": "2024-06-21"}],
    ]
    resp = client.get("/api/ext/tsg/companies/ext_company:1/card")
    assert resp.status_code == 200
    data = resp.json()
    assert data["company"]["name"] == "TEST A.Ş."
    assert "sermaye" in [f["field_type"] for f in data["fields"]]


@patch("extensions.tsg.report_router.repo_query", new_callable=AsyncMock)
def test_get_company_timeline(mock_query, client):
    mock_query.return_value = [
        {"event_type": "yonetim", "summary": "YK değişti", "gazette_date": "2024-06-21"}
    ]
    resp = client.get("/api/ext/tsg/companies/ext_company:1/timeline")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


@patch("extensions.tsg.report_router.repo_query", new_callable=AsyncMock)
def test_get_company_persons(mock_query, client):
    mock_query.return_value = [
        {"name": "Turgut Aydın", "person_type": "yonetim", "role": "YK Başkanı", "is_active": True}
    ]
    resp = client.get("/api/ext/tsg/companies/ext_company:1/persons")
    assert resp.status_code == 200
    assert resp.json()[0]["name"] == "Turgut Aydın"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run python -m pytest tests/extensions/test_tsg_report_router.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement report router**

Create `extensions/tsg/report_router.py`:

```python
"""TSG Intelligence rapor API'leri."""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from loguru import logger

from open_notebook.database.repository import repo_query


def create_tsg_report_router() -> APIRouter:
    router = APIRouter()

    @router.get("/companies")
    async def list_companies(
        status: Optional[str] = Query(None),
    ) -> List[Dict[str, Any]]:
        """Tüm şirketleri listele."""
        if status:
            results = await repo_query(
                "SELECT * FROM ext_company WHERE status = $status ORDER BY name",
                {"status": status},
            )
        else:
            results = await repo_query(
                "SELECT * FROM ext_company ORDER BY name"
            )
        return results

    @router.get("/companies/{company_id}/card")
    async def get_company_card(company_id: str) -> Dict[str, Any]:
        """Şirket bilgi kartı — temel bilgiler + güncel alanlar."""
        companies = await repo_query(
            "SELECT * FROM $cid",
            {"cid": company_id},
        )
        if not companies:
            raise HTTPException(status_code=404, detail="Şirket bulunamadı")

        fields = await repo_query(
            "SELECT * FROM ext_company_field WHERE company_id = $cid",
            {"cid": company_id},
        )

        return {
            "company": companies[0],
            "fields": fields,
        }

    @router.get("/companies/{company_id}/persons")
    async def get_company_persons(
        company_id: str,
        person_type: Optional[str] = Query(None),
        active_only: bool = Query(True),
    ) -> List[Dict[str, Any]]:
        """Şirket kişileri (yönetim, ortaklar, denetçiler)."""
        query = "SELECT * FROM ext_company_person WHERE company_id = $cid"
        params: Dict[str, Any] = {"cid": company_id}

        if person_type:
            query += " AND person_type = $pt"
            params["pt"] = person_type
        if active_only:
            query += " AND is_active = true"

        query += " ORDER BY imza_derecesi ASC, name ASC"
        return await repo_query(query, params)

    @router.get("/companies/{company_id}/timeline")
    async def get_company_timeline(
        company_id: str,
        event_type: Optional[str] = Query(None),
    ) -> List[Dict[str, Any]]:
        """Şirket kronolojisi."""
        query = "SELECT * FROM ext_company_event WHERE company_id = $cid"
        params: Dict[str, Any] = {"cid": company_id}

        if event_type:
            query += " AND event_type = $et"
            params["et"] = event_type

        query += " ORDER BY gazette_date DESC"
        return await repo_query(query, params)

    @router.get("/companies/{company_id}/articles")
    async def get_company_articles(company_id: str) -> List[Dict[str, Any]]:
        """Güncel esas sözleşme maddeleri."""
        return await repo_query(
            "SELECT * FROM ext_company_article WHERE company_id = $cid ORDER BY article_no",
            {"cid": company_id},
        )

    @router.get("/companies/{company_id}/authority")
    async def get_authority_matrix(
        company_id: str,
        scope: Optional[str] = Query(None),
    ) -> List[Dict[str, Any]]:
        """İmza yetki matrisi."""
        query = "SELECT * FROM ext_authority_matrix WHERE company_id = $cid"
        params: Dict[str, Any] = {"cid": company_id}

        if scope:
            query += " AND scope = $scope"
            params["scope"] = scope

        query += " ORDER BY min_degree ASC, rule_no ASC"
        return await repo_query(query, params)

    @router.get("/reports/sermaye")
    async def report_all_sermaye() -> List[Dict[str, Any]]:
        """Tüm şirketlerin güncel sermaye tablosu."""
        return await repo_query(
            """
            SELECT
                c.name as sirket,
                c.short_name as kisa_ad,
                f.value as sermaye,
                f.gazette_date as tarih
            FROM ext_company_field f
            JOIN ext_company c ON f.company_id = c.id
            WHERE f.field_type = 'sermaye'
            ORDER BY c.name
            """
        )

    return router
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run python -m pytest tests/extensions/test_tsg_report_router.py -v`
Expected: All 4 tests PASS

- [ ] **Step 5: Commit**

```bash
git add extensions/tsg/report_router.py tests/extensions/test_tsg_report_router.py
git commit -m "feat(tsg): add report API router (companies, card, timeline, persons, authority)"
```

---

## Task 9: Chat Router (Hibrit Sorgulama)

**Files:**
- Create: `extensions/tsg/chat_router.py`
- Create: `extensions/tsg/prompts/chat_system.yaml`
- Create: `tests/extensions/test_tsg_chat_router.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/extensions/test_tsg_chat_router.py
import pytest
from unittest.mock import AsyncMock, patch
from fastapi import FastAPI
from fastapi.testclient import TestClient

from extensions.tsg.chat_router import create_tsg_chat_router


@pytest.fixture
def app():
    app = FastAPI()
    router = create_tsg_chat_router()
    app.include_router(router, prefix="/api/ext/tsg")
    return app


@pytest.fixture
def client(app):
    return TestClient(app)


@patch("extensions.tsg.chat_router.classify_question", new_callable=AsyncMock)
@patch("extensions.tsg.chat_router.answer_factual", new_callable=AsyncMock)
def test_chat_factual_question(mock_answer, mock_classify, client):
    mock_classify.return_value = {"type": "factual", "company_id": "ext_company:1", "field": "sermaye"}
    mock_answer.return_value = {"answer": "50.000.000 TL", "source": "21.06.2024 TTSG", "type": "db"}
    resp = client.post(
        "/api/ext/tsg/chat",
        json={"question": "Aydın Holding sermayesi ne?", "company_id": "ext_company:1"},
    )
    assert resp.status_code == 200
    assert "50.000.000" in resp.json()["answer"]


@patch("extensions.tsg.chat_router.classify_question", new_callable=AsyncMock)
@patch("extensions.tsg.chat_router.answer_timeline", new_callable=AsyncMock)
def test_chat_timeline_question(mock_answer, mock_classify, client):
    mock_classify.return_value = {"type": "timeline", "company_id": "ext_company:1", "event_type": "sermaye"}
    mock_answer.return_value = {"answer": "2023: 10M → 2024: 50M", "source": "event tablosu", "type": "db"}
    resp = client.post(
        "/api/ext/tsg/chat",
        json={"question": "Sermaye ne zaman değişti?", "company_id": "ext_company:1"},
    )
    assert resp.status_code == 200
    assert resp.json()["answer_type"] == "db"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run python -m pytest tests/extensions/test_tsg_chat_router.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Create chat system prompt**

Create `extensions/tsg/prompts/chat_system.yaml`:

```yaml
name: chat_system
description: "TSG Intelligence chat sistem prompt'u"
prompt: |
  Sen bir Ticaret Sicil Gazetesi uzmanısın. Kullanıcıların şirketler hakkındaki sorularını yanıtlıyorsun.

  KURALLAR:
  1. Her zaman EN GÜNCEL bilgiyi ver (en son gazete tarihli kayıt)
  2. Cevabın kaynağını belirt (gazete tarihi ve sayısı)
  3. Emin olmadığın bilgiyi tahmin etme, "bu bilgi mevcut kayıtlarda yok" de
  4. Birden fazla gazete kaydı varsa kronolojik sırayı belirt
  5. OCR hatası olabileceğini göz önünde bulundur
  6. Türkçe cevap ver (kullanıcı İngilizce sorarsa İngilizce cevapla)

classify_prompt: |
  Kullanıcının sorusunu sınıflandır. JSON döndür:

  Soru: {question}
  Şirket ID: {company_id}

  {{
    "type": "factual|timeline|analytic|comparison",
    "company_id": "{company_id}",
    "field": "sermaye|adres|faaliyet|temsil|denetci|null",
    "event_type": "kurulus|sermaye|yonetim|adres|null",
    "detail": "kısa açıklama"
  }}
```

- [ ] **Step 4: Implement chat router**

Create `extensions/tsg/chat_router.py`:

```python
"""TSG Intelligence hibrit chat router."""

import json
from typing import Any, Dict, Optional

from fastapi import APIRouter
from loguru import logger
from pydantic import BaseModel

from open_notebook.database.repository import repo_query


class ChatRequest(BaseModel):
    question: str
    company_id: Optional[str] = None
    language: str = "tr"


class ChatResponse(BaseModel):
    answer: str
    answer_type: str  # "db" | "rag" | "llm"
    source: Optional[str] = None
    company_id: Optional[str] = None


async def classify_question(question: str, company_id: Optional[str]) -> Dict[str, Any]:
    """Soruyu sınıflandır: factual, timeline, analytic, comparison."""
    from extensions.tsg.extractor import call_llm, load_prompt, parse_json_response

    data = load_prompt("chat_system")
    # chat_system.yaml'dan classify_prompt'u al
    import yaml, os
    prompt_path = os.path.join(os.path.dirname(__file__), "prompts", "chat_system.yaml")
    with open(prompt_path, "r", encoding="utf-8") as f:
        prompts = yaml.safe_load(f)

    classify_prompt = prompts["classify_prompt"].replace(
        "{question}", question
    ).replace("{company_id}", company_id or "bilinmiyor")

    response = await call_llm(classify_prompt)
    return parse_json_response(response)


async def answer_factual(company_id: str, field: Optional[str]) -> Dict[str, Any]:
    """Faktüel soru — DB'den direkt cevap."""
    if field:
        results = await repo_query(
            "SELECT * FROM ext_company_field WHERE company_id = $cid AND field_type = $ft",
            {"cid": company_id, "ft": field},
        )
        if results:
            r = results[0]
            return {
                "answer": f"{r['value']}",
                "source": f"{r.get('gazette_date', '?')} tarihli TTSG",
                "type": "db",
            }

    # Genel şirket bilgisi
    companies = await repo_query("SELECT * FROM $cid", {"cid": company_id})
    if companies:
        c = companies[0]
        fields = await repo_query(
            "SELECT * FROM ext_company_field WHERE company_id = $cid",
            {"cid": company_id},
        )
        info_parts = [f"**{c.get('name', '?')}**"]
        for f in fields:
            info_parts.append(f"- {f['field_type']}: {f['value']}")
        return {
            "answer": "\n".join(info_parts),
            "source": f"Son güncelleme: {c.get('last_gazette_date', '?')}",
            "type": "db",
        }

    return {"answer": "Şirket bulunamadı.", "source": None, "type": "db"}


async def answer_timeline(
    company_id: str, event_type: Optional[str]
) -> Dict[str, Any]:
    """Kronoloji sorusu — event tablosundan."""
    query = "SELECT * FROM ext_company_event WHERE company_id = $cid"
    params: Dict[str, Any] = {"cid": company_id}
    if event_type:
        query += " AND event_type = $et"
        params["et"] = event_type
    query += " ORDER BY gazette_date ASC"

    events = await repo_query(query, params)
    if not events:
        return {"answer": "Bu konuda kayıt bulunamadı.", "source": None, "type": "db"}

    lines = []
    for e in events:
        date = e.get("gazette_date", "?")
        summary = e.get("summary", "")
        lines.append(f"**{date}** — {summary}")

    return {
        "answer": "\n".join(lines),
        "source": f"{len(events)} gazete kaydından",
        "type": "db",
    }


async def answer_analytic(
    company_id: str, question: str
) -> Dict[str, Any]:
    """Analitik soru — RAG + LLM."""
    from extensions.tsg.extractor import call_llm, load_prompt
    import yaml, os

    prompt_path = os.path.join(os.path.dirname(__file__), "prompts", "chat_system.yaml")
    with open(prompt_path, "r", encoding="utf-8") as f:
        prompts = yaml.safe_load(f)

    # Şirket bağlamını topla
    company = await repo_query("SELECT * FROM $cid", {"cid": company_id})
    fields = await repo_query(
        "SELECT * FROM ext_company_field WHERE company_id = $cid", {"cid": company_id}
    )
    events = await repo_query(
        "SELECT * FROM ext_company_event WHERE company_id = $cid ORDER BY gazette_date DESC LIMIT 10",
        {"cid": company_id},
    )

    context_parts = []
    if company:
        context_parts.append(f"Şirket: {company[0].get('name', '?')}")
    for f in fields:
        context_parts.append(f"{f['field_type']}: {f['value']}")
    for e in events[:5]:
        context_parts.append(f"[{e.get('gazette_date')}] {e.get('summary', '')}")

    context = "\n".join(context_parts)
    system = prompts["prompt"]

    full_prompt = f"{system}\n\nŞİRKET BİLGİLERİ:\n{context}\n\nSORU: {question}"
    answer = await call_llm(full_prompt)

    return {"answer": answer, "source": "Yapılandırılmış veri + LLM analizi", "type": "llm"}


def create_tsg_chat_router() -> APIRouter:
    router = APIRouter()

    @router.post("/chat", response_model=ChatResponse)
    async def chat(req: ChatRequest):
        classification = await classify_question(req.question, req.company_id)
        q_type = classification.get("type", "analytic")
        company_id = classification.get("company_id") or req.company_id

        if not company_id:
            return ChatResponse(
                answer="Lütfen bir şirket belirtin.",
                answer_type="error",
            )

        if q_type == "factual":
            result = await answer_factual(company_id, classification.get("field"))
        elif q_type == "timeline":
            result = await answer_timeline(company_id, classification.get("event_type"))
        elif q_type == "comparison":
            result = await answer_analytic(company_id, req.question)
        else:
            result = await answer_analytic(company_id, req.question)

        return ChatResponse(
            answer=result["answer"],
            answer_type=result["type"],
            source=result.get("source"),
            company_id=company_id,
        )

    return router
```

- [ ] **Step 5: Run test to verify it passes**

Run: `uv run python -m pytest tests/extensions/test_tsg_chat_router.py -v`
Expected: All 2 tests PASS

- [ ] **Step 6: Commit**

```bash
git add extensions/tsg/chat_router.py extensions/tsg/prompts/chat_system.yaml tests/extensions/test_tsg_chat_router.py
git commit -m "feat(tsg): add hybrid chat router (factual/timeline/analytic)"
```

---

## Task 10: Wire TSG Extension into Loader + E2E Test

**Files:**
- Modify: `extensions/loader.py`

- [ ] **Step 1: Update extension loader**

Add TSG extension to `extensions/loader.py`, after the outputs extension block:

```python
    # TSG Intelligence extension
    if "tsg" in enabled:
        from extensions.tsg.migration import run_tsg_migration
        from extensions.tsg.report_router import create_tsg_report_router
        from extensions.tsg.chat_router import create_tsg_chat_router

        # Run migration
        import asyncio
        try:
            asyncio.get_event_loop().run_until_complete(run_tsg_migration())
        except RuntimeError:
            # Already in async context — migration will run on first request
            logger.info("TSG migration deferred to first request")

        # Register routers
        tsg_report_router = create_tsg_report_router()
        app.include_router(tsg_report_router, prefix="/api/ext/tsg", tags=["ext-tsg"])

        tsg_chat_router = create_tsg_chat_router()
        app.include_router(tsg_chat_router, prefix="/api/ext/tsg", tags=["ext-tsg-chat"])

        logger.success("TSG Intelligence extension loaded")
```

Also update `docker-compose.override.yml` to add `tsg` to EXTENSIONS_ENABLED:

```yaml
- EXTENSIONS_ENABLED=auth,outputs,i18n,tsg
```

- [ ] **Step 2: Run all tests**

Run: `uv run python -m pytest tests/extensions/ -v`
Expected: All tests PASS

- [ ] **Step 3: Commit**

```bash
git add extensions/loader.py docker-compose.override.yml
git commit -m "feat(tsg): wire TSG extension into loader + enable in docker-compose"
```

- [ ] **Step 4: Rebuild and test with Docker**

```bash
docker compose -f docker-compose.yml -f docker-compose.override.yml down
docker compose -f docker-compose.yml -f docker-compose.override.yml build
docker compose -f docker-compose.yml -f docker-compose.override.yml up -d
```

Verify:
```bash
# Health check
curl -s http://localhost:5055/health

# TSG extension loaded
docker logs notebooklm-dev-open_notebook-1 | grep "TSG"

# Companies endpoint (empty at first)
curl -s http://localhost:5055/api/ext/tsg/companies
```

- [ ] **Step 5: Run bulk loader**

```bash
docker exec -it notebooklm-dev-open_notebook-1 \
  uv run python -m extensions.tsg.bulk_loader \
  "/Users/salihgencer/Downloads/Şirket Bilgileri OCR ve PDF/ocr_results 2/"
```

Or from host (if volume mounted):
```bash
uv run python -m extensions.tsg.bulk_loader \
  "/Users/salihgencer/Downloads/Şirket Bilgileri OCR ve PDF/ocr_results 2/"
```

- [ ] **Step 6: Verify data**

```bash
# Şirket listesi
curl -s http://localhost:5055/api/ext/tsg/companies | python3 -m json.tool | head -20

# Aydın Holding kartı
curl -s "http://localhost:5055/api/ext/tsg/companies/ext_company:XXX/card" | python3 -m json.tool

# Kronoloji
curl -s "http://localhost:5055/api/ext/tsg/companies/ext_company:XXX/timeline" | python3 -m json.tool

# Chat
curl -s -X POST http://localhost:5055/api/ext/tsg/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "Aydın Holding sermayesi ne?", "company_id": "ext_company:XXX"}'
```

- [ ] **Step 7: Final commit**

```bash
git add -A
git commit -m "chore: TSG Intelligence MVP complete — bulk load + chat + reports"
git push origin develop
```
