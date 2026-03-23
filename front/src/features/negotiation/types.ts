export type CardLabel = 'BEST_PRICE' | 'MOST_BALANCED' | 'FASTEST_PAYMENT'
export type Signal = 'good' | 'neutral' | 'weak'

export interface Terms {
  price: string
  delivery: string
  payment: string
  contract: string
}

export interface Signals {
  price: Signal
  delivery: Signal
  payment: Signal
  contract: Signal
}

export interface Card {
  label: string
  recommended: boolean
  terms: Terms
  signals: Signals
}

export interface SecuredOffer {
  label: string
  terms: Terms
}

export interface OffersResponse {
  banner: string
  is_final_round: boolean
  is_first_visit: boolean
  cards: Card[]
  secured_offer: SecuredOffer | null
  actions_available: string[]
}

export interface AgreeResponse {
  status: string
  agreed_terms: Terms
}

export interface SecureResponse {
  secured_offer: SecuredOffer
}

export interface EndResponse {
  status: string
}

export interface ResetResponse {
  status: string
}

export interface OfferDetail {
  label: string
  value: string
  signal: Signal
}
