import { useEffect, useReducer } from 'react'
import * as api from './api'
import { ApiError } from './api'
import { OfferCard } from './components/OfferCard'
import type { Card, CardLabel, OffersResponse, Terms } from './types'

// ---------------------------------------------------------------------------
// State machine
// ---------------------------------------------------------------------------

type NegotiationView =
  | { phase: 'loading' }
  | { phase: 'offers'; data: OffersResponse }
  | { phase: 'acting'; data: OffersResponse; pendingAction: string }
  | { phase: 'agreed'; terms: Terms }
  | { phase: 'no_deal' }
  | { phase: 'error'; message: string }

type Action =
  | { type: 'OFFERS_LOADED'; data: OffersResponse }
  | { type: 'ACTION_START'; data: OffersResponse; pendingAction: string }
  | { type: 'OFFERS_UPDATED'; data: OffersResponse }
  | { type: 'AGREED'; terms: Terms }
  | { type: 'NO_DEAL' }
  | { type: 'ERROR'; message: string }

function reducer(_state: NegotiationView, action: Action): NegotiationView {
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

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const NEGOTIATION_ID = 'demo'

const LABEL_DISPLAY_TO_ENUM: Record<string, CardLabel> = {
  'BEST PRICE': 'BEST_PRICE',
  'MOST BALANCED': 'MOST_BALANCED',
  'FASTEST PAYMENT': 'FASTEST_PAYMENT',
}

const LABEL_ICON: Record<string, string> = {
  'BEST PRICE': '💰',
  'MOST BALANCED': '⚖️',
  'FASTEST PAYMENT': '⚡',
}

function toTitleCase(s: string): string {
  return s
    .split(' ')
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1).toLowerCase())
    .join(' ')
}

function toLabelEnum(displayLabel: string): CardLabel {
  const key = displayLabel.toUpperCase()
  const result = LABEL_DISPLAY_TO_ENUM[key]
  if (!result) {
    throw new Error(`Unknown card label: ${displayLabel}`)
  }
  return result
}

function cardToProps(card: Card) {
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

function errorMessage(err: unknown): string {
  if (err instanceof ApiError) {
    if (typeof err.detail === 'object' && err.detail !== null && 'error' in err.detail) {
      return String((err.detail as { error: unknown }).error)
    }
    return `Request failed (${err.status})`
  }
  if (err instanceof Error) return err.message
  return 'An unexpected error occurred'
}

// ---------------------------------------------------------------------------
// App
// ---------------------------------------------------------------------------

export default function App() {
  const [view, dispatch] = useReducer(reducer, { phase: 'loading' })

  useEffect(() => {
    api
      .getOffers(NEGOTIATION_ID)
      .then((data) => dispatch({ type: 'OFFERS_LOADED', data }))
      .catch((err: unknown) => dispatch({ type: 'ERROR', message: errorMessage(err) }))
  }, [])

  function handleAgree(card: Card) {
    if (view.phase !== 'offers') return
    const currentData = view.data
    dispatch({ type: 'ACTION_START', data: currentData, pendingAction: 'agree' })
    api
      .agree(NEGOTIATION_ID, toLabelEnum(card.label))
      .then((res) => dispatch({ type: 'AGREED', terms: res.agreed_terms }))
      .catch((err: unknown) => dispatch({ type: 'ERROR', message: errorMessage(err) }))
  }

  function handleFallback(card: Card) {
    if (view.phase !== 'offers') return
    const currentData = view.data
    dispatch({ type: 'ACTION_START', data: currentData, pendingAction: 'secure' })
    api
      .secure(NEGOTIATION_ID, toLabelEnum(card.label))
      .then(() => api.getOffers(NEGOTIATION_ID))
      .then((data) => dispatch({ type: 'OFFERS_UPDATED', data }))
      .catch((err: unknown) => dispatch({ type: 'ERROR', message: errorMessage(err) }))
  }

  function handleImprove(card: Card) {
    if (view.phase !== 'offers') return
    const currentData = view.data
    dispatch({ type: 'ACTION_START', data: currentData, pendingAction: 'improve' })
    api
      .improve(NEGOTIATION_ID, toLabelEnum(card.label))
      .then((data) => dispatch({ type: 'OFFERS_UPDATED', data }))
      .catch((err: unknown) => dispatch({ type: 'ERROR', message: errorMessage(err) }))
  }

  function handleEndNegotiation() {
    if (view.phase !== 'offers') return
    const currentData = view.data
    dispatch({ type: 'ACTION_START', data: currentData, pendingAction: 'end' })
    api
      .endNegotiation(NEGOTIATION_ID)
      .then(() => dispatch({ type: 'NO_DEAL' }))
      .catch((err: unknown) => dispatch({ type: 'ERROR', message: errorMessage(err) }))
  }

  function handleReset() {
    api
      .resetNegotiation(NEGOTIATION_ID)
      .then(() => api.getOffers(NEGOTIATION_ID))
      .then((data) => dispatch({ type: 'OFFERS_LOADED', data }))
      .catch((err: unknown) => dispatch({ type: 'ERROR', message: errorMessage(err) }))
  }

  // -------------------------------------------------------------------------
  // Phase: loading
  // -------------------------------------------------------------------------
  if (view.phase === 'loading') {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gray-50/80">
        <p className="text-sm font-medium text-gray-500">Loading offers…</p>
      </div>
    )
  }

  // -------------------------------------------------------------------------
  // Phase: agreed
  // -------------------------------------------------------------------------
  if (view.phase === 'agreed') {
    const { terms } = view
    return (
      <div className="flex min-h-screen flex-col items-center justify-center bg-gray-50/80 px-4">
        <div className="w-full max-w-sm rounded-2xl border border-emerald-200 bg-white p-8 shadow-lg">
          <h1 className="mb-1 text-xl font-bold text-gray-900">Deal agreed</h1>
          <p className="mb-6 text-sm text-gray-500">Here are the agreed terms.</p>
          <dl className="flex flex-col gap-3">
            {(
              [
                ['Price', terms.price],
                ['Delivery', terms.delivery],
                ['Payment', terms.payment],
                ['Contract', terms.contract],
              ] as [string, string][]
            ).map(([label, value]) => (
              <div key={label} className="flex items-center justify-between">
                <dt className="text-xs font-semibold uppercase tracking-widest text-gray-400">
                  {label}
                </dt>
                <dd className="text-sm font-bold text-gray-900">{value}</dd>
              </div>
            ))}
          </dl>
          <button
            type="button"
            onClick={handleReset}
            className="mt-6 w-full rounded-xl border border-gray-200 bg-white px-4 py-2.5 text-sm font-medium text-gray-600 transition hover:bg-gray-50"
          >
            Reset demo
          </button>
        </div>
      </div>
    )
  }

  // -------------------------------------------------------------------------
  // Phase: no_deal
  // -------------------------------------------------------------------------
  if (view.phase === 'no_deal') {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center bg-gray-50/80 px-4">
        <div className="w-full max-w-sm rounded-2xl border border-gray-200 bg-white p-8 shadow-sm">
          <h1 className="mb-1 text-xl font-bold text-gray-900">Negotiation ended</h1>
          <p className="mb-6 text-sm text-gray-500">No deal was reached.</p>
          <button
            type="button"
            onClick={handleReset}
            className="w-full rounded-xl border border-gray-200 bg-white px-4 py-2.5 text-sm font-medium text-gray-600 transition hover:bg-gray-50"
          >
            Reset demo
          </button>
        </div>
      </div>
    )
  }

  // -------------------------------------------------------------------------
  // Phase: error
  // -------------------------------------------------------------------------
  if (view.phase === 'error') {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center bg-gray-50/80 px-4">
        <div className="w-full max-w-sm rounded-2xl border border-red-200 bg-white p-8 shadow-sm">
          <h1 className="mb-1 text-xl font-bold text-gray-900">Something went wrong</h1>
          <p className="mb-6 text-sm text-gray-500">{view.message}</p>
          <div className="flex gap-3">
            <button
              type="button"
              onClick={() => {
                api
                  .getOffers(NEGOTIATION_ID)
                  .then((data) => dispatch({ type: 'OFFERS_LOADED', data }))
                  .catch((err: unknown) => dispatch({ type: 'ERROR', message: errorMessage(err) }))
              }}
              className="rounded-xl bg-gray-900 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-gray-700"
            >
              Retry
            </button>
            <button
              type="button"
              onClick={handleReset}
              className="rounded-xl border border-gray-200 bg-white px-4 py-2.5 text-sm font-medium text-gray-600 transition hover:bg-gray-50"
            >
              Reset demo
            </button>
          </div>
        </div>
      </div>
    )
  }

  // -------------------------------------------------------------------------
  // Phase: offers / acting
  // -------------------------------------------------------------------------
  const { data } = view
  const isActing = view.phase === 'acting'
  const showImprove = data.actions_available.includes('improve')

  return (
    <div className="flex min-h-screen flex-col items-center bg-gray-50/80 px-4 py-12">
      {/* Status badge */}
      <div className="mb-4 inline-flex items-center gap-1.5 rounded-full border border-emerald-200 bg-emerald-50 px-4 py-1.5">
        <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
        <span className="text-[11px] font-semibold uppercase tracking-widest text-emerald-700">
          {data.banner}
        </span>
      </div>

      {/* Heading */}
      <h1 className="mb-2 text-3xl font-bold tracking-tight text-gray-900">
        Review your negotiated offers
      </h1>

      {/* Secured offer indicator */}
      {data.secured_offer && (
        <p className="mb-6 text-sm text-gray-500">
          Fallback secured:{' '}
          <span className="font-semibold text-gray-700">
            {toTitleCase(data.secured_offer.label)} — {data.secured_offer.terms.price}
          </span>
        </p>
      )}
      {!data.secured_offer && <div className="mb-6" />}

      {/* Cards */}
      <div className="grid w-full max-w-4xl grid-cols-1 items-start gap-6 md:grid-cols-3">
        {data.cards.map((card) => {
          const props = cardToProps(card)
          return (
            <OfferCard
              key={card.label}
              title={props.title}
              titleIcon={props.titleIcon}
              badge={props.badge}
              recommended={props.recommended}
              details={props.details}
              disabled={isActing}
              onAgree={() => handleAgree(card)}
              onFallback={() => handleFallback(card)}
              onImprove={showImprove ? () => handleImprove(card) : () => {}}
            />
          )
        })}
      </div>

      {/* Final round: end negotiation */}
      {data.is_final_round && (
        <div className="mt-10">
          <button
            type="button"
            onClick={handleEndNegotiation}
            disabled={isActing}
            className="rounded-xl border border-gray-300 bg-white px-6 py-2.5 text-sm font-medium text-gray-600 transition hover:bg-gray-50 disabled:pointer-events-none disabled:opacity-50"
          >
            End negotiation
          </button>
        </div>
      )}
    </div>
  )
}
