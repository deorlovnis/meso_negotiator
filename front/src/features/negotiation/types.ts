export type CardLabel = 'BEST_PRICE' | 'MOST_BALANCED' | 'FASTEST_PAYMENT'
export type TermType = 'price' | 'delivery' | 'payment' | 'contract'
export type IndicatorState = 'better' | 'neutral' | 'worse'

export interface Terms {
  price: string
  delivery: string
  payment: string
  contract: string
}

export interface Signals {
  price: IndicatorState
  delivery: IndicatorState
  payment: IndicatorState
  contract: IndicatorState
}

export interface Card {
  label: string
  recommended: boolean
  terms: Terms
  signals: Signals
}

export interface SecuredOffer {
  rank: number
  label: string
  terms: Terms
  round_secured: number
}

export interface OffersResponse {
  banner: string
  is_final_round: boolean
  is_first_visit: boolean
  cards: Card[]
  secured_offers: SecuredOffer[]
  can_secure: boolean
  actions_available: string[]
}

export interface AgreeResponse {
  status: string
  agreed_terms: Terms
}

export interface EndResponse {
  status: string
}

export interface ResetResponse {
  status: string
}
