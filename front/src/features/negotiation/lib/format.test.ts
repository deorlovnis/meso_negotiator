import { describe, expect, it } from 'vitest'
import { ApiError } from '../api/negotiation-api'
import type { Card } from '../types'
import { cardToProps, errorMessage, toLabelEnum, toTitleCase } from './format'

// ---------------------------------------------------------------------------
// toTitleCase
// ---------------------------------------------------------------------------

describe('toTitleCase', () => {
  // C1: Multi-word uppercase → title case
  // Error category: Computation errors (string transformation)
  it('C1: converts "BEST PRICE" to "Best Price"', () => {
    expect(toTitleCase('BEST PRICE')).toBe('Best Price')
  })

  // C2: Single word uppercase → title case
  // Error category: Input/output errors (boundary — single word)
  it('C2: converts single word "PRICE" to "Price"', () => {
    expect(toTitleCase('PRICE')).toBe('Price')
  })

  // C3: Empty string → empty string
  // Error category: Input/output errors (boundary — empty input)
  it('C3: returns empty string for empty input', () => {
    expect(toTitleCase('')).toBe('')
  })

  // C4: Mixed case → normalized title case
  // Error category: Computation errors (case normalization)
  it('C4: normalizes mixed case "bEsT pRiCe" to "Best Price"', () => {
    expect(toTitleCase('bEsT pRiCe')).toBe('Best Price')
  })
})

// ---------------------------------------------------------------------------
// toLabelEnum
// ---------------------------------------------------------------------------

describe('toLabelEnum', () => {
  // C5: Title-case display label → enum
  // Error category: Logic errors (lookup correctness)
  it('C5: converts "Best Price" to BEST_PRICE enum', () => {
    expect(toLabelEnum('Best Price')).toBe('BEST_PRICE')
  })

  // C6: Already-uppercase display label → enum
  // Error category: Input/output errors (equivalence class — already uppercase)
  it('C6: converts "BEST PRICE" to BEST_PRICE enum', () => {
    expect(toLabelEnum('BEST PRICE')).toBe('BEST_PRICE')
  })

  // C7: Unknown label → throws Error
  // Error category: Input/output errors (invalid input handling)
  it('C7: throws Error for unknown label "UNKNOWN"', () => {
    expect(() => toLabelEnum('UNKNOWN')).toThrow(Error)
    expect(() => toLabelEnum('UNKNOWN')).toThrow('Unknown card label: UNKNOWN')
  })

  // C8: Lowercase display label → enum (case insensitive lookup)
  // Error category: Input/output errors (equivalence class — lowercase)
  it('C8: converts lowercase "best price" to BEST_PRICE enum', () => {
    expect(toLabelEnum('best price')).toBe('BEST_PRICE')
  })

  // Additional: verify all three valid labels map correctly
  it('maps all three valid labels', () => {
    expect(toLabelEnum('Most Balanced')).toBe('MOST_BALANCED')
    expect(toLabelEnum('Fastest Payment')).toBe('FASTEST_PAYMENT')
  })

  // Adversarial: whitespace-only string should throw
  it('throws for whitespace-only input', () => {
    expect(() => toLabelEnum('   ')).toThrow(Error)
  })
})

// ---------------------------------------------------------------------------
// cardToProps
// ---------------------------------------------------------------------------

const makeCard = (overrides: Partial<Card> = {}): Card => ({
  label: 'BEST PRICE',
  recommended: false,
  terms: { price: '$42/unit', delivery: '14 days', payment: 'Net 30', contract: '12 months' },
  signals: { price: 'good', delivery: 'neutral', payment: 'weak', contract: 'good' },
  ...overrides,
})

describe('cardToProps', () => {
  // C9: Maps all 4 terms with correct labels
  // Error category: Interface errors (contract between data and display)
  it('C9: maps all 4 term details with correct labels', () => {
    const card = makeCard()
    const props = cardToProps(card)
    const labels = props.details.map((d) => d.label)
    expect(labels).toEqual([
      'Price (per unit)',
      'Delivery Time',
      'Payment Terms',
      'Contract Length',
    ])
  })

  it('C9: maps term values correctly', () => {
    const card = makeCard()
    const props = cardToProps(card)
    const values = props.details.map((d) => d.value)
    expect(values).toEqual(['$42/unit', '14 days', 'Net 30', '12 months'])
  })

  it('C9: maps signal values correctly', () => {
    const card = makeCard()
    const props = cardToProps(card)
    const signals = props.details.map((d) => d.signal)
    expect(signals).toEqual(['good', 'neutral', 'weak', 'good'])
  })

  // C10: badge is 'Recommended' only when card.recommended === true
  // Error category: Logic errors (conditional mapping)
  it('C10: badge is "Recommended" when card.recommended is true', () => {
    const card = makeCard({ recommended: true })
    const props = cardToProps(card)
    expect(props.badge).toBe('Recommended')
    expect(props.recommended).toBe(true)
  })

  it('C10: badge is undefined when card.recommended is false', () => {
    const card = makeCard({ recommended: false })
    const props = cardToProps(card)
    expect(props.badge).toBeUndefined()
    expect(props.recommended).toBe(false)
  })

  // C11: Unknown label gets fallback icon
  // Error category: Input/output errors (fallback behavior)
  it('C11: uses fallback icon for unknown label', () => {
    const card = makeCard({ label: 'MYSTERY OFFER' })
    const props = cardToProps(card)
    expect(props.titleIcon).toBe('\u{1F4CB}') // clipboard emoji
  })

  // Additional: verify known labels get their specific icons
  it('maps known labels to their specific icons', () => {
    const bestPrice = cardToProps(makeCard({ label: 'BEST PRICE' }))
    expect(bestPrice.titleIcon).toBe('\u{1F4B0}') // money bag

    const balanced = cardToProps(makeCard({ label: 'MOST BALANCED' }))
    expect(balanced.titleIcon).toBe('\u2696\uFE0F') // scales

    const fastest = cardToProps(makeCard({ label: 'FASTEST PAYMENT' }))
    expect(fastest.titleIcon).toBe('\u26A1') // lightning
  })

  // Additional: title is converted to title case
  it('converts label to title case for the title prop', () => {
    const props = cardToProps(makeCard({ label: 'MOST BALANCED' }))
    expect(props.title).toBe('Most Balanced')
  })

  // Adversarial: lowercase label still gets correct icon via toUpperCase
  it('handles lowercase label by uppercasing for icon lookup', () => {
    const card = makeCard({ label: 'best price' })
    const props = cardToProps(card)
    expect(props.titleIcon).toBe('\u{1F4B0}')
  })
})

// ---------------------------------------------------------------------------
// errorMessage
// ---------------------------------------------------------------------------

describe('errorMessage', () => {
  // C12: ApiError with {error: 'terminal'} → extracts error field
  // Error category: Logic errors (error extraction chain)
  it('C12: extracts error field from ApiError detail object', () => {
    const err = new ApiError(409, { error: 'terminal' })
    expect(errorMessage(err)).toBe('terminal')
  })

  // C13: ApiError with string detail → falls back to status message
  // Error category: Logic errors (fallback branch)
  it('C13: falls back to status message when detail is a string', () => {
    const err = new ApiError(409, 'some string')
    expect(errorMessage(err)).toBe('Request failed (409)')
  })

  // C14: plain Error → uses message property
  // Error category: Logic errors (instanceof chain)
  it('C14: uses message from plain Error', () => {
    const err = new Error('Network fail')
    expect(errorMessage(err)).toBe('Network fail')
  })

  // C15: non-Error values → fallback message
  // Error category: Input/output errors (unexpected types)
  it('C15: returns fallback for number', () => {
    expect(errorMessage(42)).toBe('An unexpected error occurred')
  })

  it('C15: returns fallback for null', () => {
    expect(errorMessage(null)).toBe('An unexpected error occurred')
  })

  it('C15: returns fallback for undefined', () => {
    expect(errorMessage(undefined)).toBe('An unexpected error occurred')
  })

  // C16: ApiError with {error: 0} → extracts falsy but present error field
  // Error category: Logic errors (falsy value edge case)
  it('C16: extracts falsy error value 0 via String coercion', () => {
    const err = new ApiError(422, { error: 0 })
    expect(errorMessage(err)).toBe('0')
  })

  // C17: ApiError with null detail → falls back to status message
  // Error category: Logic errors (null detail edge case)
  it('C17: falls back to status message when detail is null', () => {
    const err = new ApiError(500, null)
    expect(errorMessage(err)).toBe('Request failed (500)')
  })

  // Adversarial: ApiError with detail {error: ''} → empty string is truthy for 'in' check
  it('extracts empty string error field', () => {
    const err = new ApiError(400, { error: '' })
    expect(errorMessage(err)).toBe('')
  })

  // Adversarial: ApiError with detail {} (no error key) → status fallback
  it('falls back to status when detail object has no error key', () => {
    const err = new ApiError(422, { message: 'validation failed' })
    expect(errorMessage(err)).toBe('Request failed (422)')
  })

  // Adversarial: ApiError is an instanceof Error — verify it hits ApiError branch first
  it('ApiError is checked before plain Error (instanceof ordering)', () => {
    const err = new ApiError(409, { error: 'conflict' })
    // ApiError extends Error, so both instanceof checks would pass.
    // The function must check ApiError first.
    expect(err instanceof Error).toBe(true)
    expect(err instanceof ApiError).toBe(true)
    expect(errorMessage(err)).toBe('conflict') // not err.message
  })
})
