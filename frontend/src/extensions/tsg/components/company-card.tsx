'use client'

import { useCompanyCard } from '../hooks/use-tsg-api'

const FIELD_LABELS: Record<string, string> = {
  sermaye: 'Sermaye',
  adres: 'Adres',
  faaliyet: 'Faaliyet Konusu',
  temsil: 'Temsil Şekli',
  denetci: 'Denetçi',
  sure: 'Süre',
  hesap_donemi: 'Hesap Dönemi',
  tasfiye: 'Tasfiye',
}

export function CompanyCard({ companyId }: { companyId: string }) {
  const { data, isLoading } = useCompanyCard(companyId)

  if (isLoading) return <div className="text-muted-foreground p-4">Yükleniyor...</div>
  if (!data) return <div className="text-muted-foreground p-4">Veri bulunamadı</div>

  const { company, fields } = data

  return (
    <div className="space-y-6">
      {/* Şirket bilgileri */}
      <div className="grid grid-cols-2 gap-4">
        <InfoCard label="Ünvan" value={company.name} />
        <InfoCard label="Mersis No" value={company.mersis_no} />
        <InfoCard label="Ticaret Sicil No" value={company.ticaret_sicil_no} />
        <InfoCard label="Şirket Türü" value={company.company_type} />
        <InfoCard label="Durum" value={company.status} />
        <InfoCard label="Gazete Sayısı" value={String(company.gazette_count)} />
      </div>

      {/* Güncel alanlar */}
      {fields.length > 0 && (
        <div>
          <h3 className="text-sm font-semibold text-muted-foreground mb-3">Güncel Bilgiler</h3>
          <div className="grid grid-cols-1 gap-3">
            {fields.map((f) => (
              <div key={f.id} className="border rounded-lg p-3">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs font-medium text-muted-foreground uppercase">
                    {FIELD_LABELS[f.field_type] || f.field_type}
                  </span>
                  {f.gazette_date && (
                    <span className="text-xs text-muted-foreground">{f.gazette_date}</span>
                  )}
                </div>
                <div className="text-sm">{f.value || '—'}</div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

function InfoCard({ label, value }: { label: string; value?: string | null }) {
  return (
    <div className="border rounded-lg p-3">
      <div className="text-xs font-medium text-muted-foreground mb-1">{label}</div>
      <div className="text-sm font-medium">{value || '—'}</div>
    </div>
  )
}
