"""TSG veritabanı migration — 8 tablo ve index tanımları."""

from open_notebook.database.repository import repo_query

TSG_MIGRATION_SQL = """
-- ============================================================
-- ext_company: Şirket ana kaydı
-- ============================================================
DEFINE TABLE ext_company SCHEMAFULL;
DEFINE FIELD mersis_no         ON TABLE ext_company TYPE option<string>;
DEFINE FIELD ticaret_sicil_no  ON TABLE ext_company TYPE option<string>;
DEFINE FIELD unvan             ON TABLE ext_company TYPE option<string>;
DEFINE FIELD eski_unvanlar     ON TABLE ext_company TYPE option<array>;
DEFINE FIELD nevi               ON TABLE ext_company TYPE option<string>;
DEFINE FIELD status             ON TABLE ext_company TYPE option<string>;
DEFINE FIELD il                 ON TABLE ext_company TYPE option<string>;
DEFINE FIELD ilce               ON TABLE ext_company TYPE option<string>;
DEFINE FIELD sicil_mudurlugu    ON TABLE ext_company TYPE option<string>;
DEFINE FIELD gazette_count      ON TABLE ext_company TYPE int DEFAULT 0;
DEFINE FIELD raw_extraction     ON TABLE ext_company TYPE option<object>;

DEFINE INDEX idx_company_mersis   ON TABLE ext_company COLUMNS mersis_no UNIQUE;
DEFINE INDEX idx_company_name     ON TABLE ext_company COLUMNS unvan;

-- ============================================================
-- ext_company_field: Güncel durum alanları
-- ============================================================
DEFINE TABLE ext_company_field SCHEMAFULL;
DEFINE FIELD company_id     ON TABLE ext_company_field TYPE option<string>;
DEFINE FIELD field_type     ON TABLE ext_company_field TYPE option<string>;
DEFINE FIELD value          ON TABLE ext_company_field TYPE option<string>;
DEFINE FIELD gazette_issue  ON TABLE ext_company_field TYPE option<string>;
DEFINE FIELD gazette_date   ON TABLE ext_company_field TYPE option<string>;
DEFINE FIELD is_active      ON TABLE ext_company_field TYPE bool DEFAULT true;
DEFINE FIELD version        ON TABLE ext_company_field TYPE int DEFAULT 1;
DEFINE FIELD raw_extraction ON TABLE ext_company_field TYPE option<object>;

DEFINE INDEX idx_field_company ON TABLE ext_company_field COLUMNS company_id;
DEFINE INDEX idx_field_type    ON TABLE ext_company_field COLUMNS field_type;

-- ============================================================
-- ext_company_person: Kişiler — yönetim/ortak/denetçi
-- ============================================================
DEFINE TABLE ext_company_person SCHEMAFULL;
DEFINE FIELD company_id     ON TABLE ext_company_person TYPE option<string>;
DEFINE FIELD person_type    ON TABLE ext_company_person TYPE option<string>;
DEFINE FIELD ad_soyad       ON TABLE ext_company_person TYPE option<string>;
DEFINE FIELD tc_kimlik      ON TABLE ext_company_person TYPE option<string>;
DEFINE FIELD uyruk          ON TABLE ext_company_person TYPE option<string>;
DEFINE FIELD entity_type    ON TABLE ext_company_person TYPE option<string>;
DEFINE FIELD gorev          ON TABLE ext_company_person TYPE option<string>;
DEFINE FIELD pay_orani      ON TABLE ext_company_person TYPE option<string>;
DEFINE FIELD pay_tutari     ON TABLE ext_company_person TYPE option<string>;
DEFINE FIELD gazette_issue  ON TABLE ext_company_person TYPE option<string>;
DEFINE FIELD gazette_date   ON TABLE ext_company_person TYPE option<string>;
DEFINE FIELD is_active      ON TABLE ext_company_person TYPE bool DEFAULT true;
DEFINE FIELD raw_extraction ON TABLE ext_company_person TYPE option<object>;

DEFINE INDEX idx_person_company ON TABLE ext_company_person COLUMNS company_id;
DEFINE INDEX idx_person_name    ON TABLE ext_company_person COLUMNS ad_soyad;

-- ============================================================
-- ext_company_event: Kronoloji
-- ============================================================
DEFINE TABLE ext_company_event SCHEMAFULL;
DEFINE FIELD company_id     ON TABLE ext_company_event TYPE option<string>;
DEFINE FIELD event_type     ON TABLE ext_company_event TYPE option<string>;
DEFINE FIELD event_date     ON TABLE ext_company_event TYPE option<string>;
DEFINE FIELD gazette_issue  ON TABLE ext_company_event TYPE option<string>;
DEFINE FIELD gazette_date   ON TABLE ext_company_event TYPE option<string>;
DEFINE FIELD aciklama        ON TABLE ext_company_event TYPE option<string>;
DEFINE FIELD delil_belgesi  ON TABLE ext_company_event TYPE option<object>;
DEFINE FIELD raw_extraction ON TABLE ext_company_event TYPE option<object>;

DEFINE INDEX idx_event_company ON TABLE ext_company_event COLUMNS company_id;
DEFINE INDEX idx_event_date    ON TABLE ext_company_event COLUMNS event_date;

-- ============================================================
-- ext_company_article: Esas sözleşme maddeleri
-- ============================================================
DEFINE TABLE ext_company_article SCHEMAFULL;
DEFINE FIELD company_id     ON TABLE ext_company_article TYPE option<string>;
DEFINE FIELD article_no     ON TABLE ext_company_article TYPE int;
DEFINE FIELD baslik          ON TABLE ext_company_article TYPE option<string>;
DEFINE FIELD icerik          ON TABLE ext_company_article TYPE option<string>;
DEFINE FIELD gazette_issue  ON TABLE ext_company_article TYPE option<string>;
DEFINE FIELD gazette_date   ON TABLE ext_company_article TYPE option<string>;
DEFINE FIELD is_active      ON TABLE ext_company_article TYPE bool DEFAULT true;
DEFINE FIELD raw_extraction ON TABLE ext_company_article TYPE option<object>;

DEFINE INDEX idx_article_company ON TABLE ext_company_article COLUMNS company_id;

-- ============================================================
-- ext_article_history: Sözleşme değişiklik geçmişi
-- ============================================================
DEFINE TABLE ext_article_history SCHEMAFULL;
DEFINE FIELD article_id     ON TABLE ext_article_history TYPE option<string>;
DEFINE FIELD company_id     ON TABLE ext_article_history TYPE option<string>;
DEFINE FIELD article_no     ON TABLE ext_article_history TYPE int;
DEFINE FIELD eski_icerik    ON TABLE ext_article_history TYPE option<string>;
DEFINE FIELD yeni_icerik    ON TABLE ext_article_history TYPE option<string>;
DEFINE FIELD gazette_issue  ON TABLE ext_article_history TYPE option<string>;
DEFINE FIELD gazette_date   ON TABLE ext_article_history TYPE option<string>;
DEFINE FIELD version        ON TABLE ext_article_history TYPE int DEFAULT 1;
DEFINE FIELD raw_extraction ON TABLE ext_article_history TYPE option<object>;

-- ============================================================
-- ext_company_branch: Şubeler
-- ============================================================
DEFINE TABLE ext_company_branch SCHEMAFULL;
DEFINE FIELD company_id         ON TABLE ext_company_branch TYPE option<string>;
DEFINE FIELD sube_adi           ON TABLE ext_company_branch TYPE option<string>;
DEFINE FIELD sube_sicil_no      ON TABLE ext_company_branch TYPE option<string>;
DEFINE FIELD il                  ON TABLE ext_company_branch TYPE option<string>;
DEFINE FIELD ilce                ON TABLE ext_company_branch TYPE option<string>;
DEFINE FIELD adres               ON TABLE ext_company_branch TYPE option<string>;
DEFINE FIELD gazette_issue      ON TABLE ext_company_branch TYPE option<string>;
DEFINE FIELD gazette_date       ON TABLE ext_company_branch TYPE option<string>;
DEFINE FIELD is_active          ON TABLE ext_company_branch TYPE bool DEFAULT true;
DEFINE FIELD raw_extraction     ON TABLE ext_company_branch TYPE option<object>;

-- ============================================================
-- ext_authority_matrix: İmza yetki matrisi
-- ============================================================
DEFINE TABLE ext_authority_matrix SCHEMAFULL;
DEFINE FIELD company_id     ON TABLE ext_authority_matrix TYPE option<string>;
DEFINE FIELD person_id      ON TABLE ext_authority_matrix TYPE option<string>;
DEFINE FIELD ad_soyad       ON TABLE ext_authority_matrix TYPE option<string>;
DEFINE FIELD yetki_turu     ON TABLE ext_authority_matrix TYPE option<string>;
DEFINE FIELD yetki_siniri   ON TABLE ext_authority_matrix TYPE option<string>;
DEFINE FIELD min_degree     ON TABLE ext_authority_matrix TYPE option<int>;
DEFINE FIELD gazette_issue  ON TABLE ext_authority_matrix TYPE option<string>;
DEFINE FIELD gazette_date   ON TABLE ext_authority_matrix TYPE option<string>;
DEFINE FIELD is_active      ON TABLE ext_authority_matrix TYPE bool DEFAULT true;
DEFINE FIELD old_names      ON TABLE ext_authority_matrix TYPE option<array>;
DEFINE FIELD raw_extraction ON TABLE ext_authority_matrix TYPE option<object>;

DEFINE INDEX idx_authority_company ON TABLE ext_authority_matrix COLUMNS company_id;
"""


async def run_tsg_migration() -> None:
    """TSG tablolarını ve indexlerini SurrealDB'de oluşturur (idempotent)."""
    from loguru import logger
    try:
        await repo_query(TSG_MIGRATION_SQL)
    except RuntimeError as e:
        if "already exists" in str(e):
            logger.debug(f"TSG tabloları zaten mevcut: {e}")
        else:
            raise
