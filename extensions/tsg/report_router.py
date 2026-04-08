"""TSG Report API Router — Yapılandırılmış şirket verilerini sorgulayan REST endpoint'leri."""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query

from open_notebook.database.repository import repo_query


def create_tsg_report_router() -> APIRouter:
    """TSG report endpoint'lerini içeren APIRouter oluşturur."""

    router = APIRouter()

    @router.get("/companies")
    async def list_companies(
        status: Optional[str] = Query(None, description="Şirket durumu filtresi"),
    ) -> List[Dict[str, Any]]:
        """Tüm şirketleri listeler. Opsiyonel status filtresi desteklenir."""
        query = "SELECT * FROM ext_company ORDER BY name"
        result = await repo_query(query)

        # SurrealDB çoklu sorgu sonucu liste listesi döndürebilir
        rows: List[Dict[str, Any]] = result[0] if result and isinstance(result[0], list) else result

        if status is not None:
            rows = [c for c in rows if c.get("status") == status]

        return rows

    @router.get("/companies/{company_id}/card")
    async def get_company_card(company_id: str) -> Dict[str, Any]:
        """Şirket bilgi kartını döndürür: şirket detayları + alanlar."""
        cid = f"ext_company:{company_id}" if ":" not in company_id else company_id

        result = await repo_query(
            "SELECT * FROM $cid; SELECT * FROM ext_company_field WHERE company_id = $cid",
            {"cid": cid},
        )

        # İki sorgunun sonuçlarını ayır
        company_rows = result[0] if result else []
        field_rows = result[1] if len(result) > 1 else []

        # Liste listesi gelebilir
        if company_rows and isinstance(company_rows, list):
            companies = company_rows
        else:
            companies = []

        if not companies:
            raise HTTPException(status_code=404, detail=f"Şirket bulunamadı: {company_id}")

        fields = field_rows if isinstance(field_rows, list) else []

        return {"company": companies[0], "fields": fields}

    @router.get("/companies/{company_id}/persons")
    async def get_company_persons(
        company_id: str,
        person_type: Optional[str] = Query(None, description="Kişi türü filtresi"),
        active_only: bool = Query(True, description="Sadece aktif kişileri getir"),
    ) -> List[Dict[str, Any]]:
        """Şirkete ait kişileri döndürür."""
        cid = f"ext_company:{company_id}" if ":" not in company_id else company_id

        query = (
            "SELECT * FROM ext_company_person "
            "WHERE company_id = $cid "
            "ORDER BY imza_derecesi ASC, name ASC"
        )
        result = await repo_query(query, {"cid": cid})

        rows: List[Dict[str, Any]] = result[0] if result and isinstance(result[0], list) else result

        if active_only:
            rows = [p for p in rows if p.get("is_active", True)]

        if person_type is not None:
            rows = [p for p in rows if p.get("person_type") == person_type]

        return rows

    @router.get("/companies/{company_id}/timeline")
    async def get_company_timeline(
        company_id: str,
        event_type: Optional[str] = Query(None, description="Olay türü filtresi"),
    ) -> List[Dict[str, Any]]:
        """Şirket kronolojisini döndürür."""
        cid = f"ext_company:{company_id}" if ":" not in company_id else company_id

        query = (
            "SELECT * FROM ext_company_event "
            "WHERE company_id = $cid "
            "ORDER BY gazette_date DESC"
        )
        result = await repo_query(query, {"cid": cid})

        rows: List[Dict[str, Any]] = result[0] if result and isinstance(result[0], list) else result

        if event_type is not None:
            rows = [e for e in rows if e.get("event_type") == event_type]

        return rows

    @router.get("/companies/{company_id}/articles")
    async def get_company_articles(company_id: str) -> List[Dict[str, Any]]:
        """Şirketin güncel ana sözleşme maddelerini döndürür."""
        cid = f"ext_company:{company_id}" if ":" not in company_id else company_id

        query = (
            "SELECT * FROM ext_company_article "
            "WHERE company_id = $cid "
            "ORDER BY article_no ASC"
        )
        result = await repo_query(query, {"cid": cid})

        rows: List[Dict[str, Any]] = result[0] if result and isinstance(result[0], list) else result
        return rows

    @router.get("/companies/{company_id}/authority")
    async def get_company_authority(
        company_id: str,
        scope: Optional[str] = Query(None, description="Kapsam filtresi"),
    ) -> List[Dict[str, Any]]:
        """Şirketin yetki matrisini döndürür."""
        cid = f"ext_company:{company_id}" if ":" not in company_id else company_id

        query = (
            "SELECT * FROM ext_company_authority "
            "WHERE company_id = $cid "
            "ORDER BY min_degree ASC, rule_no ASC"
        )
        result = await repo_query(query, {"cid": cid})

        rows: List[Dict[str, Any]] = result[0] if result and isinstance(result[0], list) else result

        if scope is not None:
            rows = [a for a in rows if a.get("scope") == scope]

        return rows

    return router
