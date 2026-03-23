import type { Terms } from '../types'

interface AgreedPhaseProps {
  terms: Terms
  onReset: () => void
}

export function AgreedPhase({ terms, onReset }: AgreedPhaseProps) {
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
          onClick={onReset}
          className="mt-6 w-full rounded-xl border border-gray-200 bg-white px-4 py-2.5 text-sm font-medium text-gray-600 transition hover:bg-gray-50"
        >
          Reset demo
        </button>
      </div>
    </div>
  )
}
