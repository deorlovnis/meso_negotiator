import type {
  AgreeResponse,
  CardLabel,
  EndResponse,
  OffersResponse,
  ResetResponse,
  SecureResponse,
} from './types'

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    public readonly detail: unknown,
  ) {
    super(`API error ${status}`)
    this.name = 'ApiError'
  }
}

async function fetchApi<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(path, options)
  if (!response.ok) {
    let detail: unknown = null
    try {
      detail = await response.json()
    } catch {
      detail = await response.text()
    }
    throw new ApiError(response.status, detail)
  }
  return response.json() as Promise<T>
}

export function getOffers(id: string): Promise<OffersResponse> {
  return fetchApi<OffersResponse>(`/api/negotiations/${id}/offers`)
}

export function agree(id: string, cardLabel: CardLabel): Promise<AgreeResponse> {
  return fetchApi<AgreeResponse>(`/api/negotiations/${id}/agree`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ card_label: cardLabel }),
  })
}

export function secure(id: string, cardLabel: CardLabel): Promise<SecureResponse> {
  return fetchApi<SecureResponse>(`/api/negotiations/${id}/secure`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ card_label: cardLabel }),
  })
}

export function improve(id: string, cardLabel: CardLabel): Promise<OffersResponse> {
  return fetchApi<OffersResponse>(`/api/negotiations/${id}/improve`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ card_label: cardLabel }),
  })
}

export function endNegotiation(id: string): Promise<EndResponse> {
  return fetchApi<EndResponse>(`/api/negotiations/${id}/end`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
  })
}

export function resetNegotiation(id: string): Promise<ResetResponse> {
  return fetchApi<ResetResponse>(`/api/negotiations/${id}/reset`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
  })
}
