export interface Company {
  id: string
  name: string
  mersis_no?: string
  ticaret_sicil_no?: string
  company_type?: string
  status?: string
  gazette_count: number
  last_gazette_date?: string
}

export interface CompanyField {
  id: string
  field_type: string
  value: string
  gazette_date?: string
  gazette_no?: string
}

export interface CompanyPerson {
  id: string
  name: string
  person_type: string
  role?: string
  tc_no?: string
  uyruk?: string
  pay_ratio?: string
  pay_amount?: string
  is_active: boolean
  gazette_date?: string
}

export interface CompanyEvent {
  id: string
  event_type: string
  summary?: string
  gazette_date?: string
  gazette_no?: string
}

export interface CompanyCard {
  company: Company
  fields: CompanyField[]
}

export interface ChatResponse {
  answer: string
  answer_type: string
  source?: string
  company_id?: string
}
