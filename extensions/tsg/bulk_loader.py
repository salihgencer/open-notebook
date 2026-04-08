"""TSG Bulk Loader — Şirket klasörlerinden gazete dosyalarını toplu yükler.

Kullanım:
    python -m extensions.tsg.bulk_loader /path/to/base_dir

Klasör yapısı beklentisi:
    base_dir/
        ŞİRKET ADI 1/
            gazete1.txt
            gazete2.txt
        ŞİRKET ADI 2/
            ...
"""

import asyncio
import sys
from pathlib import Path
from typing import Dict

from loguru import logger

from extensions.tsg.migration import run_tsg_migration
from extensions.tsg.pipeline import process_gazette_file


async def load_company_folder(folder_path: str, company_name: str) -> Dict[str, int]:
    """Bir şirket klasöründeki tüm .txt dosyalarını işler.

    Args:
        folder_path: İşlenecek klasörün yolu.
        company_name: Şirketin adı (klasör adından türetilir).

    Returns:
        {"total": N, "success": N, "skipped": N, "error": N} istatistikleri.
    """
    folder = Path(folder_path)
    txt_files = sorted(folder.glob("*.txt"))

    stats: Dict[str, int] = {"total": 0, "success": 0, "skipped": 0, "error": 0}

    for txt_file in txt_files:
        stats["total"] += 1
        try:
            text = txt_file.read_text(encoding="utf-8", errors="replace")
            result = await process_gazette_file(text, company_name, source_id=txt_file.name)

            if result.get("success"):
                stats["success"] += 1
                logger.debug(
                    f"[{company_name}] İşlendi: {txt_file.name} "
                    f"(event={result.get('event_type')}, tarih={result.get('gazette_date')})"
                )
            else:
                error_msg = result.get("error", "Bilinmeyen hata")
                if "duplicate" in error_msg.lower():
                    stats["skipped"] += 1
                    logger.debug(f"[{company_name}] Atlandı (duplicate): {txt_file.name}")
                else:
                    stats["error"] += 1
                    logger.warning(
                        f"[{company_name}] Hata — {txt_file.name}: {error_msg}"
                    )
        except Exception as exc:
            stats["error"] += 1
            logger.warning(f"[{company_name}] Beklenmeyen hata — {txt_file.name}: {exc}")

    return stats


async def load_all_companies(base_dir: str) -> None:
    """Temel dizindeki tüm şirket klasörlerini sırayla yükler.

    Args:
        base_dir: Şirket alt klasörlerini içeren temel dizin.
    """
    # Önce migration'ı çalıştır
    logger.info("TSG migration başlatılıyor...")
    await run_tsg_migration()
    logger.info("TSG migration tamamlandı.")

    base = Path(base_dir)
    if not base.is_dir():
        logger.error(f"Temel dizin bulunamadı: {base_dir}")
        return

    # Alt dizinleri listele (nokta ile başlayanları atla)
    company_folders = sorted(
        [d for d in base.iterdir() if d.is_dir() and not d.name.startswith(".")]
    )

    if not company_folders:
        logger.warning(f"Yüklenecek şirket klasörü bulunamadı: {base_dir}")
        return

    logger.info(f"Toplam {len(company_folders)} şirket klasörü bulundu.")

    # Genel istatistikler
    total_stats: Dict[str, int] = {"total": 0, "success": 0, "skipped": 0, "error": 0}

    for folder in company_folders:
        company_name = folder.name
        logger.info(f"Yükleniyor: {company_name} ({folder})")

        company_stats = await load_company_folder(str(folder), company_name)

        # Genel istatistiklere ekle
        for key in total_stats:
            total_stats[key] += company_stats[key]

        # Şirket özeti
        logger.info(
            f"  {'✅' if company_stats['error'] == 0 else '⚠️'} {company_name}: "
            f"toplam={company_stats['total']} | "
            f"başarılı={company_stats['success']} | "
            f"atlandı={company_stats['skipped']} | "
            f"hata={company_stats['error']}"
        )

    # Genel özet
    logger.info("=" * 60)
    logger.info("BULK LOAD TAMAMLANDI")
    logger.info(f"  📁 Şirket sayısı  : {len(company_folders)}")
    logger.info(f"  📄 Toplam dosya   : {total_stats['total']}")
    logger.info(f"  ✅ Başarılı        : {total_stats['success']}")
    logger.info(f"  ⏭️  Atlandı         : {total_stats['skipped']}")
    logger.info(f"  ❌ Hata            : {total_stats['error']}")
    logger.info("=" * 60)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Kullanım: python -m extensions.tsg.bulk_loader <base_dir>")
        sys.exit(1)

    base_dir = sys.argv[1]
    asyncio.run(load_all_companies(base_dir))
