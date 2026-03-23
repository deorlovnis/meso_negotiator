interface NoDealPhaseProps {
  onReset: () => void
}

export function NoDealPhase({ onReset }: NoDealPhaseProps) {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-gray-50/80 px-4">
      <div className="w-full max-w-sm rounded-2xl border border-gray-200 bg-white p-8 shadow-sm">
        <h1 className="mb-1 text-xl font-bold text-gray-900">Negotiation ended</h1>
        <p className="mb-6 text-sm text-gray-500">No deal was reached.</p>
        <button
          type="button"
          onClick={onReset}
          className="w-full rounded-xl border border-gray-200 bg-white px-4 py-2.5 text-sm font-medium text-gray-600 transition hover:bg-gray-50"
        >
          Reset demo
        </button>
      </div>
    </div>
  )
}
