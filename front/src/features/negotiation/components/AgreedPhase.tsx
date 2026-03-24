import {
  ArrowUp,
  CreditCard,
  DollarSign,
  Download,
  FileText,
  Scale,
  Sparkles,
  Truck,
} from 'lucide-react'
import type { Terms } from '../types'

interface AgreedPhaseProps {
  terms: Terms
  cardLabel?: string
  onReset: () => void
}

function termIcon(type: string) {
  const cls = 'w-4 h-4 text-slate-400'
  switch (type) {
    case 'price':
      return <DollarSign className={cls} />
    case 'delivery':
      return <Truck className={cls} />
    case 'payment':
      return <CreditCard className={cls} />
    case 'contract':
      return <FileText className={cls} />
    default:
      return null
  }
}

const TERM_LABELS: Record<string, string> = {
  price: 'Price (Per Unit)',
  delivery: 'Delivery Time',
  payment: 'Payment Terms',
  contract: 'Contract Length',
}

export function AgreedPhase({ terms, cardLabel, onReset }: AgreedPhaseProps) {
  const displayLabel = cardLabel
    ? cardLabel.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())
    : 'Most Balanced'

  const termEntries = [
    { key: 'price', value: terms.price },
    { key: 'delivery', value: terms.delivery },
    { key: 'payment', value: terms.payment },
    { key: 'contract', value: terms.contract },
  ]

  return (
    <div className="fixed inset-0 z-[100] overflow-y-auto">
      <div className="fixed inset-0 bg-[#353E4C] z-0" />

      <div className="min-h-full w-full flex flex-col items-center p-4 py-12 lg:p-8 relative z-10">
        {/* Title */}
        <div className="text-center mb-8 mt-12">
          <h2 className="text-4xl md:text-[52px] font-black text-white tracking-tight drop-shadow-lg mb-3 flex items-center justify-center gap-3">
            <span className="text-[52px]">🎉</span> Deal Closed!
          </h2>
          <p className="text-xl text-slate-200 font-medium max-w-lg mx-auto">
            You made a win win choice!
          </p>
        </div>

        {/* Card */}
        <div className="w-full max-w-[420px]">
          <div className="relative flex flex-col w-full rounded-2xl bg-white border border-[#a59080]/40 shadow-[0_8px_30px_rgba(165,144,128,0.18)] overflow-hidden">
            <div className="absolute top-0 left-0 right-0 h-1.5 bg-[#a59080] z-20" />

            <div className="flex flex-col flex-grow p-6 lg:p-7">
              {/* Header */}
              <div className="flex justify-between items-center mb-6">
                <span className="inline-flex items-center text-xs font-bold uppercase tracking-wider px-3.5 py-1.5 rounded-full border shadow-sm bg-[#fcfafa] text-[#5c4d41] border-[#a59080]/30">
                  <Scale className="w-3.5 h-3.5 mr-1.5" />
                  {displayLabel}
                </span>
                <span className="flex items-center text-xs font-bold text-[#a59080] bg-[#fcfafa] border border-[#a59080]/20 px-2.5 py-1 rounded-md shadow-sm">
                  <Sparkles className="w-3.5 h-3.5 mr-1.5 fill-current" />
                  Recommended
                </span>
              </div>

              {/* Terms */}
              <div className="space-y-3 mb-6">
                {termEntries.map(({ key, value }) => (
                  <div
                    key={key}
                    className="flex items-center justify-between p-3.5 rounded-xl border border-transparent"
                  >
                    <div className="flex items-center gap-3.5">
                      <div className="p-2 rounded-lg bg-slate-50">{termIcon(key)}</div>
                      <div>
                        <div className="text-[11px] text-slate-500 font-medium uppercase tracking-wide mb-0.5">
                          {TERM_LABELS[key] || key}
                        </div>
                        <div className="text-sm font-bold text-slate-900">{value}</div>
                      </div>
                    </div>
                    <ArrowUp className="w-4 h-4 text-[#10B981]" strokeWidth={3} />
                  </div>
                ))}
              </div>

              {/* Download button */}
              <div className="mt-auto pt-5 border-t border-slate-100">
                <button
                  type="button"
                  className="w-full py-4 px-4 font-bold text-[15px] rounded-xl bg-[#10B981] text-white shadow-md shadow-[#10B981]/20 hover:bg-[#0e9f6e] flex items-center justify-center gap-2 transition-all"
                >
                  <Download className="w-5 h-5" />
                  Download Contract PDF
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Reset */}
        <button
          type="button"
          onClick={onReset}
          className="mt-8 text-sm font-medium text-slate-400 hover:text-white transition-colors underline underline-offset-4"
        >
          Reset demo
        </button>
      </div>
    </div>
  )
}
