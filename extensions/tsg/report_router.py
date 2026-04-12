"""TSG Report API Router — Yapılandırılmış şirket verilerini sorgulayan REST endpoint'leri."""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query

from open_notebook.database.repository import repo_query


def _normalize_company(c: Dict[str, Any]) -> Dict[str, Any]:
    """DB alanlarını tutarlı API çıktısına dönüştürür."""
    return {
        "id": c.get("id"),
        "name": c.get("unvan", c.get("name", "")),
        "mersis_no": c.get("mersis_no"),
        "ticaret_sicil_no": c.get("ticaret_sicil_no"),
        "company_type": c.get("nevi", c.get("company_type")),
        "status": c.get("status", "aktif"),
        "gazette_count": c.get("gazette_count", 0),
        "last_gazette_date": c.get("last_gazette_date"),
    }


def _normalize_person(p: Dict[str, Any]) -> Dict[str, Any]:
    """Person DB alanlarını tutarlı API çıktısına dönüştürür."""
    return {
        "id": p.get("id"),
        "name": p.get("ad_soyad", p.get("name", "")),
        "person_type": p.get("person_type"),
        "role": p.get("gorev", p.get("role")),
        "tc_no": p.get("tc_kimlik", p.get("tc_no")),
        "uyruk": p.get("uyruk"),
        "pay_ratio": p.get("pay_orani", p.get("pay_ratio")),
        "pay_amount": p.get("pay_tutari", p.get("pay_amount")),
        "is_active": p.get("is_active", True),
        "gazette_date": p.get("gazette_date"),
    }


def _normalize_event(e: Dict[str, Any]) -> Dict[str, Any]:
    """Event DB alanlarını tutarlı API çıktısına dönüştürür."""
    return {
        "id": e.get("id"),
        "event_type": e.get("event_type", ""),
        "summary": e.get("aciklama", e.get("summary", "")),
        "gazette_date": e.get("gazette_date", e.get("event_date")),
        "gazette_no": e.get("gazette_issue", e.get("gazette_no")),
    }


def _normalize_field(f: Dict[str, Any]) -> Dict[str, Any]:
    """Field DB alanlarını tutarlı API çıktısına dönüştürür."""
    return {
        "id": f.get("id"),
        "field_type": f.get("field_type"),
        "value": f.get("value", f.get("deger", "")),
        "gazette_date": f.get("gazette_date"),
        "gazette_no": f.get("gazette_issue", f.get("gazette_no")),
    }


def create_tsg_report_router() -> APIRouter:
    router = APIRouter()

    @router.get("/companies")
    async def list_companies(
        status: Optional[str] = Query(None),
    ) -> List[Dict[str, Any]]:
        result = await repo_query("SELECT * FROM ext_company ORDER BY unvan")
        rows = result[0] if result and isinstance(result[0], list) else result
        companies = [_normalize_company(c) for c in rows]
        if status:
            companies = [c for c in companies if c.get("status") == status]
        return companies

    @router.get("/companies/{company_id}/card")
    async def get_company_card(company_id: str) -> Dict[str, Any]:
        cid = f"ext_company:{company_id}" if ":" not in company_id else company_id

        companies = await repo_query(f"SELECT * FROM {cid}")
        if not companies:
            raise HTTPException(status_code=404, detail="Şirket bulunamadı")

        fields = await repo_query(
            "SELECT * FROM ext_company_field WHERE company_id = $cid",
            {"cid": cid},
        )

        return {
            "company": _normalize_company(companies[0]),
            "fields": [_normalize_field(f) for f in (fields or [])],
        }

    @router.get("/companies/{company_id}/persons")
    async def get_company_persons(
        company_id: str,
        person_type: Optional[str] = Query(None),
        active_only: bool = Query(True),
    ) -> List[Dict[str, Any]]:
        cid = f"ext_company:{company_id}" if ":" not in company_id else company_id

        result = await repo_query(
            "SELECT * FROM ext_company_person WHERE company_id = $cid ORDER BY ad_soyad ASC",
            {"cid": cid},
        )
        rows = result[0] if result and isinstance(result[0], list) else result
        persons = [_normalize_person(p) for p in rows]

        if active_only:
            persons = [p for p in persons if p.get("is_active", True)]
        if person_type:
            persons = [p for p in persons if p.get("person_type") == person_type]

        return persons

    @router.get("/companies/{company_id}/timeline")
    async def get_company_timeline(
        company_id: str,
        event_type: Optional[str] = Query(None),
    ) -> List[Dict[str, Any]]:
        cid = f"ext_company:{company_id}" if ":" not in company_id else company_id

        result = await repo_query(
            "SELECT * FROM ext_company_event WHERE company_id = $cid ORDER BY gazette_date DESC",
            {"cid": cid},
        )
        rows = result[0] if result and isinstance(result[0], list) else result
        events = [_normalize_event(e) for e in rows]

        if event_type:
            events = [e for e in events if event_type in e.get("event_type", "")]

        return events

    @router.get("/companies/{company_id}/articles")
    async def get_company_articles(company_id: str) -> List[Dict[str, Any]]:
        cid = f"ext_company:{company_id}" if ":" not in company_id else company_id
        result = await repo_query(
            "SELECT * FROM ext_company_article WHERE company_id = $cid ORDER BY article_no ASC",
            {"cid": cid},
        )
        return result[0] if result and isinstance(result[0], list) else (result or [])

    @router.get("/companies/{company_id}/authority")
    async def get_company_authority(
        company_id: str,
        scope: Optional[str] = Query(None),
    ) -> List[Dict[str, Any]]:
        cid = f"ext_company:{company_id}" if ":" not in company_id else company_id
        result = await repo_query(
            "SELECT * FROM ext_authority_matrix WHERE company_id = $cid",
            {"cid": cid},
        )
        rows = result[0] if result and isinstance(result[0], list) else (result or [])
        if scope:
            rows = [a for a in rows if a.get("scope") == scope]
        return rows

    return router
