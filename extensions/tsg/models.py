"""TSG Pydantic modelleri — 8 tablo için ObjectModel tabanlı şema tanımları."""

from typing import Any, ClassVar, Dict, List, Optional

from open_notebook.domain.base import ObjectModel

# ----------------------------------------------------------------
# Sabit değer kümeleri
# ----------------------------------------------------------------
FIELD_TYPES = (
    "sermaye",
    "adres",
    "faaliyet",
    "temsil",
    "denetci",
    "sure",
    "hesap_donemi",
)

EVENT_TYPES = (
    "kurulus",
    "sermaye",
    "yonetim",
    "adres",
    "unvan",
    "faaliyet",
    "temsil",
    "denetci",
    "pay_devri",
    "ana_sozlesme_tadili",
    "ic_yonerge",
    "sube_acilis",
    "sube_kapanis",
    "merkez_nakli",
    "tasfiye",
    "terkin",
    "konkordato",
    "bolunme",
    "ek_tasfiye",
    "ttk198",
    "acentelik",
    "diger",
)

PERSON_TYPES = (
    "yonetim",
    "ortak",
    "denetci",
    "tasfiye_memuru",
    "konkordato_komiseri",
)


# ----------------------------------------------------------------
# Model tanımları
# ----------------------------------------------------------------


class Company(ObjectModel):
    """Şirket ana kaydı."""

    table_name: ClassVar[str] = "ext_company"

    mersis_no: Optional[str] = None
    ticaret_sicil_no: Optional[str] = None
    unvan: Optional[str] = None
    eski_unvanlar: Optional[List[str]] = None
    nevi: Optional[str] = None
    status: Optional[str] = "aktif"
    il: Optional[str] = None
    ilce: Optional[str] = None
    sicil_mudurlugu: Optional[str] = None
    gazette_count: int = 0
    raw_extraction: Optional[Dict[str, Any]] = None


class CompanyField(ObjectModel):
    """Şirketin güncel durum alanları (sermaye, adres vb.)."""

    table_name: ClassVar[str] = "ext_company_field"

    company_id: Optional[str] = None
    field_type: Optional[str] = None
    value: Optional[str] = None
    gazette_issue: Optional[str] = None
    gazette_date: Optional[str] = None
    is_active: bool = True
    version: int = 1
    raw_extraction: Optional[Dict[str, Any]] = None

    def __init__(self, **data):
        if "field_type" in data and data["field_type"] is not None:
            if data["field_type"] not in FIELD_TYPES:
                raise ValueError(
                    f"Geçersiz field_type: '{data['field_type']}'. "
                    f"Geçerli değerler: {FIELD_TYPES}"
                )
        super().__init__(**data)


class CompanyPerson(ObjectModel):
    """Şirket kişileri — yönetim, ortak, denetçi vb."""

    table_name: ClassVar[str] = "ext_company_person"

    company_id: Optional[str] = None
    person_type: Optional[str] = None
    ad_soyad: Optional[str] = None
    tc_kimlik: Optional[str] = None
    uyruk: Optional[str] = None
    entity_type: Optional[str] = "gercek_kisi"
    gorev: Optional[str] = None
    pay_orani: Optional[str] = None
    pay_tutari: Optional[str] = None
    gazette_issue: Optional[str] = None
    gazette_date: Optional[str] = None
    is_active: bool = True
    raw_extraction: Optional[Dict[str, Any]] = None


class CompanyEvent(ObjectModel):
    """Şirket kronoloji olayları."""

    table_name: ClassVar[str] = "ext_company_event"

    company_id: Optional[str] = None
    event_type: Optional[str] = None
    event_date: Optional[str] = None
    gazette_issue: Optional[str] = None
    gazette_date: Optional[str] = None
    aciklama: Optional[str] = None
    delil_belgesi: Optional[Dict[str, Any]] = None
    raw_extraction: Optional[Dict[str, Any]] = None

    def __init__(self, **data):
        if "event_type" in data and data["event_type"] is not None:
            if data["event_type"] not in EVENT_TYPES:
                raise ValueError(
                    f"Geçersiz event_type: '{data['event_type']}'. "
                    f"Geçerli değerler: {EVENT_TYPES}"
                )
        super().__init__(**data)


class CompanyArticle(ObjectModel):
    """Esas sözleşme maddeleri."""

    table_name: ClassVar[str] = "ext_company_article"

    company_id: Optional[str] = None
    article_no: int = 0
    baslik: Optional[str] = None
    icerik: Optional[str] = None
    gazette_issue: Optional[str] = None
    gazette_date: Optional[str] = None
    is_active: bool = True
    raw_extraction: Optional[Dict[str, Any]] = None


class ArticleHistory(ObjectModel):
    """Sözleşme maddesi değişiklik geçmişi."""

    table_name: ClassVar[str] = "ext_article_history"

    article_id: Optional[str] = None
    company_id: Optional[str] = None
    article_no: int = 0
    eski_icerik: Optional[str] = None
    yeni_icerik: Optional[str] = None
    gazette_issue: Optional[str] = None
    gazette_date: Optional[str] = None
    version: int = 1
    raw_extraction: Optional[Dict[str, Any]] = None


class CompanyBranch(ObjectModel):
    """Şube kayıtları."""

    table_name: ClassVar[str] = "ext_company_branch"

    company_id: Optional[str] = None
    sube_adi: Optional[str] = None
    sube_sicil_no: Optional[str] = None
    il: Optional[str] = None
    ilce: Optional[str] = None
    adres: Optional[str] = None
    gazette_issue: Optional[str] = None
    gazette_date: Optional[str] = None
    is_active: bool = True
    raw_extraction: Optional[Dict[str, Any]] = None


class AuthorityMatrix(ObjectModel):
    """İmza yetki matrisi."""

    table_name: ClassVar[str] = "ext_authority_matrix"

    company_id: Optional[str] = None
    person_id: Optional[str] = None
    ad_soyad: Optional[str] = None
    yetki_turu: Optional[str] = None
    yetki_siniri: Optional[str] = None
    min_degree: Optional[int] = None
    gazette_issue: Optional[str] = None
    gazette_date: Optional[str] = None
    is_active: bool = True
    old_names: Optional[List[str]] = None
    raw_extraction: Optional[Dict[str, Any]] = None
