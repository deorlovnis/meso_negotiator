import { describe, expect, it } from 'vitest'
import type { OffersResponse, Terms } from '../types'
import type { Action, NegotiationView } from './reducer'
import { reducer } from './reducer'

// ---------------------------------------------------------------------------
// Test data — realistic domain values, not placeholders
// ---------------------------------------------------------------------------

const offersData: OffersResponse = {
  banner: 'Round 2 of 3',
  is_final_round: false,
  is_first_visit: false,
  cards: [
    {
      label: 'BEST PRICE',
      recommended: true,
      terms: { price: '$42/unit', delivery: '14 days', payment: 'Net 30', contract: '12 months' },
      signals: { price: 'good', delivery: 'neutral', payment: 'neutral', contract: 'weak' },
    },
  ],
  secured_offer: null,
  actions_available: ['improve', 'secure'],
}

const altOffersData: OffersResponse = {
  banner: 'Round 3 of 3',
  is_final_round: true,
  is_first_visit: false,
  cards: [],
  secured_offer: {
    label: 'MOST BALANCED',
    terms: { price: '$50/unit', delivery: '7 days', payment: 'Net 15', contract: '6 months' },
  },
  actions_available: [],
}

const agreedTerms: Terms = {
  price: '$45/unit',
  delivery: '10 days',
  payment: 'Net 30',
  contract: '12 months',
}

// Every possible source phase for cross-phase transition tests
const allPhases: Array<{ label: string; state: NegotiationView }> = [
  { label: 'loading', state: { phase: 'loading' } },
  { label: 'offers', state: { phase: 'offers', data: offersData } },
  { label: 'acting', state: { phase: 'acting', data: offersData, pendingAction: 'agree' } },
  { label: 'agreed', state: { phase: 'agreed', terms: agreedTerms } },
  { label: 'no_deal', state: { phase: 'no_deal' } },
  { label: 'error', state: { phase: 'error', message: 'something broke' } },
]

// ---------------------------------------------------------------------------
// A1: OFFERS_LOADED from any state produces {phase: 'offers', data}
// Error category: Logic errors (state transition correctness)
// ---------------------------------------------------------------------------
describe('A1: OFFERS_LOADED from any state produces {phase: "offers", data}', () => {
  for (const { label, state } of allPhases) {
    it(`transitions from "${label}" phase to offers`, () => {
      const action: Action = { type: 'OFFERS_LOADED', data: offersData }
      const next = reducer(state, action)
      expect(next).toEqual({ phase: 'offers', data: offersData })
    })
  }

  // Adversarial: the retry path — OFFERS_LOADED from error is how retry works
  it('retry path: OFFERS_LOADED from error phase restores offers with new data', () => {
    const errorState: NegotiationView = { phase: 'error', message: 'Network timeout' }
    const action: Action = { type: 'OFFERS_LOADED', data: altOffersData }
    const next = reducer(errorState, action)
    expect(next).toEqual({ phase: 'offers', data: altOffersData })
  })
})

// ---------------------------------------------------------------------------
// A2: OFFERS_UPDATED produces same shape as OFFERS_LOADED
// Error category: Logic errors (action aliasing)
// ---------------------------------------------------------------------------
describe('A2: OFFERS_UPDATED produces same shape as OFFERS_LOADED', () => {
  it('produces identical output shape to OFFERS_LOADED for the same data', () => {
    const state: NegotiationView = { phase: 'acting', data: offersData, pendingAction: 'improve' }
    const loaded = reducer(state, { type: 'OFFERS_LOADED', data: altOffersData })
    const updated = reducer(state, { type: 'OFFERS_UPDATED', data: altOffersData })
    expect(updated).toEqual(loaded)
  })

  it('OFFERS_UPDATED replaces the data entirely', () => {
    const state: NegotiationView = { phase: 'offers', data: offersData }
    const next = reducer(state, { type: 'OFFERS_UPDATED', data: altOffersData })
    expect(next).toEqual({ phase: 'offers', data: altOffersData })
    expect(next.data).toBe(altOffersData)
  })
})

// ---------------------------------------------------------------------------
// A3: ACTION_START preserves data and pendingAction
// Error category: Data errors (field preservation)
// ---------------------------------------------------------------------------
describe('A3: ACTION_START preserves data and pendingAction', () => {
  it('transitions to acting phase with data and pendingAction', () => {
    const state: NegotiationView = { phase: 'offers', data: offersData }
    const action: Action = { type: 'ACTION_START', data: offersData, pendingAction: 'agree' }
    const next = reducer(state, action)
    expect(next).toEqual({ phase: 'acting', data: offersData, pendingAction: 'agree' })
  })

  it('preserves the exact data reference', () => {
    const state: NegotiationView = { phase: 'offers', data: offersData }
    const action: Action = { type: 'ACTION_START', data: offersData, pendingAction: 'secure' }
    const next = reducer(state, action)
    expect(next.phase).toBe('acting')
    if (next.phase === 'acting') {
      expect(next.data).toBe(offersData)
    }
  })
})

// ---------------------------------------------------------------------------
// A4: AGREED transitions to {phase: 'agreed', terms}
// Error category: Logic errors (terminal state transition)
// ---------------------------------------------------------------------------
describe('A4: AGREED transitions to {phase: "agreed", terms}', () => {
  it('produces agreed phase with the provided terms', () => {
    const state: NegotiationView = { phase: 'acting', data: offersData, pendingAction: 'agree' }
    const action: Action = { type: 'AGREED', terms: agreedTerms }
    const next = reducer(state, action)
    expect(next).toEqual({ phase: 'agreed', terms: agreedTerms })
  })

  it('carries all four term fields', () => {
    const action: Action = { type: 'AGREED', terms: agreedTerms }
    const next = reducer({ phase: 'offers', data: offersData }, action)
    if (next.phase === 'agreed') {
      expect(next.terms.price).toBe('$45/unit')
      expect(next.terms.delivery).toBe('10 days')
      expect(next.terms.payment).toBe('Net 30')
      expect(next.terms.contract).toBe('12 months')
    } else {
      expect.unreachable('Expected agreed phase')
    }
  })
})

// ---------------------------------------------------------------------------
// A5: NO_DEAL transitions to {phase: 'no_deal'}
// Error category: Logic errors (terminal state transition)
// ---------------------------------------------------------------------------
describe('A5: NO_DEAL transitions to {phase: "no_deal"}', () => {
  it('produces no_deal phase with no extra properties', () => {
    const state: NegotiationView = { phase: 'acting', data: offersData, pendingAction: 'end' }
    const next = reducer(state, { type: 'NO_DEAL' })
    expect(next).toEqual({ phase: 'no_deal' })
  })

  it('result has only the phase property', () => {
    const next = reducer({ phase: 'offers', data: offersData }, { type: 'NO_DEAL' })
    expect(Object.keys(next)).toEqual(['phase'])
  })
})

// ---------------------------------------------------------------------------
// A6: ERROR from any state produces {phase: 'error', message}
// Error category: Logic errors (error recovery transition)
// ---------------------------------------------------------------------------
describe('A6: ERROR from any state produces {phase: "error", message}', () => {
  for (const { label, state } of allPhases) {
    it(`transitions from "${label}" phase to error`, () => {
      const action: Action = { type: 'ERROR', message: 'Server returned 500' }
      const next = reducer(state, action)
      expect(next).toEqual({ phase: 'error', message: 'Server returned 500' })
    })
  }
})

// ---------------------------------------------------------------------------
// A7: Reducer is pure — previous state is never mutated
// Error category: Data errors (immutability)
// ---------------------------------------------------------------------------
describe('A7: Reducer is pure — previous state is never mutated', () => {
  it('OFFERS_LOADED does not mutate the previous state object', () => {
    const prev: NegotiationView = { phase: 'offers', data: offersData }
    const frozen = Object.freeze({ ...prev })
    // Object.freeze would throw on mutation in strict mode
    const next = reducer(frozen as NegotiationView, { type: 'OFFERS_LOADED', data: altOffersData })
    expect(next).not.toBe(frozen)
    expect(frozen.phase).toBe('offers')
  })

  it('ACTION_START does not mutate the previous state object', () => {
    const prev: NegotiationView = { phase: 'offers', data: offersData }
    const snapshot = { ...prev }
    reducer(prev, { type: 'ACTION_START', data: offersData, pendingAction: 'agree' })
    expect(prev).toEqual(snapshot)
  })

  it('ERROR does not mutate the previous state object', () => {
    const prev: NegotiationView = { phase: 'acting', data: offersData, pendingAction: 'secure' }
    const snapshot = JSON.parse(JSON.stringify(prev))
    reducer(prev, { type: 'ERROR', message: 'timeout' })
    expect(prev).toEqual(snapshot)
  })

  it('returns a new object reference on every dispatch', () => {
    const state: NegotiationView = { phase: 'offers', data: offersData }
    const next = reducer(state, { type: 'OFFERS_LOADED', data: offersData })
    expect(next).not.toBe(state)
  })
})

// ---------------------------------------------------------------------------
// A8: pendingAction string preserved verbatim
// Error category: Data errors (string fidelity)
// ---------------------------------------------------------------------------
describe('A8: pendingAction string preserved verbatim', () => {
  const cases = ['agree', 'secure', 'improve', 'end', 'arbitrary_action_name']

  for (const actionName of cases) {
    it(`preserves pendingAction="${actionName}" verbatim`, () => {
      const state: NegotiationView = { phase: 'offers', data: offersData }
      const action: Action = { type: 'ACTION_START', data: offersData, pendingAction: actionName }
      const next = reducer(state, action)
      if (next.phase === 'acting') {
        expect(next.pendingAction).toBe(actionName)
      } else {
        expect.unreachable('Expected acting phase')
      }
    })
  }

  it('preserves empty string as pendingAction', () => {
    const state: NegotiationView = { phase: 'offers', data: offersData }
    const next = reducer(state, { type: 'ACTION_START', data: offersData, pendingAction: '' })
    if (next.phase === 'acting') {
      expect(next.pendingAction).toBe('')
    } else {
      expect.unreachable('Expected acting phase')
    }
  })
})
