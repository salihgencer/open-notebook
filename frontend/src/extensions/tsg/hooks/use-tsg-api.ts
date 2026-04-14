import { useQuery, useMutation } from '@tanstack/react-query'
import apiClient from '@/lib/api/client'
import type { Company, CompanyCard, CompanyPerson, CompanyEvent, ChatResponse } from '../types'

// Extension API'leri /api/ext/tsg altında — JWT token gerekiyor
// apiClient zaten auth header ekliyor

async function fetchWithExtAuth<T>(url: string): Promise<T> {
  // ext endpoint'leri için JWT token'ı localStorage'dan al
  const token = localStorage.getItem('notebooklm_access_token')
  const headers: Record<string, string> = {}
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }
  const response = await apiClient.get<T>(url, {
    baseURL: undefined, // override apiClient default
    headers,
  })
  return response.data
}

async function postWithExtAuth<T>(url: string, data: unknown): Promise<T> {
  const token = localStorage.getItem('notebooklm_access_token')
  const headers: Record<string, string> = {}
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }
  const response = await apiClient.post<T>(url, data, {
    baseURL: undefined,
    headers,
  })
  return response.data
}

export function useCompanies() {
  return useQuery({
    queryKey: ['tsg', 'companies'],
    queryFn: () => fetchWithExtAuth<Company[]>('/api/ext/tsg/companies'),
  })
}

export function useCompanyCard(companyId: string) {
  return useQuery({
    queryKey: ['tsg', 'company', companyId, 'card'],
    queryFn: () => fetchWithExtAuth<CompanyCard>(`/api/ext/tsg/companies/${companyId}/card`),
    enabled: !!companyId,
  })
}

export function useCompanyPersons(companyId: string, personType?: string) {
  return useQuery({
    queryKey: ['tsg', 'company', companyId, 'persons', personType],
    queryFn: () => {
      const params = personType ? `?person_type=${personType}` : ''
      return fetchWithExtAuth<CompanyPerson[]>(`/api/ext/tsg/companies/${companyId}/persons${params}`)
    },
    enabled: !!companyId,
  })
}

export function useCompanyTimeline(companyId: string, eventType?: string) {
  return useQuery({
    queryKey: ['tsg', 'company', companyId, 'timeline', eventType],
    queryFn: () => {
      const params = eventType ? `?event_type=${eventType}` : ''
      return fetchWithExtAuth<CompanyEvent[]>(`/api/ext/tsg/companies/${companyId}/timeline${params}`)
    },
    enabled: !!companyId,
  })
}

export function useTsgChat() {
  return useMutation({
    mutationFn: (data: { question: string; company_id: string }) =>
      postWithExtAuth<ChatResponse>('/api/ext/tsg/chat', data),
  })
}
