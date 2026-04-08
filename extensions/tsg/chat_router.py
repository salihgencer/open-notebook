"""TSG Chat Router — Soruları sınıflandırır ve doğru veri kaynağına yönlendirir."""

from typing import Any, Dict, List, Optional

import yaml
from fastapi import APIRouter
from pydantic import BaseModel

from extensions.tsg.extractor import call_llm, load_prompt, parse_json_response
from open_notebook.database.repository import repo_query


# ----------------------------------------------------------------
# Pydantic modeller
# ----------------------------------------------------------------


class ChatRequest(BaseModel):
    question: str
    company_id: Optional[str] = None
    language: str = "tr"


class ChatResponse(BaseModel):
    answer: str
    answer_type: str
    source: Optional[str] = None
    company_id: Optional[str] = None


# ----------------------------------------------------------------
# Yardımcı: classify_prompt'u YAML'dan yükle
# ----------------------------------------------------------------


def _load_classify_prompt() -> str:
    """chat_system.yaml dosyasından classify_prompt alanını yükler."""
    from pathlib import Path

    prompt_path = Path(__file__).parent / "prompts" / "chat_system.yaml"
    with open(prompt_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data["classify_prompt"]


# ----------------------------------------------------------------
# 1. Soru sınıflandırma
# ----------------------------------------------------------------


async def classify_question(question: str, company_id: Optional[str]) -> Dict:
    """
    Kullanıcı sorusunu sınıflandırır.

    chat_system.yaml'daki classify_prompt'u kullanır, LLM'e gönderir,
    JSON yanıtı ayrıştırır.

    Returns:
        type, company_id, field, event_type, detail alanlarını içeren dict
    """
    classify_template = _load_classify_prompt()
    prompt = classify_template.replace("{question}", question).replace(
        "{company_id}", company_id or "null"
    )
    response_text = await call_llm(prompt)
    return parse_json_response(response_text)


# ----------------------------------------------------------------
# 2. Faktüel soru yanıtlama
# ----------------------------------------------------------------


async def answer_factual(company_id: str, field: Optional[str]) -> Dict:
    """
    Belirli bir alan (field) için veritabanından veri getirir.

    field verilmezse tüm alanları döndürür.

    Returns:
        answer, source, type alanlarını içeren dict
    """
    cid = f"ext_company:{company_id}" if ":" not in company_id else company_id

    if field and field != "null":
        result = await repo_query(
            "SELECT * FROM ext_company_field WHERE company_id = $cid AND field_name = $field",
            {"cid": cid, "field": field},
        )
    else:
        result = await repo_query(
            "SELECT * FROM ext_company_field WHERE company_id = $cid",
            {"cid": cid},
        )

    rows: List[Dict[str, Any]] = result[0] if result and isinstance(result[0], list) else result

    if not rows:
        return {
            "answer": f"Bu bilgi mevcut kayıtlarda yok.",
            "source": None,
            "type": "db",
        }

    # En güncel kaydı öne al (gazette_date'e göre)
    rows_sorted = sorted(rows, key=lambda r: r.get("gazette_date", ""), reverse=True)
    latest = rows_sorted[0]

    source_parts = []
    if latest.get("gazette_date"):
        source_parts.append(latest["gazette_date"])
    if latest.get("gazette_no"):
        source_parts.append(f"Sayı: {latest['gazette_no']}")

    answer_lines = []
    for row in rows_sorted:
        fn = row.get("field_name", "")
        fv = row.get("field_value", "")
        answer_lines.append(f"{fn}: {fv}")

    return {
        "answer": "\n".join(answer_lines),
        "source": ", ".join(source_parts) if source_parts else None,
        "type": "db",
    }


# ----------------------------------------------------------------
# 3. Zaman çizelgesi soru yanıtlama
# ----------------------------------------------------------------


async def answer_timeline(company_id: str, event_type: Optional[str]) -> Dict:
    """
    Şirketin olay geçmişini tarih sırasıyla döndürür.

    Returns:
        answer, source, type alanlarını içeren dict
    """
    cid = f"ext_company:{company_id}" if ":" not in company_id else company_id

    if event_type and event_type != "null":
        result = await repo_query(
            "SELECT * FROM ext_company_event WHERE company_id = $cid AND event_type = $event_type ORDER BY gazette_date ASC",
            {"cid": cid, "event_type": event_type},
        )
    else:
        result = await repo_query(
            "SELECT * FROM ext_company_event WHERE company_id = $cid ORDER BY gazette_date ASC",
            {"cid": cid},
        )

    rows: List[Dict[str, Any]] = result[0] if result and isinstance(result[0], list) else result

    if not rows:
        return {
            "answer": "Bu şirkete ait kayıtlarda olay bulunamadı.",
            "source": f"0 gazete kaydından",
            "type": "db",
        }

    answer_lines = []
    for row in rows:
        date = row.get("gazette_date", "?")
        etype = row.get("event_type", "?")
        summary = row.get("summary") or row.get("description") or ""
        line = f"• {date} — {etype}"
        if summary:
            line += f": {summary}"
        answer_lines.append(line)

    return {
        "answer": "\n".join(answer_lines),
        "source": f"{len(rows)} gazete kaydından",
        "type": "db",
    }


# ----------------------------------------------------------------
# 4. Analitik soru yanıtlama
# ----------------------------------------------------------------


async def answer_analytic(company_id: str, question: str) -> Dict:
    """
    Şirket bağlamını toplayıp LLM ile analitik yanıt üretir.

    Returns:
        answer, source, type alanlarını içeren dict
    """
    cid = f"ext_company:{company_id}" if ":" not in company_id else company_id

    # Şirket bağlamını topla: alanlar + son olaylar
    fields_result = await repo_query(
        "SELECT * FROM ext_company_field WHERE company_id = $cid",
        {"cid": cid},
    )
    events_result = await repo_query(
        "SELECT * FROM ext_company_event WHERE company_id = $cid ORDER BY gazette_date DESC LIMIT 10",
        {"cid": cid},
    )

    field_rows: List[Dict[str, Any]] = (
        fields_result[0] if fields_result and isinstance(fields_result[0], list) else fields_result
    )
    event_rows: List[Dict[str, Any]] = (
        events_result[0] if events_result and isinstance(events_result[0], list) else events_result
    )

    # Bağlam metni oluştur
    context_parts = [f"Şirket ID: {company_id}"]

    if field_rows:
        context_parts.append("\n--- Şirket Alanları ---")
        for row in field_rows:
            context_parts.append(f"{row.get('field_name', '')}: {row.get('field_value', '')}")

    if event_rows:
        context_parts.append("\n--- Son Olaylar ---")
        for row in event_rows:
            context_parts.append(
                f"{row.get('gazette_date', '?')} - {row.get('event_type', '?')}: "
                f"{row.get('summary') or row.get('description') or ''}"
            )

    company_context = "\n".join(context_parts)

    # Sistem promptunu yükle ve LLM'e gönder
    system_prompt = load_prompt("chat_system")
    full_prompt = (
        f"{system_prompt}\n\n"
        f"ŞİRKET BİLGİLERİ:\n{company_context}\n\n"
        f"KULLANICI SORUSU: {question}"
    )

    answer_text = await call_llm(full_prompt)

    source_info = f"{len(field_rows)} alan, {len(event_rows)} olay kaydından"
    return {
        "answer": answer_text,
        "source": source_info,
        "type": "llm",
    }


# ----------------------------------------------------------------
# 5. API Router
# ----------------------------------------------------------------


def create_tsg_chat_router() -> APIRouter:
    """TSG chat endpoint'lerini içeren APIRouter oluşturur."""

    router = APIRouter()

    @router.post("/chat", response_model=ChatResponse)
    async def chat(request: ChatRequest) -> ChatResponse:
        """
        Kullanıcı sorusunu sınıflandırır ve uygun yanıt fonksiyonuna yönlendirir.
        """
        classification = await classify_question(request.question, request.company_id)

        q_type = classification.get("type", "analytic")
        cid = classification.get("company_id") or request.company_id
        field = classification.get("field")
        event_type = classification.get("event_type")

        if q_type == "factual" and cid:
            result = await answer_factual(cid, field)
        elif q_type == "timeline" and cid:
            result = await answer_timeline(cid, event_type)
        elif cid:
            result = await answer_analytic(cid, request.question)
        else:
            result = {
                "answer": "Şirket kimliği belirtilmedi. Lütfen hangi şirketi sorduğunuzu belirtin.",
                "source": None,
                "type": "error",
            }

        return ChatResponse(
            answer=result["answer"],
            answer_type=result["type"],
            source=result.get("source"),
            company_id=cid,
        )

    return router
