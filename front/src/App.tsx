import { AgreedPhase } from './features/negotiation/components/AgreedPhase'
import { ErrorPhase } from './features/negotiation/components/ErrorPhase'
import { LoadingPhase } from './features/negotiation/components/LoadingPhase'
import { NoDealPhase } from './features/negotiation/components/NoDealPhase'
import { OffersPhase } from './features/negotiation/components/OffersPhase'
import { useNegotiation } from './features/negotiation/hooks/useNegotiation'

export default function App() {
  const {
    view,
    handleAgree,
    handleFallback,
    handleImprove,
    handleEndNegotiation,
    handleCompareAgree,
    handleReset,
    handleRetry,
  } = useNegotiation()

  switch (view.phase) {
    case 'loading':
      return <LoadingPhase />
    case 'agreed':
      return <AgreedPhase terms={view.terms} cardLabel={view.cardLabel} onReset={handleReset} />
    case 'no_deal':
      return <NoDealPhase onReset={handleReset} />
    case 'error':
      return <ErrorPhase message={view.message} onRetry={handleRetry} onReset={handleReset} />
    case 'offers':
    case 'acting':
      return (
        <OffersPhase
          data={view.data}
          isActing={view.phase === 'acting'}
          onAgree={handleAgree}
          onFallback={handleFallback}
          onImprove={handleImprove}
          onEndNegotiation={handleEndNegotiation}
          onCompareAgree={handleCompareAgree}
        />
      )
  }
}
