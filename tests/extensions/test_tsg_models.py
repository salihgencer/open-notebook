"""TSG migration SQL ve Pydantic model testleri."""

import pytest

from extensions.tsg.migration import TSG_MIGRATION_SQL
from extensions.tsg.models import (
    FIELD_TYPES,
    EVENT_TYPES,
    PERSON_TYPES,
    Company,
    CompanyField,
    CompanyPerson,
    CompanyEvent,
    CompanyArticle,
    ArticleHistory,
    CompanyBranch,
    AuthorityMatrix,
)


# ----------------------------------------------------------------
# Migration SQL testleri
# ----------------------------------------------------------------


def test_migration_sql_contains_all_table_names():
    """Migration SQL, 8 tablonun tamamını içermeli."""
    expected_tables = [
        "ext_company",
        "ext_company_field",
        "ext_company_person",
        "ext_company_event",
        "ext_company_article",
        "ext_article_history",
        "ext_company_branch",
        "ext_authority_matrix",
    ]
    for table in expected_tables:
        assert table in TSG_MIGRATION_SQL, f"Tablo bulunamadı: {table}"


def test_migration_sql_contains_all_indexes():
    """Migration SQL, tüm index tanımlarını içermeli."""
    expected_indexes = [
        "idx_company_mersis",
        "idx_company_name",
        "idx_field_company",
        "idx_field_type",
        "idx_person_company",
        "idx_person_name",
        "idx_event_company",
        "idx_event_date",
        "idx_article_company",
        "idx_authority_company",
    ]
    for index in expected_indexes:
        assert index in TSG_MIGRATION_SQL, f"Index bulunamadı: {index}"


def test_migration_sql_mersis_index_is_unique():
    """MERSIS indexi UNIQUE olmalı."""
    assert "idx_company_mersis" in TSG_MIGRATION_SQL
    # UNIQUE kelimesi idx_company_mersis tanımından sonra gelmeli
    idx_pos = TSG_MIGRATION_SQL.index("idx_company_mersis")
    snippet = TSG_MIGRATION_SQL[idx_pos: idx_pos + 100]
    assert "UNIQUE" in snippet, "MERSIS indexi UNIQUE değil"


# ----------------------------------------------------------------
# Company model testleri
# ----------------------------------------------------------------


def test_company_creation_with_defaults():
    """Company oluşturulduğunda varsayılan değerler doğru olmalı."""
    company = Company(unvan="Test A.Ş.")
    assert company.status == "aktif"
    assert company.gazette_count == 0
    assert company.id is None


def test_company_table_name():
    assert Company.table_name == "ext_company"


# ----------------------------------------------------------------
# CompanyField model testleri
# ----------------------------------------------------------------


def test_company_field_validates_valid_field_type():
    """Geçerli field_type değeri kabul edilmeli."""
    for ft in FIELD_TYPES:
        field = CompanyField(field_type=ft)
        assert field.field_type == ft


def test_company_field_rejects_invalid_field_type():
    """Geçersiz field_type değeri ValueError fırlatmalı."""
    with pytest.raises(ValueError, match="Geçersiz field_type"):
        CompanyField(field_type="gecersiz_tip")


def test_company_field_none_field_type_is_allowed():
    """field_type=None olduğunda hata fırlatılmamalı."""
    field = CompanyField(field_type=None)
    assert field.field_type is None


def test_company_field_defaults():
    """CompanyField varsayılan değerleri doğru olmalı."""
    field = CompanyField()
    assert field.is_active is True
    assert field.version == 1


# ----------------------------------------------------------------
# CompanyPerson model testleri
# ----------------------------------------------------------------


def test_company_person_defaults():
    """CompanyPerson varsayılan değerleri doğru olmalı."""
    person = CompanyPerson(ad_soyad="Ahmet Yılmaz")
    assert person.is_active is True
    assert person.entity_type == "gercek_kisi"


def test_company_person_table_name():
    assert CompanyPerson.table_name == "ext_company_person"


# ----------------------------------------------------------------
# CompanyEvent model testleri
# ----------------------------------------------------------------


def test_company_event_validates_valid_event_type():
    """Geçerli event_type değeri kabul edilmeli."""
    for et in EVENT_TYPES:
        event = CompanyEvent(event_type=et)
        assert event.event_type == et


def test_company_event_rejects_invalid_event_type():
    """Geçersiz event_type değeri ValueError fırlatmalı."""
    with pytest.raises(ValueError, match="Geçersiz event_type"):
        CompanyEvent(event_type="gecersiz_olay")


def test_company_event_none_event_type_is_allowed():
    """event_type=None olduğunda hata fırlatılmamalı."""
    event = CompanyEvent(event_type=None)
    assert event.event_type is None


def test_company_event_table_name():
    assert CompanyEvent.table_name == "ext_company_event"


# ----------------------------------------------------------------
# Sabit kümeler testleri
# ----------------------------------------------------------------


def test_field_types_constant():
    """FIELD_TYPES 7 değer içermeli."""
    assert len(FIELD_TYPES) == 7
    assert "sermaye" in FIELD_TYPES
    assert "adres" in FIELD_TYPES
    assert "hesap_donemi" in FIELD_TYPES


def test_event_types_constant():
    """EVENT_TYPES 22 değer içermeli."""
    assert len(EVENT_TYPES) == 22
    assert "kurulus" in EVENT_TYPES
    assert "tasfiye" in EVENT_TYPES
    assert "diger" in EVENT_TYPES


def test_person_types_constant():
    """PERSON_TYPES 5 değer içermeli."""
    assert len(PERSON_TYPES) == 5
    assert "yonetim" in PERSON_TYPES
    assert "ortak" in PERSON_TYPES
    assert "konkordato_komiseri" in PERSON_TYPES


# ----------------------------------------------------------------
# Diğer model table_name testleri
# ----------------------------------------------------------------


def test_all_table_names():
    """Tüm modellerin table_name değerleri doğru olmalı."""
    assert Company.table_name == "ext_company"
    assert CompanyField.table_name == "ext_company_field"
    assert CompanyPerson.table_name == "ext_company_person"
    assert CompanyEvent.table_name == "ext_company_event"
    assert CompanyArticle.table_name == "ext_company_article"
    assert ArticleHistory.table_name == "ext_article_history"
    assert CompanyBranch.table_name == "ext_company_branch"
    assert AuthorityMatrix.table_name == "ext_authority_matrix"
