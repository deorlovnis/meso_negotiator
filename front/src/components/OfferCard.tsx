type Signal = 'good' | 'neutral' | 'weak'

interface OfferDetail {
  label: string
  value: string
  signal: Signal
}

interface OfferCardProps {
  title: string
  titleIcon: string
  badge?: string
  recommended?: boolean
  details: OfferDetail[]
  onAgree: () => void
  onFallback: () => void
  onImprove: () => void
}

const signalColor: Record<Signal, string> = {
  good: 'bg-emerald-400',
  neutral: 'bg-amber-400',
  weak: 'bg-red-400',
}

export function OfferCard({
  title,
  titleIcon,
  badge,
  recommended,
  details,
  onAgree,
  onFallback,
  onImprove,
}: OfferCardProps) {
  return (
    <div
      className={`flex flex-col rounded-2xl border bg-white ${
        recommended
          ? 'border-emerald-700/30 shadow-lg ring-1 ring-emerald-700/10'
          : 'border-gray-200 shadow-sm'
      }`}
    >
      {/* Header */}
      <div className="flex items-center gap-2 px-6 pt-5 pb-1">
        <span className="text-xs">{titleIcon}</span>
        <span className="text-xs font-semibold uppercase tracking-widest text-gray-500">
          {title}
        </span>
        {badge && (
          <span className="ml-1 rounded-full bg-emerald-800 px-3 py-0.5 text-[11px] font-medium text-white">
            {badge}
          </span>
        )}
      </div>

      {/* Divider */}
      <div className="mx-6 mt-3 border-t border-gray-100" />

      {/* Details */}
      <div className="flex flex-col gap-5 px-6 pt-4 pb-6">
        {details.map((detail) => (
          <div key={detail.label} className="flex items-center gap-3">
            <span
              className={`mt-0.5 h-2 w-2 shrink-0 rounded-full ${signalColor[detail.signal]}`}
            />
            <div className="min-w-0">
              <p className="text-[10px] font-semibold uppercase tracking-widest text-gray-400">
                {detail.label}
              </p>
              <p className="text-base font-bold text-gray-900">{detail.value}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Actions */}
      <div className="mt-auto flex flex-col items-center gap-2.5 px-6 pb-5">
        <button
          type="button"
          onClick={onAgree}
          className="flex w-full items-center justify-center gap-2 rounded-xl bg-emerald-800 px-4 py-3 text-sm font-semibold text-white transition hover:bg-emerald-900"
        >
          <svg
            className="h-4 w-4"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={2.5}
            aria-hidden="true"
            role="presentation"
          >
            <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
          </svg>
          Agree
        </button>
        <button
          type="button"
          onClick={onFallback}
          className="flex w-full items-center justify-center gap-2 rounded-xl border border-gray-200 bg-white px-4 py-2.5 text-sm font-medium text-gray-600 transition hover:bg-gray-50"
        >
          <svg
            className="h-3.5 w-3.5 text-gray-400"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={2}
            aria-hidden="true"
            role="presentation"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"
            />
          </svg>
          Secure as fallback
        </button>
        <button
          type="button"
          onClick={onImprove}
          className="mt-1 text-xs text-gray-400 underline decoration-gray-300 underline-offset-2 transition hover:text-gray-600"
        >
          Improve terms
        </button>
      </div>
    </div>
  )
}
