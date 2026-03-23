import { ApiError } from '../api/negotiation-api'
import { LABEL_DISPLAY_TO_ENUM, LABEL_ICON } from '../constants'
import type { Card, CardLabel, OfferDetail } from '../types'

export function toTitleCase(s: string): string {
  return s
    .split(' ')
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1).toLowerCase())
    .join(' ')
}

export function toLabelEnum(displayLabel: string): CardLabel {
  const key = displayLabel.toUpperCase()
  const result = LABEL_DISPLAY_TO_ENUM[key]
  if (!result) {
    throw new Error(`Unknown card label: ${displayLabel}`)
  }
  return result
}

export function cardToProps(card: Card): {
  title: string
  titleIcon: string
  badge: string | undefined
  recommended: boolean
  details: OfferDetail[]
} {
  const displayLabel = card.label.toUpperCase()
  return {
    title: toTitleCase(displayLabel),
    titleIcon: LABEL_ICON[displayLabel] ?? '📋',
    badge: card.recommended ? 'Recommended' : undefined,
    recommended: card.recommended,
    details: [
      { label: 'Price (per unit)', value: card.terms.price, signal: card.signals.price },
      { label: 'Delivery Time', value: card.terms.delivery, signal: card.signals.delivery },
      { label: 'Payment Terms', value: card.terms.payment, signal: card.signals.payment },
      { label: 'Contract Length', value: card.terms.contract, signal: card.signals.contract },
    ],
  }
}

export function errorMessage(err: unknown): string {
  if (err instanceof ApiError) {
    if (typeof err.detail === 'object' && err.detail !== null && 'error' in err.detail) {
      return String((err.detail as { error: unknown }).error)
    }
    return `Request failed (${err.status})`
  }
  if (err instanceof Error) return err.message
  return 'An unexpected error occurred'
}
