# TSG Intelligence Frontend

**Tarih:** 2026-04-14
**Durum:** Onaylandı

---

## 1. Özet

TSG Intelligence verilerini tarayıcıdan görüntüleyen frontend. İki sayfa: dashboard (şirket tablosu) ve detay (4 sekmeli).

## 2. Sayfalar

### Dashboard — `/tsg`

- 35 şirketin aranabilir tablosu
- Sütunlar: Şirket adı, sektör, gazete sayısı, son gazete tarihi, durum
- Arama kutusu (ünvana göre filtre)
- Şirkete tıklayınca detay sayfasına yönlendir
- API: `GET /api/ext/tsg/companies`

### Detay — `/tsg/[company_id]`

4 sekme:

**Sekme 1: Kimlik Kartı**
- Şirket bilgileri kartı: ünvan, mersis, ticaret sicil no, adres, sermaye, temsil, durum
- Grid layout, her alan kaynak tarihiyle birlikte
- API: `GET /api/ext/tsg/companies/{id}/card`

**Sekme 2: Yönetim & Ortaklar**
- Yönetim kurulu tablosu (ad, görev, imza derecesi)
- Ortaklar tablosu (ad, pay oranı, pay tutarı)
- API: `GET /api/ext/tsg/companies/{id}/persons`

**Sekme 3: Kronoloji**
- Zaman çizelgesi görünümü — tarih, işlem türü, özet
- Event type filtresi (dropdown)
- API: `GET /api/ext/tsg/companies/{id}/timeline`

**Sekme 4: Chat**
- Doğal dil soru kutusu
- Cevap + kaynak referansı gösterimi
- API: `POST /api/ext/tsg/chat`

## 3. Teknik

- `frontend/src/extensions/tsg/` altında
- Mevcut auth provider (JWT token) kullanılır
- Mevcut i18n provider kullanılır
- open-notebook'un mevcut Tailwind + shadcn/ui stil sistemi
- Next.js App Router: `frontend/src/app/(dashboard)/tsg/` altında sayfa route'ları

## 4. Dosya Yapısı

```
frontend/src/
├── app/(dashboard)/tsg/
│   ├── page.tsx                    # Dashboard sayfası
│   └── [companyId]/
│       └── page.tsx                # Detay sayfası
│
├── extensions/tsg/
│   ├── components/
│   │   ├── company-table.tsx       # Dashboard tablosu
│   │   ├── company-card.tsx        # Kimlik kartı sekmesi
│   │   ├── company-persons.tsx     # Yönetim & Ortaklar sekmesi
│   │   ├── company-timeline.tsx    # Kronoloji sekmesi
│   │   └── company-chat.tsx        # Chat sekmesi
│   ├── hooks/
│   │   └── use-tsg-api.ts          # API çağrıları hook'u
│   └── types.ts                    # TypeScript tipleri
```

## 5. Kapsam Dışı (Faz 2)

- Esas Sözleşme sekmesi
- Yetki Matrisi sekmesi
- PPTX/PDF export
- Şirket karşılaştırma
