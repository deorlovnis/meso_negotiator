import type { OffersResponse, Terms } from '../types'

export type NegotiationView =
  | { phase: 'loading' }
  | { phase: 'offers'; data: OffersResponse }
  | { phase: 'acting'; data: OffersResponse; pendingAction: string }
  | { phase: 'agreed'; terms: Terms }
  | { phase: 'no_deal' }
  | { phase: 'error'; message: string }

export type Action =
  | { type: 'OFFERS_LOADED'; data: OffersResponse }
  | { type: 'ACTION_START'; data: OffersResponse; pendingAction: string }
  | { type: 'OFFERS_UPDATED'; data: OffersResponse }
  | { type: 'AGREED'; terms: Terms }
  | { type: 'NO_DEAL' }
  | { type: 'ERROR'; message: string }

export function reducer(_state: NegotiationView, action: Action): NegotiationView {
  switch (action.type) {
    case 'OFFERS_LOADED':
    case 'OFFERS_UPDATED':
      return { phase: 'offers', data: action.data }
    case 'ACTION_START':
      return { phase: 'acting', data: action.data, pendingAction: action.pendingAction }
    case 'AGREED':
      return { phase: 'agreed', terms: action.terms }
    case 'NO_DEAL':
      return { phase: 'no_deal' }
    case 'ERROR':
      return { phase: 'error', message: action.message }
  }
}
