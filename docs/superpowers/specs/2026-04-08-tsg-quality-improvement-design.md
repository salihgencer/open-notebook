# TSG Extraction Kalite İyileştirmesi

**Tarih:** 2026-04-08
**Durum:** Onaylandı
**Hedef:** Extraction başarı oranını %60'tan %95+'a çıkarmak

---

## 1. Problem Analizi

Mevcut durum (Aydın Holding 10 dosya testi): %60 başarı oranı.

| Hata Türü | Oran | Kök Neden |
|---|---|---|
| İlan bulundu ama şirket eşleşmedi | ~%30 | OCR karakter farkları (Í vs İ, HOLDING vs HOLDİNG) |
| İlan hiç ayrılamadı | ~%5 | Splitter pattern dosyayı parse edemedi |
| JSON parse hatası | ~%40 | LLM yanıtı kesik veya farklı formatta |
| Geçersiz dosya | ~%3 | OCR yerine başka içerik |

Kritik keşif: `AYDIN HOLDING ANONÍM ŞİRKETİ` — OCR `İ` yerine `Í` (Latin I with acute) yazmış. Mevcut normalize fonksiyonu bu varyantları yakalayamıyor.

---

## 2. Çözüm: 3 Katmanlı İyileştirme

### Katman 1: Agresif OCR Normalizasyon

`splitter.py`'daki `_TR_NORMALIZE` genişletilir:

```python
_NORMALIZE_MAP = str.maketrans({
    # Türkçe → ASCII
    'Ğ': 'G', 'ğ': 'g', 'İ': 'I', 'ı': 'i',
    'Ö': 'O', 'ö': 'o', 'Ü': 'U', 'ü': 'u',
    'Ş': 'S', 'ş': 's', 'Ç': 'C', 'ç': 'c',
    # OCR aksan hataları
    'Í': 'I', 'í': 'i', 'Ì': 'I', 'ì': 'i', 'Î': 'I', 'î': 'i',
    'É': 'E', 'é': 'e', 'È': 'E', 'è': 'e', 'Ë': 'E', 'ë': 'e', 'Ê': 'E', 'ê': 'e',
    'Ó': 'O', 'ó': 'o', 'Ò': 'O', 'ò': 'o', 'Ô': 'O', 'ô': 'o',
    'Ú': 'U', 'ú': 'u', 'Ù': 'U', 'ù': 'u', 'Û': 'U', 'û': 'u',
    'Á': 'A', 'á': 'a', 'À': 'A', 'à': 'a', 'Â': 'A', 'â': 'a',
    'Ș': 'S', 'ș': 's', 'Ț': 'T', 'ț': 't',
})

def normalize_ocr(text: str) -> str:
    return text.upper().translate(_NORMALIZE_MAP)
```

Tüm şirket eşleştirmeleri `normalize_ocr()` üzerinden geçer.

### Katman 2: 3 Kademeli Fallback

Mevcut: tek pattern → eşleşme yok → fail.

Yeni:

```
Kademe 1: split_announcements → find_company (normalize_ocr ile)
    Başarılı → devam
    │
Kademe 2: Tüm metinde ngram arama
    Şirket adının ilk 2 kelimesini normalize_ocr ile ara
    Bulunduysa → o satırın etrafındaki blok (±50 satır) = ilan metni
    │
Kademe 3: Tüm metni LLM'e ver
    "Bu metinde {şirket_adı} hakkındaki ilanı bul ve ayır"
    LLM çıktısı = ilan metni
```

### Katman 3: Prompt İyileştirme + JSON Güvenilirliği

**Triage prompt:**
- Daha kısa talimat
- "SADECE JSON döndür, başka metin EKLEME" vurgusu
- Daha az alan (6 alan yeterli)

**Detay prompt:**
- fields düzleştirilir: `{"sermaye": "50M TL", "adres": "..."}` (iç içe obje yok)
- Her alan grubu net ayrılmış

**JSON parse güvenilirliği:**
1. İlk parse: mevcut mantık (markdown temizle → düz JSON → { } bul)
2. Başarısızsa: regex ile tüm JSON bloklarını bul, en büyüğünü al
3. Hala başarısızsa: LLM'e retry — "Şu yanıtını geçerli JSON olarak düzelt" (max 1 retry)

---

## 3. Başarı Ölçümü

Bulk loader her dosya için detaylı loglama:

```
Sonuç raporu:
  Toplam: 512 dosya
  İlan bulundu: X / 512 (%Y)    — Katman 1+2 başarısı
  Triage başarılı: X / bulunan  — Katman 3 triage
  Detay başarılı: X / triage    — Katman 3 detay
  DB'ye yazıldı: X / 512 (%Y)  — Genel başarı
```

**Hedef: DB'ye yazıldı >= %95 (512 dosyadan 486+)**

---

## 4. Dosya Değişiklikleri

| Dosya | Değişiklik |
|---|---|
| `extensions/tsg/splitter.py` | normalize_ocr fonksiyonu, genişletilmiş karakter mapping |
| `extensions/tsg/pipeline.py` | 3 kademeli fallback zinciri |
| `extensions/tsg/extractor.py` | JSON parse retry, geliştirilmiş hata toleransı |
| `extensions/tsg/prompts/triage.yaml` | Kısaltılmış, net talimat |
| `extensions/tsg/prompts/genel.yaml` | Düzleştirilmiş JSON schema |
| `extensions/tsg/bulk_loader.py` | Detaylı başarı raporu |
| `tests/extensions/test_tsg_splitter.py` | OCR varyant testleri |
| `tests/extensions/test_tsg_extractor.py` | JSON retry testleri |
