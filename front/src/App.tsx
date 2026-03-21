import { OfferCard } from './components/OfferCard'

const noop = () => {}

const offers = [
  {
    title: 'Best Price',
    titleIcon: '💰',
    details: [
      { label: 'Price (per unit)', value: '$120.00', signal: 'good' as const },
      { label: 'Delivery Time', value: '10 days', signal: 'good' as const },
      { label: 'Payment Terms', value: 'Net 60', signal: 'neutral' as const },
      { label: 'Contract Length', value: '12 months', signal: 'good' as const },
    ],
  },
  {
    title: 'Most Balanced',
    titleIcon: '⚖️',
    badge: 'Recommended',
    recommended: true,
    details: [
      { label: 'Price (per unit)', value: '$115.00', signal: 'good' as const },
      { label: 'Delivery Time', value: '14 days', signal: 'neutral' as const },
      { label: 'Payment Terms', value: 'Net 45', signal: 'good' as const },
      { label: 'Contract Length', value: '24 months', signal: 'weak' as const },
    ],
  },
  {
    title: 'Fastest Payment',
    titleIcon: '⚡',
    details: [
      { label: 'Price (per unit)', value: '$110.00', signal: 'good' as const },
      { label: 'Delivery Time', value: '14 days', signal: 'neutral' as const },
      { label: 'Payment Terms', value: 'Net 30', signal: 'good' as const },
      { label: 'Contract Length', value: '12 months', signal: 'good' as const },
    ],
  },
]

function App() {
  return (
    <div className="flex min-h-screen flex-col items-center bg-gray-50/80 px-4 py-12">
      {/* Status badge */}
      <div className="mb-4 inline-flex items-center gap-1.5 rounded-full border border-emerald-200 bg-emerald-50 px-4 py-1.5">
        <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
        <span className="text-[11px] font-semibold uppercase tracking-widest text-emerald-700">
          Offers updated based on your preferences
        </span>
      </div>

      {/* Heading */}
      <h1 className="mb-10 text-3xl font-bold tracking-tight text-gray-900">
        Review your negotiated offers
      </h1>

      {/* Cards */}
      <div className="grid w-full max-w-4xl grid-cols-1 items-start gap-6 md:grid-cols-3">
        {offers.map((offer) => (
          <OfferCard
            key={offer.title}
            title={offer.title}
            titleIcon={offer.titleIcon}
            badge={offer.badge}
            recommended={offer.recommended}
            details={offer.details}
            onAgree={noop}
            onFallback={noop}
            onImprove={noop}
          />
        ))}
      </div>
    </div>
  )
}

export default App
