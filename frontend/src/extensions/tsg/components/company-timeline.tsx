'use client'

import { useState } from 'react'
import { useCompanyTimeline } from '../hooks/use-tsg-api'

const EVENT_LABELS: Record<string, string> = {
  kurulus: 'Kuruluş',
  sermaye: 'Sermaye',
  yonetim: 'Yönetim',
  adres: 'Adres',
  unvan: 'Ünvan',
  faaliyet: 'Faaliyet',
  temsil: 'Temsil',
  denetci: 'Denetçi',
  pay_devri: 'Pay Devri',
  ana_sozlesme_tadili: 'Ana Sözleşme',
  ic_yonerge: 'İç Yönerge',
  sube_acilis: 'Şube Açılış',
  sube_kapanis: 'Şube Kapanış',
  merkez_nakli: 'Merkez Nakli',
  tasfiye: 'Tasfiye',
  terkin: 'Terkin',
  konkordato: 'Konkordato',
  ttk198: 'TTK 198',
  diger: 'Diğer',
}

const EVENT_COLORS: Record<string, string> = {
  kurulus: 'bg-green-500',
  sermaye: 'bg-blue-500',
  yonetim: 'bg-purple-500',
  adres: 'bg-yellow-500',
  tasfiye: 'bg-red-500',
  terkin: 'bg-red-700',
}

export function CompanyTimeline({ companyId }: { companyId: string }) {
  const [filter, setFilter] = useState<string>('')
  const { data: events, isLoading } = useCompanyTimeline(companyId)

  if (isLoading) return <div className="text-muted-foreground p-4">Yükleniyor...</div>
  if (!events?.length) return <div className="text-muted-foreground p-4">Kronoloji kaydı yok</div>

  const filtered = filter ? events.filter((e) => (e.event_type || '').includes(filter)) : events
  const uniqueTypes = [...new Set(events.map((e) => e.event_type?.split('|')[0] || 'diger'))]

  return (
    <div className="space-y-4">
      {/* Filtre */}
      <div className="flex gap-2 flex-wrap">
        <button
          className={`px-3 py-1 text-xs rounded-md border ${!filter ? 'bg-primary text-primary-foreground' : ''}`}
          onClick={() => setFilter('')}
        >
          Tümü ({events.length})
        </button>
        {uniqueTypes.map((t) => (
          <button
            key={t}
            className={`px-3 py-1 text-xs rounded-md border ${filter === t ? 'bg-primary text-primary-foreground' : ''}`}
            onClick={() => setFilter(filter === t ? '' : t)}
          >
            {EVENT_LABELS[t] || t}
          </button>
        ))}
      </div>

      {/* Timeline */}
      <div className="space-y-1">
        {filtered.map((e, i) => {
          const mainType = (e.event_type || 'diger').split('|')[0]
          const color = EVENT_COLORS[mainType] || 'bg-gray-500'
          return (
            <div key={e.id || i} className="flex items-start gap-3 p-3 border rounded-lg">
              <div className="flex flex-col items-center gap-1 min-w-[90px]">
                <span className="text-xs font-mono text-muted-foreground">
                  {e.gazette_date || '—'}
                </span>
                <span className={`px-2 py-0.5 text-[10px] rounded-full text-white ${color}`}>
                  {EVENT_LABELS[mainType] || mainType}
                </span>
              </div>
              <div className="flex-1 min-w-0">
                <div className="text-sm">{e.summary || e.event_type || '—'}</div>
                {e.gazette_no && (
                  <div className="text-xs text-muted-foreground mt-1">TTSG Sayı: {e.gazette_no}</div>
                )}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
