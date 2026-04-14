'use client'

import { useMemo, useState } from 'react'
import { useRouter } from 'next/navigation'
import { Input } from '@/components/ui/input'
import { useCompanies } from '../hooks/use-tsg-api'
import type { Company } from '../types'

export function CompanyTable() {
  const router = useRouter()
  const { data: companies, isLoading } = useCompanies()
  const [search, setSearch] = useState('')

  const filtered = useMemo(() => {
    if (!companies) return []
    if (!search.trim()) return companies
    const q = search.toLowerCase()
    return companies.filter((c) => (c.name || '').toLowerCase().includes(q))
  }, [companies, search])

  if (isLoading) {
    return <div className="flex items-center justify-center h-64 text-muted-foreground">Yükleniyor...</div>
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">TSG Intelligence</h1>
          <p className="text-muted-foreground text-sm">{companies?.length || 0} şirket</p>
        </div>
        <Input
          placeholder="Şirket ara..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-64"
        />
      </div>

      <div className="border rounded-lg overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b bg-muted/50">
              <th className="text-left p-3 font-medium">Şirket</th>
              <th className="text-right p-3 font-medium w-24">Gazete</th>
              <th className="text-left p-3 font-medium w-32">Son Tarih</th>
              <th className="text-left p-3 font-medium w-24">Durum</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((c) => (
              <tr
                key={c.id}
                className="border-b hover:bg-muted/30 cursor-pointer transition-colors"
                onClick={() => router.push(`/tsg/${encodeURIComponent(c.id)}`)}
              >
                <td className="p-3">
                  <div className="font-medium text-primary">{c.name || '—'}</div>
                  {c.mersis_no && <div className="text-xs text-muted-foreground">Mersis: {c.mersis_no}</div>}
                </td>
                <td className="p-3 text-right tabular-nums">{c.gazette_count}</td>
                <td className="p-3 text-muted-foreground">{c.last_gazette_date || '—'}</td>
                <td className="p-3">
                  <span className={`inline-flex items-center gap-1 text-xs ${c.status === 'aktif' ? 'text-green-500' : 'text-yellow-500'}`}>
                    <span className="w-1.5 h-1.5 rounded-full bg-current" />
                    {c.status || 'aktif'}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {filtered.length === 0 && (
          <div className="p-8 text-center text-muted-foreground">Sonuç bulunamadı</div>
        )}
      </div>
    </div>
  )
}
