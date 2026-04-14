'use client'

import { AppShell } from '@/components/layout/AppShell'
import { CompanyTable } from '@/extensions/tsg/components/company-table'

export default function TsgDashboardPage() {
  return (
    <AppShell>
      <div className="flex-1 overflow-auto p-6">
        <CompanyTable />
      </div>
    </AppShell>
  )
}
