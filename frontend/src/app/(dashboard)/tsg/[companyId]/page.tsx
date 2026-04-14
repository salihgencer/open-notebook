'use client'

import { useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { AppShell } from '@/components/layout/AppShell'
import { Button } from '@/components/ui/button'
import { ArrowLeft } from 'lucide-react'
import { CompanyCard } from '@/extensions/tsg/components/company-card'
import { CompanyPersons } from '@/extensions/tsg/components/company-persons'
import { CompanyTimeline } from '@/extensions/tsg/components/company-timeline'
import { CompanyChat } from '@/extensions/tsg/components/company-chat'
import { useCompanyCard } from '@/extensions/tsg/hooks/use-tsg-api'

const TABS = [
  { id: 'card', label: '📋 Kimlik Kartı' },
  { id: 'persons', label: '👥 Yönetim & Ortaklar' },
  { id: 'timeline', label: '📅 Kronoloji' },
  { id: 'chat', label: '💬 Chat' },
] as const

type TabId = (typeof TABS)[number]['id']

export default function CompanyDetailPage() {
  const params = useParams()
  const router = useRouter()
  const companyId = decodeURIComponent(params.companyId as string)
  const [activeTab, setActiveTab] = useState<TabId>('card')

  const { data } = useCompanyCard(companyId)
  const companyName = data?.company?.name || 'Yükleniyor...'

  return (
    <AppShell>
      <div className="flex-1 overflow-auto">
        {/* Header */}
        <div className="border-b px-6 py-4">
          <div className="flex items-center gap-3 mb-2">
            <Button variant="ghost" size="icon" onClick={() => router.push('/tsg')}>
              <ArrowLeft className="h-4 w-4" />
            </Button>
            <div>
              <h1 className="text-xl font-bold">{companyName}</h1>
              {data?.company?.mersis_no && (
                <p className="text-sm text-muted-foreground">
                  Mersis: {data.company.mersis_no} | {data.company.gazette_count} gazete
                </p>
              )}
            </div>
          </div>

          {/* Tabs */}
          <div className="flex gap-1 mt-3">
            {TABS.map((tab) => (
              <button
                key={tab.id}
                className={`px-4 py-2 text-sm rounded-md transition-colors ${
                  activeTab === tab.id
                    ? 'bg-primary text-primary-foreground'
                    : 'hover:bg-muted'
                }`}
                onClick={() => setActiveTab(tab.id)}
              >
                {tab.label}
              </button>
            ))}
          </div>
        </div>

        {/* Tab content */}
        <div className="p-6">
          {activeTab === 'card' && <CompanyCard companyId={companyId} />}
          {activeTab === 'persons' && <CompanyPersons companyId={companyId} />}
          {activeTab === 'timeline' && <CompanyTimeline companyId={companyId} />}
          {activeTab === 'chat' && <CompanyChat companyId={companyId} />}
        </div>
      </div>
    </AppShell>
  )
}
