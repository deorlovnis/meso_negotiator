import { StatusBadge } from '../../../shared/components/StatusBadge'
import { cardToProps, toTitleCase } from '../lib/format'
import type { Card, OffersResponse } from '../types'
import { OfferCard } from './OfferCard'

interface OffersPhaseProps {
  data: OffersResponse
  isActing: boolean
  onAgree: (card: Card) => void
  onFallback: (card: Card) => void
  onImprove: (card: Card) => void
  onEndNegotiation: () => void
}

export function OffersPhase({
  data,
  isActing,
  onAgree,
  onFallback,
  onImprove,
  onEndNegotiation,
}: OffersPhaseProps) {
  const showImprove = data.actions_available.includes('improve')

  return (
    <div className="flex min-h-screen flex-col items-center bg-gray-50/80 px-4 py-12">
      <StatusBadge text={data.banner} />

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
              onAgree={() => onAgree(card)}
              onFallback={() => onFallback(card)}
              onImprove={showImprove ? () => onImprove(card) : () => {}}
            />
          )
        })}
      </div>

      {/* Final round: end negotiation */}
      {data.is_final_round && (
        <div className="mt-10">
          <button
            type="button"
            onClick={onEndNegotiation}
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
