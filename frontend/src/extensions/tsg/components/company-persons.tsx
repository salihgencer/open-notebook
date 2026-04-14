'use client'

import { useState } from 'react'
import { useCompanyPersons } from '../hooks/use-tsg-api'

const TYPE_LABELS: Record<string, string> = {
  yonetim: 'Yönetim Kurulu',
  ortak: 'Ortaklar',
  denetci: 'Denetçiler',
  tasfiye_memuru: 'Tasfiye Memuru',
  konkordato_komiseri: 'Konkordato Komiseri',
}

export function CompanyPersons({ companyId }: { companyId: string }) {
  const [filter, setFilter] = useState<string>('')
  const { data: persons, isLoading } = useCompanyPersons(companyId)

  if (isLoading) return <div className="text-muted-foreground p-4">Yükleniyor...</div>
  if (!persons?.length) return <div className="text-muted-foreground p-4">Kişi kaydı yok</div>

  // Türe göre grupla
  const groups: Record<string, typeof persons> = {}
  for (const p of persons) {
    const type = p.person_type || 'diger'
    if (filter && type !== filter) continue
    if (!groups[type]) groups[type] = []
    groups[type].push(p)
  }

  const types = Object.keys(TYPE_LABELS).filter((t) => persons.some((p) => p.person_type === t))

  return (
    <div className="space-y-6">
      {/* Filtre */}
      <div className="flex gap-2 flex-wrap">
        <button
          className={`px-3 py-1 text-xs rounded-md border ${!filter ? 'bg-primary text-primary-foreground' : ''}`}
          onClick={() => setFilter('')}
        >
          Tümü ({persons.length})
        </button>
        {types.map((t) => (
          <button
            key={t}
            className={`px-3 py-1 text-xs rounded-md border ${filter === t ? 'bg-primary text-primary-foreground' : ''}`}
            onClick={() => setFilter(filter === t ? '' : t)}
          >
            {TYPE_LABELS[t] || t} ({persons.filter((p) => p.person_type === t).length})
          </button>
        ))}
      </div>

      {/* Gruplar */}
      {Object.entries(groups).map(([type, list]) => (
        <div key={type}>
          <h3 className="text-sm font-semibold text-muted-foreground mb-2">
            {TYPE_LABELS[type] || type}
          </h3>
          <div className="border rounded-lg overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b bg-muted/50">
                  <th className="text-left p-2 font-medium">Ad Soyad</th>
                  <th className="text-left p-2 font-medium">Görev</th>
                  {type === 'ortak' && <th className="text-right p-2 font-medium">Pay Oranı</th>}
                  <th className="text-left p-2 font-medium w-28">Gazete Tarihi</th>
                </tr>
              </thead>
              <tbody>
                {list.map((p) => (
                  <tr key={p.id} className="border-b">
                    <td className="p-2 font-medium">{p.name || '—'}</td>
                    <td className="p-2 text-muted-foreground">{p.role || '—'}</td>
                    {type === 'ortak' && <td className="p-2 text-right tabular-nums">{p.pay_ratio || '—'}</td>}
                    <td className="p-2 text-muted-foreground text-xs">{p.gazette_date || '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ))}
    </div>
  )
}
