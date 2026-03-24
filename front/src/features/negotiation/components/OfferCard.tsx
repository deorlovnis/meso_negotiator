import {
  ArrowDown,
  ArrowRightLeft,
  ArrowUp,
  Check,
  CircleDollarSign,
  CreditCard,
  DollarSign,
  Download,
  FileText,
  Handshake,
  Lock,
  Minus,
  MousePointerClick,
  Scale,
  Sparkles,
  Truck,
  Zap,
} from 'lucide-react'
import { useState } from 'react'
import type { IndicatorState, Signals, Terms, TermType } from '../types'

interface TermRow {
  type: TermType
  label: string
  value: string
  indicator: IndicatorState
}

interface OfferCardProps {
  cardLabel: string
  recommended?: boolean
  terms: Terms
  signals: Signals
  disabled?: boolean
  canSecure?: boolean
  isSecured?: boolean
  showImprove?: boolean
  showSecure?: boolean
  isAgreedView?: boolean
  onAgree: () => void
  onSecure: () => void
  onImprove: (improveTerm: TermType, tradeTerm: TermType | null) => void
}

function termIcon(type: TermType, isHighlight: boolean) {
  const cls = `w-4 h-4 ${isHighlight ? 'text-[#10B981]' : 'text-slate-400'}`
  switch (type) {
    case 'price':
      return <DollarSign className={cls} />
    case 'delivery':
      return <Truck className={cls} />
    case 'payment':
      return <CreditCard className={cls} />
    case 'contract':
      return <FileText className={cls} />
  }
}

function badgeIcon(label: string) {
  const cls = 'w-3.5 h-3.5 mr-1.5'
  const normalized = label.replace(/_/g, ' ').toUpperCase()
  if (normalized.includes('BEST') || normalized.includes('PRICE'))
    return <CircleDollarSign className={cls} />
  if (normalized.includes('BALANCED')) return <Scale className={cls} />
  if (normalized.includes('FASTEST') || normalized.includes('PAYMENT'))
    return <Zap className={cls} />
  return <Lock className={cls} />
}

function indicator(state: IndicatorState) {
  if (state === 'better') return <ArrowUp className="w-4 h-4 text-[#10B981]" strokeWidth={3} />
  if (state === 'worse') return <ArrowDown className="w-4 h-4 text-amber-500" strokeWidth={3} />
  return <Minus className="w-4 h-4 text-slate-300" strokeWidth={3} />
}

function toDisplayLabel(label: string): string {
  return label.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())
}

function buildTermRows(terms: Terms, signals: Signals): TermRow[] {
  return [
    { type: 'price', label: 'Price (Per Unit)', value: terms.price, indicator: signals.price },
    {
      type: 'delivery',
      label: 'Delivery Time',
      value: terms.delivery,
      indicator: signals.delivery,
    },
    { type: 'payment', label: 'Payment Terms', value: terms.payment, indicator: signals.payment },
    {
      type: 'contract',
      label: 'Contract Length',
      value: terms.contract,
      indicator: signals.contract,
    },
  ]
}

// biome-ignore lint/complexity/noExcessiveCognitiveComplexity: 3-view card is inherently complex
export function OfferCard({
  cardLabel,
  recommended = false,
  terms,
  signals,
  disabled = false,
  canSecure = true,
  isSecured = false,
  showImprove = true,
  showSecure = true,
  isAgreedView = false,
  onAgree,
  onSecure,
  onImprove,
}: OfferCardProps) {
  const [view, setView] = useState<'default' | 'select' | 'trade'>('default')
  const [improvingTerm, setImprovingTerm] = useState<TermRow | null>(null)

  const allTermRows = buildTermRows(terms, signals)
  const displayedTerms =
    view === 'trade' && improvingTerm
      ? allTermRows.filter((t) => t.type !== improvingTerm.type)
      : allTermRows

  const isInteractive = view === 'select' || view === 'trade'
  const displayLabel = toDisplayLabel(cardLabel)

  return (
    <div
      className={`relative flex flex-col w-full rounded-2xl bg-white border overflow-hidden transition-all duration-300 ${
        recommended
          ? 'border-[#a59080]/40 shadow-[0_8px_30px_rgba(165,144,128,0.18)] z-10'
          : 'border-slate-200 shadow-sm hover:shadow-md'
      }`}
    >
      {recommended && <div className="absolute top-0 left-0 right-0 h-1.5 bg-[#a59080] z-20" />}

      <div className="flex flex-col flex-grow p-6 lg:p-7 relative overflow-hidden">
        {/* Header */}
        <div className="flex justify-between items-center mb-6">
          <span
            className={`inline-flex items-center text-xs font-bold uppercase tracking-wider px-3.5 py-1.5 rounded-full border shadow-sm ${
              recommended
                ? 'bg-[#fcfafa] text-[#5c4d41] border-[#a59080]/30'
                : 'bg-slate-50 text-slate-700 border-slate-200'
            }`}
          >
            {badgeIcon(cardLabel)}
            {displayLabel}
          </span>
          {recommended && (
            <span className="flex items-center text-xs font-bold text-[#a59080] bg-[#fcfafa] border border-[#a59080]/20 px-2.5 py-1 rounded-md shadow-sm">
              <Sparkles className="w-3.5 h-3.5 mr-1.5 fill-current" />
              Recommended
            </span>
          )}
        </div>

        {/* Term rows */}
        <div className="space-y-3 mb-6 flex-grow">
          {/* biome-ignore lint/complexity/noExcessiveCognitiveComplexity: term row with interactive states */}
          {displayedTerms.map((term) => {
            const isHighlight = term.indicator === 'better'
            return (
              <button
                type="button"
                key={term.type}
                onClick={() => {
                  if (view === 'select') {
                    setImprovingTerm(term)
                    setView('trade')
                  } else if (view === 'trade') {
                    onImprove(improvingTerm?.type, term.type)
                    setView('default')
                    setImprovingTerm(null)
                  }
                }}
                className={`relative flex items-center justify-between p-3.5 rounded-xl transition-all duration-300 w-full text-left ${
                  isInteractive ? 'cursor-pointer group' : ''
                } ${
                  !isInteractive && isHighlight
                    ? 'bg-slate-50 border border-slate-100'
                    : 'border border-transparent'
                }`}
              >
                {isInteractive && (
                  <div className="absolute inset-0 border-2 border-[#a59080]/40 bg-[#f6f4f2]/60 rounded-xl opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-0" />
                )}

                <div className="flex items-center gap-3.5 relative z-10">
                  <div
                    className={`p-2 rounded-lg transition-colors ${
                      isInteractive ? 'group-hover:bg-white group-hover:shadow-sm' : ''
                    } ${isHighlight ? 'bg-[#10B981]/15 shadow-sm' : 'bg-slate-50'}`}
                  >
                    {termIcon(term.type, isHighlight)}
                  </div>
                  <div>
                    <div className="text-[11px] text-slate-500 font-medium uppercase tracking-wide mb-0.5">
                      {term.label}
                    </div>
                    <div
                      className={`text-sm font-bold transition-colors ${
                        isHighlight || isInteractive ? 'text-slate-900' : 'text-slate-700'
                      }`}
                    >
                      {term.value}
                    </div>
                  </div>
                </div>

                <div className="relative z-10 flex items-center justify-end h-8 min-w-[100px]">
                  <div
                    className={`transition-opacity duration-300 absolute right-0 flex justify-end ${
                      isInteractive ? 'group-hover:opacity-0' : ''
                    }`}
                  >
                    {indicator(term.indicator)}
                  </div>

                  {view === 'select' && (
                    <div className="absolute right-0 flex items-center opacity-0 group-hover:opacity-100 group-hover:translate-x-0 translate-x-4 transition-all duration-300 pointer-events-none">
                      <div className="flex items-center gap-1.5 text-[11px] font-bold text-white bg-[#a59080] px-3 py-1.5 rounded-md shadow-md">
                        Improve
                        <ArrowUp className="w-3.5 h-3.5" strokeWidth={3} />
                      </div>
                    </div>
                  )}

                  {view === 'trade' && (
                    <div className="absolute right-0 flex items-center opacity-0 group-hover:opacity-100 group-hover:translate-x-0 translate-x-4 transition-all duration-300 pointer-events-none">
                      <div className="flex items-center gap-1.5 text-[11px] font-bold text-white bg-[#a59080] px-3 py-1.5 rounded-md shadow-md">
                        Trade
                        <ArrowDown className="w-3.5 h-3.5" strokeWidth={3} />
                      </div>
                    </div>
                  )}
                </div>
              </button>
            )
          })}
        </div>

        {/* Actions area */}
        <div className="mt-auto pt-5 border-t border-slate-100 flex flex-col justify-end min-h-[175px]">
          {isAgreedView ? (
            <div className="flex flex-col items-center justify-center h-full w-full mt-2">
              <button
                type="button"
                className="w-full py-4 px-4 font-bold text-[15px] rounded-xl bg-[#10B981] text-white shadow-md shadow-[#10B981]/20 hover:bg-[#0e9f6e] flex items-center justify-center gap-2 transition-all"
              >
                <Download className="w-5 h-5" />
                Download Contract PDF
              </button>
            </div>
          ) : view === 'default' ? (
            <div className="flex flex-col items-center">
              <button
                type="button"
                onClick={onAgree}
                disabled={disabled}
                className="w-full relative overflow-hidden py-3.5 px-4 font-bold text-[15px] rounded-xl bg-[#4C6B56] text-white shadow-md shadow-[#4C6B56]/20 hover:shadow-[0_8px_25px_rgba(90,125,101,0.4)] hover:bg-[#5A7D65] mb-3 disabled:opacity-50 disabled:pointer-events-none transition-all group"
              >
                <span className="relative z-10 flex items-center justify-center gap-2">
                  <Handshake className="w-[18px] h-[18px]" strokeWidth={2.5} />
                  Agree
                </span>
              </button>

              {showSecure &&
                (isSecured ? (
                  <button
                    type="button"
                    disabled
                    className="w-full py-2.5 px-4 bg-slate-50 border border-slate-200 text-[#10B981] font-bold text-[13px] rounded-xl shadow-sm mb-4 flex items-center justify-center gap-2 cursor-not-allowed"
                  >
                    <Check className="w-4 h-4 text-[#10B981]" strokeWidth={3} />
                    Secured
                  </button>
                ) : (
                  <button
                    type="button"
                    onClick={onSecure}
                    disabled={disabled || !canSecure}
                    className={`w-full py-2.5 px-4 bg-white border border-[#a59080] text-[#a59080] font-semibold text-[13px] rounded-xl hover:bg-[#a59080] hover:text-white transition-colors shadow-sm mb-4 flex items-center justify-center gap-2 group ${
                      !canSecure
                        ? 'opacity-50 cursor-not-allowed hover:bg-white hover:text-[#a59080]'
                        : ''
                    } disabled:opacity-50 disabled:pointer-events-none`}
                  >
                    <Lock className="w-4 h-4 text-[#a59080] group-hover:text-white transition-colors" />
                    Secure as fallback
                  </button>
                ))}

              {showImprove && (
                <button
                  type="button"
                  onClick={() => setView('select')}
                  disabled={disabled}
                  className="text-xs font-semibold text-slate-400 hover:text-slate-700 transition-colors underline underline-offset-4 decoration-slate-300 hover:decoration-slate-400 disabled:opacity-50 disabled:pointer-events-none"
                >
                  Improve terms
                </button>
              )}
            </div>
          ) : view === 'select' ? (
            <div className="h-full w-full flex flex-col items-center justify-center bg-[#f6f4f2]/80 border border-[#a59080]/20 rounded-xl p-5 text-center">
              <div className="w-8 h-8 rounded-full bg-white flex items-center justify-center text-[#a59080] mb-3 shadow-sm">
                <MousePointerClick className="w-4 h-4" />
              </div>
              <h4 className="text-[15px] font-bold text-slate-900 mb-1">What to improve?</h4>
              <p className="text-[13px] text-slate-500 mb-4">Select a term above to negotiate</p>
              <button
                type="button"
                onClick={() => setView('default')}
                className="text-xs font-bold text-[#a59080] hover:text-[#8f7d6f] transition-colors uppercase tracking-wider py-1 px-3 border border-[#a59080]/20 rounded-lg hover:bg-[#a59080]/5"
              >
                Cancel
              </button>
            </div>
          ) : (
            <div className="h-full w-full flex flex-col items-center justify-center bg-slate-50 border border-slate-200 rounded-xl p-4 text-center">
              <div className="w-8 h-8 rounded-full bg-white flex items-center justify-center text-[#a59080] mb-2 shadow-sm border border-slate-100">
                <ArrowRightLeft className="w-4 h-4" />
              </div>
              <h4 className="text-[14px] font-bold text-slate-900 mb-1 leading-snug">
                To improve{' '}
                <span className="text-[#a59080]">{improvingTerm?.label.toLowerCase()}</span>,
              </h4>
              <p className="text-[12px] text-slate-500 mb-4">what would you trade from above?</p>

              <button
                type="button"
                onClick={() => {
                  onImprove(improvingTerm?.type, null)
                  setView('default')
                  setImprovingTerm(null)
                }}
                className="w-full py-2.5 px-4 bg-white border border-[#a59080] text-[#a59080] font-semibold text-[13px] rounded-xl hover:bg-[#a59080] hover:text-white transition-colors shadow-sm mb-3 flex items-center justify-center gap-2 group"
              >
                <Scale className="w-4 h-4 text-[#a59080] group-hover:text-white transition-colors" />
                Balance other terms
              </button>

              <div className="flex gap-4">
                <button
                  type="button"
                  onClick={() => {
                    setView('select')
                    setImprovingTerm(null)
                  }}
                  className="text-[11px] font-bold text-slate-400 hover:text-slate-600 transition-colors uppercase tracking-wider py-1"
                >
                  Back
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setView('default')
                    setImprovingTerm(null)
                  }}
                  className="text-[11px] font-bold text-slate-400 hover:text-slate-600 transition-colors uppercase tracking-wider py-1"
                >
                  Cancel
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
