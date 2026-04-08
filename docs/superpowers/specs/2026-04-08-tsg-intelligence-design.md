# TSG Intelligence — Ticaret Sicil Gazetesi Akıllı Analiz Sistemi

**Tarih:** 2026-04-08
**Durum:** Onaylandı
**Temel:** open-notebook fork (salihgencer/open-notebook, develop branch)

---

## 1. Proje Özeti

Türk Ticaret Sicil Gazetesi (TSG) kayıtlarından şirket bilgilerini otomatik çıkaran, yapılandıran ve sorgulatan domain-specific bir sistem. open-notebook altyapısı üzerine inşa edilir.

Avukat ekibinin elle PPTX olarak hazırladığı şirket bilgi tablolarını (yetki kapsamları, imza yetkilileri, yönetim kurulu, ortaklık yapısı) otomatik üretir.

### Hedefler

- 512 OCR gazete dosyasından 36 şirketin yapılandırılmış verilerini çıkar
- Her bilgi alanı için en güncel gazete kaydını "geçerli" kabul et
- Chat ile doğal dil sorularına cevap ver (faktüel, kronoloji, analitik)
- 500+ şirket ölçeğine hazır

### Kullanıcılar

- Hukuk/muhasebe ekibi — due diligence, ortaklık kontrolü
- Yönetim/karar vericiler — portföy özeti, değişiklik takibi
- Her iki grup için hem detaylı tablo hem üst düzey özet

---

## 2. Veri Modeli (8 Tablo)

### 2.1 `ext_company` — Şirket Ana Kaydı

```
ext_company {
  id,
  notebook_id,              // open-notebook bağlantısı (1 şirket = 1 notebook)
  name,                     // güncel tam ünvan
  old_names,                // [eski ünvanlar listesi]
  short_name,               // kısa ad
  mersis_no,
  ticaret_sicil_no,
  ticaret_sicil_mudurlugu,
  company_type,             // "A.Ş." | "Ltd." | "Kooperatif"
  sector,                   // ana sektör (otomatik çıkarılır)
  status,                   // "aktif" | "tasfiye" | "terkin" | "konkordato"
  gazette_count,            // yüklü gazete sayısı
  last_gazette_date,
  last_gazette_no,
  created, updated
}
```

### 2.2 `ext_company_field` — Güncel Durum Alanları

Her bilgi alanı ayrı kayıt. Güncelleme kuralı: aynı company_id + field_type için yeni gazete geldiğinde, gazette_date daha yeniyse value güncellenir.

```
ext_company_field {
  id,
  company_id,               // → ext_company
  field_type,               // "sermaye" | "adres" | "faaliyet" | "temsil" | "denetci" | "sure" | "hesap_donemi"
  value,                    // güncel değer (text)
  gazette_date,
  gazette_no,
  ilan_kodu,                // (20229115) benzersiz ilan kimliği
  source_id,                // → source
  created, updated
}
```

### 2.3 `ext_company_person` — Kişiler

```
ext_company_person {
  id,
  company_id,
  person_type,              // "yonetim" | "ortak" | "denetci" | "tasfiye_memuru" | "konkordato_komiseri"
  entity_type,              // "gercek_kisi" | "tuzel_kisi"
  name,
  role,                     // "YK Başkanı" | "Müdür" | "Bağımsız Denetçi" vb.
  tc_no,
  uyruk,                    // "Türkiye" | "BAE" vb.
  temsilci_name,            // tüzel kişi üye ise gerçek kişi temsilci
  pay_amount,
  pay_ratio,                // ortaklar için (%)
  imza_derecesi,            // 1-8 arası
  imza_sekli,               // "munferit" | "musterek"
  imza_grubu,               // kimlerle birlikte imzalayabilir
  gorev_baslangic,
  gorev_bitis,
  is_active,                // en güncel gazetede hala var mı
  gazette_date,
  source_id,
  created, updated
}
```

### 2.4 `ext_company_event` — Kronoloji

```
ext_company_event {
  id,
  company_id,
  source_id,
  gazette_date,
  gazette_no,
  ilan_kodu,
  event_type,               // 20+ tür: kuruluş, sermaye, yonetim, adres, unvan,
                            // tasfiye, terkin, bolunme, konkordato, pay_devri,
                            // sube_acilis, sube_kapanis, merkez_nakli,
                            // ic_yonerge, acentelik, ttk198, ana_sozlesme_tadili,
                            // denetci, faaliyet, temsil, ek_tasfiye, diger
  summary,                  // 1-2 cümle Türkçe özet
  old_value,
  new_value,
  delil_belgesi,            // {noter_adi, noter_tarihi, yevmiye_no, karar_turu}
  raw_extraction,           // LLM'in çıkardığı tam JSON
  created
}
```

### 2.5 `ext_company_article` — Esas Sözleşme Maddeleri

```
ext_company_article {
  id,
  company_id,
  article_no,               // madde numarası (1, 2, 3...)
  article_title,            // "Şirketin Ünvanı" | "Amaç ve Konu" | "Sermaye" vb.
  current_text,             // güncel madde metni
  gazette_date,
  gazette_no,
  source_id,
  version,                  // kaçıncı versiyon (1 = kuruluş)
  created, updated
}
```

### 2.6 `ext_article_history` — Esas Sözleşme Değişiklik Geçmişi

```
ext_article_history {
  id,
  article_id,               // → ext_company_article
  company_id,
  article_no,
  article_title,
  old_text,
  new_text,
  change_summary,           // "Sermaye 10M TL → 50M TL artırıldı"
  gazette_date,
  gazette_no,
  source_id,
  version,                  // değişiklikten önceki versiyon no
  created
}
```

### 2.7 `ext_company_branch` — Şubeler

```
ext_company_branch {
  id,
  company_id,
  branch_name,
  branch_address,
  branch_sicil_no,
  branch_mersis_no,
  status,                   // "aktif" | "terkin"
  gazette_date,
  source_id,
  created, updated
}
```

### 2.8 `ext_authority_matrix` — İmza Yetki Matrisi

Avukat ekibinin PPTX'te elle hazırladığı "Yetki Kapsamları Tablosu"nun yapılandırılmış hali.

```
ext_authority_matrix {
  id,
  company_id,
  scope,                    // "merkez" | "sube"
  rule_no,                  // A.1, A.2, B.1, B.11.a vb.
  description,              // "Menkul ve gayrimenkul alımı ve satımı..."
  monetary_limit,           // "Sınırsız" | "10.000.000 TL" | null
  required_signers,         // "1. Derece (müşterek)" | "2. Derece VE 3. Derece"
  min_degree,               // en düşük gereken derece (sayısal)
  signing_type,             // "munferit" | "musterek"
  notes,                    // dipnotlar, özel koşullar
  ic_yonerge_ttsg_date,
  ic_yonerge_ttsg_no,
  gazette_date,
  source_id,
  created, updated
}
```

---

## 3. Extraction Pipeline

### Genel Akış (5 Aşama)

```
Dosya geldi (.txt)
    │
    ├── Aşama 1: DOĞRULAMA
    │   ├── Bozuk dosya tespiti (OCR mi, başka şey mi?)
    │   ├── Duplicate kontrolü (dosya hash'i)
    │   └── Minimum uzunluk kontrolü
    │
    ├── Aşama 2: BÖLME (Splitter)
    │   ├── Gazete tarih/sayı çıkar
    │   ├── Dosyadaki tüm şirket ilanlarını ayır
    │   │   (ipuçları: "TİCARET SİCİLİ MÜDÜRLÜĞÜ'NDEN", "İlan Sıra No:", "Ticaret Unvanı:")
    │   └── Her ilan → ayrı metin bloğu
    │
    ├── Aşama 3: EŞLEŞTIRME
    │   ├── Hedef şirket ilanını bul (klasör adı / mersis no ile)
    │   ├── Bulunamadıysa → dosya atla, log yaz
    │   └── İlan kodu çıkar
    │
    ├── Aşama 4: EXTRACTION (Gemma 4 ile, iki aşamalı)
    │   ├── 4a. Triage: işlem türü + temel meta → hızlı, kısa prompt
    │   └── 4b. Detay: işlem türüne göre özelleşmiş prompt → yapılandırılmış JSON
    │
    └── Aşama 5: KAYDETME
        ├── ext_company → oluştur veya güncelle
        ├── ext_company_field → tarih karşılaştır, güncelle
        ├── ext_company_person → listeyi güncelle (is_active)
        ├── ext_company_event → kronoloji kaydı ekle
        ├── ext_company_article → sözleşme maddeleri
        ├── ext_article_history → değişen maddeler
        ├── ext_authority_matrix → yetki matrisi
        ├── ext_company_branch → şube bilgileri
        └── Embedding → RAG için vektörize
```

### İki Aşamalı LLM Extraction

**Aşama 4a — Triage (hızlı):**
Kısa prompt ile işlem türü, gazete tarihi, ilan kodu, şirket ünvanı çıkarılır.

**Aşama 4b — Detay (işlem türüne göre):**
Her işlem türü için optimize edilmiş prompt. Örnek:
- kuruluş → tam ana sözleşme + ortaklar + yönetim
- yönetim → kişi listesi + görev + temsil
- sermaye → tutar + pay dağılımı + ödeme şekli
- ic_yonerge → yetki matrisi (derece, parasal sınır, işlem türü)

### Tespit Edilen İşlem Türleri (20+)

kuruluş, sermaye, yönetim, adres, ünvan, faaliyet, temsil, denetçi, pay_devri, ana_sozlesme_tadili, ic_yonerge, sube_acilis, sube_kapanis, merkez_nakli, tasfiye, terkin, konkordato, bölünme, ek_tasfiye, ttk198, acentelik, diger

### Edge Case'ler

- **Tek dosyada çoklu ilan:** Splitter aşamasında ayrılır
- **Sayfa devamı kopmaları:** "(Devamı X. Sayfada)" tespiti, mümkünse birleştirme
- **Duplicate dosyalar:** Dosya hash kontrolü ile engellenir
- **Bozuk dosyalar:** OCR içerik tespiti, minimum uzunluk kontrolü
- **Tüzel kişi ortak/yönetici:** entity_type alanı ile ayrılır, temsilci_name ile gerçek kişi kaydedilir
- **Yabancı uyruklu yönetici:** uyruk alanı ile desteklenir

### Klasör İzleme (File Watcher)

Konfigüre edilen klasör izlenir. Yeni .txt dosyası tespit edildiğinde klasör adı = şirket adı olarak pipeline otomatik başlar.

---

## 4. Chat & Sorgulama (Hibrit)

### Soru Yönlendirici (Router)

```
Kullanıcı sorusu
    │
    ├── FAKTÜEL → DB sorgusu (hızlı, tutarlı)
    │   "Sermayesi ne?" "Yönetim kurulu?" "10M üzeri kim imzalar?"
    │
    ├── KRONOLOJİ → Event tablosu
    │   "Sermaye ne zaman değişti?" "Son 2 yılda ne oldu?" "3. madde geçmişi?"
    │
    ├── ANALİTİK → RAG + LLM
    │   "Faaliyet konusu sağlık sektörüyle örtüşüyor mu?" "Kâr dağıtım politikası?"
    │
    └── KARŞILAŞTIRMA → Çoklu DB + LLM
        "Aydın Holding ile Memorial sermaye karşılaştırması"
        "Tüm şirketlerin güncel sermaye tablosu"
```

### Cevap Formatı

Her cevap şunları içerir:
- Cevap metni (kullanıcının seçtiği dil)
- Kaynak referansı (gazete tarihi ve sayısı)
- Güvenilirlik notu (DB'den direkt mi, LLM yorumu mu)

### Sistem Prompt'u

```
Sen bir Ticaret Sicil Gazetesi uzmanısın.

KURALLAR:
1. Her zaman EN GÜNCEL bilgiyi ver (en son gazete tarihli kayıt)
2. Cevabın kaynağını belirt (gazete tarihi ve sayısı)
3. Emin olmadığın bilgiyi tahmin etme
4. Birden fazla kayıt varsa kronolojik sırayı belirt
5. OCR hatası olabileceğini göz önünde bulundur
```

---

## 5. Rapor Çıktıları

Avukat ekibinin PPTX'te elle hazırladığı 6 tablo türünü otomatik üretir.

### Rapor Türleri

| # | Rapor | Veri Kaynağı |
|---|---|---|
| 1 | Şirket Bilgi Kartı | ext_company + ext_company_field |
| 2 | Yetki Kapsamları Tablosu | ext_authority_matrix |
| 3 | İmza Yetkilileri Tablosu | ext_company_person (derece bazlı) |
| 4 | Yönetim Kurulu Tablosu | ext_company_person (person_type=yonetim) |
| 5 | Ortaklık Yapısı | ext_company_person (person_type=ortak) |
| 6 | Değişiklik Kronolojisi | ext_company_event |

### Export Formatları

- Web UI — tablolar arayüzde render
- PDF — şirket raporu olarak indirme
- PPTX — avukat ekibinin mevcut formatıyla uyumlu
- Excel — toplu raporlar

### Toplu Rapor

Tüm şirketlerin tek sayfada özet tablosu (sermaye, yönetim, durum vb.)

---

## 6. Fazlar ve Başarı Kriterleri

### MVP — 36 Şirket Yüklü + Chat Çalışıyor

| Adım | İş | Başarı Kriteri |
|---|---|---|
| 1 | DB tabloları (8 ext_ tablo) | SurrealDB migration çalışır |
| 2 | Extraction pipeline | Tek gazete → yapılandırılmış JSON → DB |
| 3 | Toplu yükleme scripti | 512 dosya → 36 şirket otomatik işlenir |
| 4 | Hibrit chat router | Faktüel DB'den, analitik RAG'den cevaplanır |
| 5 | Temel rapor API'leri | Şirket kartı, yönetim, sermaye endpoint'leri |

### Faz 2 — Tam Tablo Seti

- Yetki kapsamları tablosu (authority matrix)
- Esas sözleşme maddeleri + değişiklik takibi
- Ortaklık yapısı tablosu
- Kronoloji raporu
- Karşılaştırma endpoint'leri

### Faz 3 — Raporlama & Otomasyon

- PDF/PPTX/Excel export
- Klasör izleme (file watcher)
- Toplu rapor (tüm şirketler)
- UI'da şirket kartları sayfası

### Faz 4 — İleri Özellikler

- Graph traversal (ortak yönetici, holding yapısı)
- Değişiklik bildirimleri (webhook/e-posta)
- PPTX formatında otomatik rapor (avukat ekibi uyumlu)

---

## 7. Teknik Altyapı

| Katman | Teknoloji |
|---|---|
| Platform | open-notebook fork (FastAPI + Next.js + SurrealDB v2) |
| LLM (extraction + chat) | Gemma 4 31B (uzak H100) |
| Embedding | Google Gemini Embedding 2 Preview |
| Auth | JWT + RBAC (mevcut extension) |
| i18n | TR/EN (mevcut extension) |
| Deploy | Docker Compose |
| Test | pytest + Vitest |

---

## 8. OCR Veri Kalitesi Notları

- Genel kalite: Orta-İyi (6/10)
- Gazete başlık/tarih/sayı genellikle temiz
- Tablo yapıları bozuk olabilir (sütun ayrımı kaybolmuş)
- Türkçe karakter tutarsızlıkları var
- Kimlik numaraları kasıtlı maskelenmiş
- Sayfa geçişlerinde metin akışı kopabilir
- Bazı dosyalarda OCR dışı içerik olabilir (kalite kontrolü gerekli)
