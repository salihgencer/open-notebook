import { useQuery, useMutation } from '@tanstack/react-query'
import type { Company, CompanyCard, CompanyPerson, CompanyEvent, ChatResponse } from '../types'

// TSG extension API'leri — /api/ext/tsg altında
// apiClient /api prefix ekliyor, ext endpoint'leri direkt fetch ile çağırıyoruz

async function tsgFetch<T>(path: string): Promise<T> {
  const token = localStorage.getItem('notebooklm_access_token')
  const headers: Record<string, string> = { 'Content-Type': 'application/json' }
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }

  // open-notebook password auth (localStorage auth-storage'dan)
  const authStorage = localStorage.getItem('auth-storage')
  if (authStorage && !token) {
    try {
      const { state } = JSON.parse(authStorage)
      if (state?.password) {
        headers['Authorization'] = `Bearer ${state.password}`
      }
    } catch {}
  }

  const res = await fetch(`/api/ext/tsg${path}`, { headers })
  if (!res.ok) throw new Error(`TSG API error: ${res.status}`)
  return res.json()
}

async function tsgPost<T>(path: string, data: unknown): Promise<T> {
  const token = localStorage.getItem('notebooklm_access_token')
  const headers: Record<string, string> = { 'Content-Type': 'application/json' }
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }
  const authStorage = localStorage.getItem('auth-storage')
  if (authStorage && !token) {
    try {
      const { state } = JSON.parse(authStorage)
      if (state?.password) {
        headers['Authorization'] = `Bearer ${state.password}`
      }
    } catch {}
  }

  const res = await fetch(`/api/ext/tsg${path}`, {
    method: 'POST',
    headers,
    body: JSON.stringify(data),
  })
  if (!res.ok) throw new Error(`TSG API error: ${res.status}`)
  return res.json()
}

export function useCompanies() {
  return useQuery({
    queryKey: ['tsg', 'companies'],
    queryFn: () => tsgFetch<Company[]>('/companies'),
  })
}

export function useCompanyCard(companyId: string) {
  return useQuery({
    queryKey: ['tsg', 'company', companyId, 'card'],
    queryFn: () => tsgFetch<CompanyCard>(`/companies/${encodeURIComponent(companyId)}/card`),
    enabled: !!companyId,
  })
}

export function useCompanyPersons(companyId: string, personType?: string) {
  return useQuery({
    queryKey: ['tsg', 'company', companyId, 'persons', personType],
    queryFn: () => {
      const params = personType ? `?person_type=${personType}` : ''
      return tsgFetch<CompanyPerson[]>(`/companies/${encodeURIComponent(companyId)}/persons${params}`)
    },
    enabled: !!companyId,
  })
}

export function useCompanyTimeline(companyId: string, eventType?: string) {
  return useQuery({
    queryKey: ['tsg', 'company', companyId, 'timeline', eventType],
    queryFn: () => {
      const params = eventType ? `?event_type=${eventType}` : ''
      return tsgFetch<CompanyEvent[]>(`/companies/${encodeURIComponent(companyId)}/timeline${params}`)
    },
    enabled: !!companyId,
  })
}

export function useTsgChat() {
  return useMutation({
    mutationFn: (data: { question: string; company_id: string }) =>
      tsgPost<ChatResponse>('/chat', data),
  })
}
