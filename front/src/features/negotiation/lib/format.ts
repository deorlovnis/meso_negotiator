import { ApiError } from '../api/negotiation-api'
import { LABEL_DISPLAY_TO_ENUM } from '../constants'
import type { CardLabel } from '../types'

export function toTitleCase(s: string): string {
  return s
    .split(' ')
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1).toLowerCase())
    .join(' ')
}

export function toLabelEnum(displayLabel: string): CardLabel {
  const key = displayLabel.replace(/_/g, ' ').toUpperCase()
  const result = LABEL_DISPLAY_TO_ENUM[key]
  if (!result) {
    throw new Error(`Unknown card label: ${displayLabel}`)
  }
  return result
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
