"""TSG State Manager — Şirket verilerini SurrealDB'de günceller.

Temel kural: ext_company_field için yalnızca yeni gazette_date > mevcut gazette_date
ise güncelleme yapılır (her zaman en güncel bilgi korunur).
"""

from typing import Any, Dict, List, Optional

from loguru import logger

from open_notebook.database.repository import repo_create, repo_query, repo_update


# ----------------------------------------------------------------
# Yardımcı fonksiyon: tarih karşılaştırma
# ----------------------------------------------------------------


def _is_newer_date(new_date: str, existing_date: str) -> bool:
    """Yeni tarih mevcut tarihten daha büyükse True döndürür.

    Tarihler ISO 8601 string formatında beklenir (ör. "2024-01-15").
    Karşılaştırma string olarak yapılır; YYYY-MM-DD formatında doğru çalışır.
    """
    if not existing_date:
        return True
    if not new_date:
        return False
    return new_date > existing_date


# ----------------------------------------------------------------
# 1. find_or_create_company
# ----------------------------------------------------------------


async def find_or_create_company(
    name: str,
    mersis_no: Optional[str] = None,
    **kwargs: Any,
) -> str:
    """Şirketi mersis_no veya isme göre arar; bulamazsa yeni kayıt oluşturur.

    Args:
        name: Şirket adı (zorunlu).
        mersis_no: MERSİS numarası (opsiyonel, önce bununla aranır).
        **kwargs: Yeni kayıt oluştururken eklenecek ek alanlar.

    Returns:
        Şirketin ID string'i (ör. "ext_company:abc123").
    """
    # Önce mersis_no ile ara
    if mersis_no:
        results = await repo_query(
            "SELECT * FROM ext_company WHERE mersis_no = $mersis_no LIMIT 1",
            {"mersis_no": mersis_no},
        )
        if results and len(results) > 0:
            records = results[0] if isinstance(results[0], list) else results
            if isinstance(records, list) and len(records) > 0:
                record = records[0]
                company_id = record.get("id")
                logger.debug(f"Şirket mersis_no ile bulundu: {company_id}")
                return str(company_id)
            elif isinstance(records, dict):
                company_id = records.get("id")
                logger.debug(f"Şirket mersis_no ile bulundu: {company_id}")
                return str(company_id)

    # İsimle ara
    name_results = await repo_query(
        "SELECT * FROM ext_company WHERE unvan = $unvan LIMIT 1",
        {"unvan": name},
    )
    if name_results and len(name_results) > 0:
        records = name_results[0] if isinstance(name_results[0], list) else name_results
        if isinstance(records, list) and len(records) > 0:
            record = records[0]
            company_id = record.get("id")
            logger.debug(f"Şirket isme göre bulundu: {company_id}")
            return str(company_id)
        elif isinstance(records, dict):
            company_id = records.get("id")
            logger.debug(f"Şirket isme göre bulundu: {company_id}")
            return str(company_id)

    # Bulunamadı — yeni kayıt oluştur
    data: Dict[str, Any] = {"unvan": name, "gazette_count": 0}
    if mersis_no:
        data["mersis_no"] = mersis_no
    data.update(kwargs)

    created = await repo_create("ext_company", data)
    # repo_create liste veya dict döndürebilir
    if isinstance(created, list):
        created = created[0]
    company_id = created.get("id")
    logger.info(f"Yeni şirket oluşturuldu: {company_id}")
    return str(company_id)


# ----------------------------------------------------------------
# 2. update_company_meta
# ----------------------------------------------------------------


async def update_company_meta(
    company_id: str,
    gazette_date: Optional[str] = None,
    gazette_no: Optional[str] = None,
    **kwargs: Any,
) -> None:
    """Şirketin meta verilerini günceller.

    gazette_count +1 artırılır. last_gazette_date ve last_gazette_no
    sağlanmışsa güncellenir.

    Args:
        company_id: Şirketin tam ID'si (ör. "ext_company:abc123").
        gazette_date: Gazete tarihi (opsiyonel).
        gazette_no: Gazete numarası (opsiyonel).
        **kwargs: Ekstra güncellenecek alanlar.
    """
    # gazette_count artır
    from open_notebook.database.repository import ensure_record_id
    await repo_query(
        f"UPDATE {company_id} SET gazette_count += 1",
    )

    # last_gazette_date ve last_gazette_no güncelle
    update_data: Dict[str, Any] = {}
    if gazette_date is not None:
        update_data["last_gazette_date"] = gazette_date
    if gazette_no is not None:
        update_data["last_gazette_no"] = gazette_no
    update_data.update(kwargs)

    if update_data:
        await repo_update("ext_company", company_id, update_data)

    logger.debug(f"Şirket meta güncellendi: {company_id}")


# ----------------------------------------------------------------
# 3. update_company_fields
# ----------------------------------------------------------------


async def update_company_fields(
    company_id: str,
    fields: Dict[str, Dict[str, Any]],
    gazette_date: str,
    source_id: Optional[str] = None,
    gazette_no: Optional[str] = None,
    ilan_kodu: Optional[str] = None,
) -> None:
    """Şirketin alan bilgilerini (sermaye, adres vb.) günceller.

    Her alan için:
    - Mevcut kayıt yoksa yeni oluşturulur.
    - Mevcut kayıt varsa ve yeni gazette_date > mevcut ise güncellenir.
    - Mevcut kayıt varsa ve yeni gazette_date <= mevcut ise ATLANIR.

    Args:
        company_id: Şirket ID'si.
        fields: Alan sözlüğü. Format: {"sermaye": {"value": "50M TL"}, ...}
        gazette_date: Bu güncellemenin gazete tarihi.
        source_id: Kaynak belge ID'si (opsiyonel).
        gazette_no: Gazete numarası (opsiyonel).
        ilan_kodu: İlan kodu (opsiyonel).
    """
    for field_type, field_data in fields.items():
        value = field_data.get("value") if isinstance(field_data, dict) else field_data

        # Mevcut kaydı kontrol et
        existing_results = await repo_query(
            "SELECT * FROM ext_company_field WHERE company_id = $cid AND field_type = $ft LIMIT 1",
            {"cid": company_id, "ft": field_type},
        )

        existing_record = None
        if existing_results and len(existing_results) > 0:
            records = existing_results[0] if isinstance(existing_results[0], list) else existing_results
            if isinstance(records, list) and len(records) > 0:
                existing_record = records[0]
            elif isinstance(records, dict) and records.get("id"):
                existing_record = records

        if existing_record is None:
            # Yeni kayıt oluştur
            new_data: Dict[str, Any] = {
                "company_id": company_id,
                "field_type": field_type,
                "value": value,
                "gazette_date": gazette_date,
                "is_active": True,
                "version": 1,
            }
            if gazette_no:
                new_data["gazette_issue"] = gazette_no
            if source_id:
                new_data["source_id"] = source_id
            if ilan_kodu:
                new_data["ilan_kodu"] = ilan_kodu

            await repo_create("ext_company_field", new_data)
            logger.debug(f"Yeni alan oluşturuldu: {field_type} — şirket: {company_id}")

        else:
            # Tarih karşılaştırması yap
            existing_date = existing_record.get("gazette_date", "")
            if _is_newer_date(gazette_date, existing_date):
                # Güncelle
                record_id = existing_record.get("id")
                update_data: Dict[str, Any] = {
                    "value": value,
                    "gazette_date": gazette_date,
                }
                if gazette_no:
                    update_data["gazette_issue"] = gazette_no
                if source_id:
                    update_data["source_id"] = source_id
                if ilan_kodu:
                    update_data["ilan_kodu"] = ilan_kodu

                await repo_update("ext_company_field", str(record_id), update_data)
                logger.debug(
                    f"Alan güncellendi: {field_type} — şirket: {company_id} "
                    f"({existing_date} → {gazette_date})"
                )
            else:
                # Atla — mevcut daha güncel
                logger.debug(
                    f"Alan atlandı (daha yeni mevcut): {field_type} — şirket: {company_id} "
                    f"(mevcut: {existing_date}, yeni: {gazette_date})"
                )


# ----------------------------------------------------------------
# 4. update_company_persons
# ----------------------------------------------------------------


async def update_company_persons(
    company_id: str,
    persons: List[Dict[str, Any]],
    gazette_date: str,
    source_id: Optional[str] = None,
) -> None:
    """Şirket kişilerini (yönetim, ortak, denetçi vb.) oluşturur.

    Her kişi için yeni bir ext_company_person kaydı açılır.

    Args:
        company_id: Şirket ID'si.
        persons: Kişi listesi. Her eleman dict formatındadır.
        gazette_date: Bu güncellemenin gazete tarihi.
        source_id: Kaynak belge ID'si (opsiyonel).
    """
    for person in persons:
        person_data: Dict[str, Any] = {
            "company_id": company_id,
            "gazette_date": gazette_date,
            "is_active": True,
        }
        person_data.update(person)
        if source_id:
            person_data["source_id"] = source_id

        await repo_create("ext_company_person", person_data)
        logger.debug(
            f"Kişi oluşturuldu: {person.get('ad_soyad', 'bilinmiyor')} — şirket: {company_id}"
        )


# ----------------------------------------------------------------
# 5. add_company_event
# ----------------------------------------------------------------


async def add_company_event(
    company_id: str,
    event_type: str,
    summary: str,
    gazette_date: Optional[str] = None,
    gazette_no: Optional[str] = None,
    source_id: Optional[str] = None,
    **kwargs: Any,
) -> str:
    """Şirket için yeni bir olay (event) kaydı oluşturur.

    Args:
        company_id: Şirket ID'si.
        event_type: Olay türü (ör. "kurulus", "sermaye").
        summary: Olay özeti / açıklaması.
        gazette_date: Gazete tarihi (opsiyonel).
        gazette_no: Gazete numarası (opsiyonel).
        source_id: Kaynak belge ID'si (opsiyonel).
        **kwargs: Ekstra alan değerleri.

    Returns:
        Oluşturulan ext_company_event kaydının ID string'i.
    """
    event_data: Dict[str, Any] = {
        "company_id": company_id,
        "event_type": event_type,
        "aciklama": summary,
    }
    if gazette_date is not None:
        event_data["gazette_date"] = gazette_date
        event_data["event_date"] = gazette_date
    if gazette_no is not None:
        event_data["gazette_issue"] = gazette_no
    if source_id is not None:
        event_data["source_id"] = source_id
    event_data.update(kwargs)

    created = await repo_create("ext_company_event", event_data)
    if isinstance(created, list):
        created = created[0]
    event_id = created.get("id")
    logger.info(f"Şirket olayı oluşturuldu: {event_id} — tür: {event_type}")
    return str(event_id)
