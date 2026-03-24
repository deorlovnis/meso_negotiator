import { Lock } from 'lucide-react'
import { useState } from 'react'
import type { Card, OffersResponse, TermType } from '../types'
import { CompareOffersModal } from './CompareOffersModal'
import { OfferCard } from './OfferCard'

interface OffersPhaseProps {
  data: OffersResponse
  isActing: boolean
  onAgree: (card: Card) => void
  onFallback: (card: Card) => void
  onImprove: (improveTerm: TermType, tradeTerm: TermType | null) => void
  onEndNegotiation: () => void
  onCompareAgree: (index: number) => void
}

export function OffersPhase({
  data,
  isActing,
  onAgree,
  onFallback,
  onImprove,
  onEndNegotiation,
  onCompareAgree,
}: OffersPhaseProps) {
  const [showCompare, setShowCompare] = useState(false)

  const showImproveAction = data.actions_available.includes('improve')
  const showSecureAction = data.actions_available.includes('secure')

  return (
    <div className="min-h-screen bg-[#F8FAFC] flex flex-col items-center justify-center py-16 px-4 sm:px-6 lg:px-8 font-sans text-slate-900 overflow-x-hidden">
      <div className="w-full max-w-[1150px] mx-auto">
        {/* Banner */}
        <div className="text-center mb-16">
          <div className="inline-flex items-center justify-center px-4 py-2 rounded-full bg-[#f6f4f2] border border-[#a59080]/20 text-[#8f7d6f] text-xs font-bold uppercase tracking-wider mb-6 shadow-sm">
            <div className="w-2 h-2 rounded-full bg-[#a59080] mr-2" />
            {data.banner || 'Offers updated based on your preferences'}
          </div>
        </div>

        {/* Cards */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 lg:gap-8 items-stretch">
          {data.cards.map((card) => (
            <div key={card.label} className="h-full">
              <OfferCard
                cardLabel={card.label}
                recommended={card.recommended}
                terms={card.terms}
                signals={card.signals}
                disabled={isActing}
                canSecure={data.can_secure}
                showImprove={showImproveAction}
                showSecure={showSecureAction}
                onAgree={() => onAgree(card)}
                onSecure={() => onFallback(card)}
                onImprove={onImprove}
              />
            </div>
          ))}
        </div>
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

      {/* Secured Offers floating pill */}
      {data.secured_offers.length > 0 && (
        <div className="fixed bottom-6 right-6 z-50 group">
          <button
            type="button"
            onClick={() => setShowCompare(true)}
            className="flex items-center gap-2.5 bg-slate-900 hover:bg-slate-800 text-white px-5 py-3 rounded-full shadow-[0_8px_30px_rgba(0,0,0,0.2)] transition-all hover:scale-105 active:scale-95"
          >
            <Lock className="w-4 h-4 text-[#10B981]" />
            <span className="text-sm font-bold tracking-wide">
              Secured Offers ({data.secured_offers.length})
            </span>
          </button>
          {/* Tooltip */}
          <div className="absolute -top-12 right-0 bg-slate-800 text-white text-xs font-semibold px-3 py-1.5 rounded-lg opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap shadow-lg">
            {data.secured_offers.length >= 3 ? 'Max reached' : 'Compare with current round'}
            <div className="absolute -bottom-1 right-8 w-2 h-2 bg-slate-800 rotate-45" />
          </div>
        </div>
      )}

      {/* Compare Offers Modal */}
      {showCompare && (
        <CompareOffersModal
          securedOffers={data.secured_offers}
          onAgree={(index) => {
            setShowCompare(false)
            onCompareAgree(index)
          }}
          onClose={() => setShowCompare(false)}
        />
      )}
    </div>
  )
}
