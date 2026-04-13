"""TSG Pipeline — Gazete dosyasından şirket verilerini uçtan uca işler.

Akış:
1. İçerik doğrulama
2. Tekrar tespiti (hash)
3. Gazete metadatası çıkarma
4. İlanları bölme
5. Şirket ilanını bulma
6. Triage çıkarımı (LLM)
7. Detay çıkarımı (LLM)
8. Şirket bul veya oluştur
9. Meta güncelle
10. Alan güncelle
11. Kişi güncelle
12. Olay ekle
"""

from typing import Any, Dict, Optional, Set

from extensions.tsg.extractor import detail_extract, triage_extract
from extensions.tsg.splitter import (
    extract_gazette_metadata,
    file_hash,
    find_company_announcement,
    split_announcements,
    validate_file_content,
)
from extensions.tsg.state_manager import (
    add_company_event,
    find_or_create_company,
    update_company_fields,
    update_company_meta,
    update_company_persons,
)

# Modül seviyesinde işlenmiş hash seti (tekrar tespiti)
_processed_hashes: Set[str] = set()


async def process_gazette_file(
    text: str,
    company_name: str,
    source_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Gazete dosyasını baştan sona işler ve şirket veritabanını günceller.

    Args:
        text: Ham gazete OCR metni.
        company_name: İşlenecek şirketin adı.
        source_id: Kaynak belge ID'si (opsiyonel).

    Returns:
        Başarı durumunda: {"success": True, "company_id": ..., "event_type": ...,
                           "gazette_date": ..., "gazette_no": ...}
        Hata durumunda: {"success": False, "error": "..."}
    """
    # Adım 1 — İçerik doğrulama
    if not validate_file_content(text):
        return {"success": False, "error": "Geçersiz dosya içeriği"}

    # Adım 2 — Tekrar tespiti
    content_hash = file_hash(text)
    if content_hash in _processed_hashes:
        return {"success": False, "error": "Duplicate dosya"}
    _processed_hashes.add(content_hash)

    try:
        # Adım 3 — Gazete metadatası
        metadata = extract_gazette_metadata(text)
        gazette_date: Optional[str] = metadata.get("date")
        gazette_no: Optional[str] = metadata.get("no")

        # Adım 4 — İlanları böl
        announcements = split_announcements(text)

        # Adım 5 — Şirket ilanını bul (3 kademeli fallback)
        from extensions.tsg.splitter import normalize_ocr
        announcement = find_company_announcement(announcements, company_name)

        if announcement is None:
            # Kademe 2: normalize_ocr ile tüm metinde satır bazlı arama
            norm_name_2 = normalize_ocr(" ".join(company_name.split()[:2]))
            norm_text = normalize_ocr(text)
            if norm_name_2 in norm_text:
                # Bulunan pozisyonun etrafındaki bloğu al (±50 satır)
                lines = text.split("\n")
                norm_lines = norm_text.split("\n")
                for i, line in enumerate(norm_lines):
                    if norm_name_2 in line:
                        start = max(0, i - 10)
                        end = min(len(lines), i + 50)
                        announcement = "\n".join(lines[start:end])
                        break

        if announcement is None:
            # Kademe 3: tüm metni değil, şirket adının geçtiği bloğu LLM'e ver
            # İlk kelimeyle bile eşleşme yoksa atla
            norm_first = normalize_ocr(company_name.split()[0])
            norm_full = normalize_ocr(text)
            if norm_first in norm_full:
                lines = text.split("\n")
                norm_lines = norm_full.split("\n")
                for i, line in enumerate(norm_lines):
                    if norm_first in line:
                        start = max(0, i - 5)
                        end = min(len(lines), i + 40)
                        announcement = "\n".join(lines[start:end])
                        break

        if announcement is None:
            return {"success": False, "error": f"Şirket ilanı bulunamadı: {company_name}"}

        # Adım 6 — Triage çıkarımı
        triage_result = await triage_extract(announcement)

        event_type: str = triage_result.get("islem_turu", "diger")
        mersis_no: Optional[str] = triage_result.get("mersis_no")

        # Adım 7 — Detay çıkarımı (hata olursa triage sonuçlarıyla devam et)
        try:
            detail_result = await detail_extract(announcement, event_type)
        except Exception as detail_err:
            from loguru import logger
            logger.warning(f"Detay extraction hatası, triage ile devam: {detail_err}")
            detail_result = {"fields": {}, "persons": [], "events": []}

        # Adım 8 — Şirketi bul veya oluştur
        company_id = await find_or_create_company(
            name=company_name,
            mersis_no=mersis_no,
        )

        # Adım 9 — Meta güncelle
        await update_company_meta(
            company_id=company_id,
            gazette_date=gazette_date,
            gazette_no=gazette_no,
        )

        # Adım 10 — Alan güncelle (varsa)
        fields = detail_result.get("fields")
        if fields:
            # fields liste olabilir; dict formatına çevir
            if isinstance(fields, list):
                fields_dict: Dict[str, Any] = {}
                for f in fields:
                    if isinstance(f, dict) and "field_type" in f:
                        fields_dict[f["field_type"]] = f
                fields = fields_dict
            if fields:
                await update_company_fields(
                    company_id=company_id,
                    fields=fields,
                    gazette_date=gazette_date or "",
                    source_id=source_id,
                    gazette_no=gazette_no,
                )

        # Adım 11 — Kişi güncelle (varsa)
        persons = detail_result.get("persons")
        if persons:
            await update_company_persons(
                company_id=company_id,
                persons=persons,
                gazette_date=gazette_date or "",
                source_id=source_id,
            )

        # Adım 12 — Olay ekle (her event için)
        events = detail_result.get("events") or []
        if not events:
            # En az bir olay ekle (triage sonucuna dayalı)
            summary = triage_result.get("sirket_unvani", company_name)
            await add_company_event(
                company_id=company_id,
                event_type=event_type,
                summary=summary,
                gazette_date=gazette_date,
                gazette_no=gazette_no,
                source_id=source_id,
            )
        else:
            for event in events:
                await add_company_event(
                    company_id=company_id,
                    event_type=event.get("event_type", event_type),
                    summary=event.get("summary", event.get("aciklama", "")),
                    gazette_date=gazette_date,
                    gazette_no=gazette_no,
                    source_id=source_id,
                )

        return {
            "success": True,
            "company_id": company_id,
            "event_type": event_type,
            "gazette_date": gazette_date,
            "gazette_no": gazette_no,
        }

    except Exception as exc:
        return {"success": False, "error": str(exc)}
