import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { OfferCard } from './OfferCard.js'

// ---------------------------------------------------------------------------
// Shared fixtures — realistic domain data, not "foo/bar" placeholders
// ---------------------------------------------------------------------------

function baseProps(
  overrides: Partial<Parameters<typeof OfferCard>[0]> = {},
): Parameters<typeof OfferCard>[0] {
  return {
    title: 'Best Price',
    titleIcon: '💰',
    details: [
      { label: 'Price (per unit)', value: '$12.50/k', signal: 'good' as const },
      { label: 'Delivery Time', value: '10-day', signal: 'neutral' as const },
      { label: 'Payment Terms', value: 'Net 30', signal: 'neutral' as const },
      { label: 'Contract Length', value: '24-month', signal: 'weak' as const },
    ],
    onAgree: vi.fn(),
    onFallback: vi.fn(),
    onImprove: vi.fn(),
    ...overrides,
  }
}

// ---------------------------------------------------------------------------
// F1–F2: Title, icon, and badge rendering
// ---------------------------------------------------------------------------

describe('OfferCard — header rendering', () => {
  // Error category: input/output — verifying the component renders its props
  it('F1: renders title text and titleIcon', () => {
    render(<OfferCard {...baseProps()} />)

    expect(screen.getByText('Best Price')).toBeInTheDocument()
    expect(screen.getByText('💰')).toBeInTheDocument()
  })

  // Error category: logic — conditional rendering branch (badge present)
  it('F2: renders badge when provided', () => {
    render(<OfferCard {...baseProps({ badge: 'Recommended' })} />)

    expect(screen.getByText('Recommended')).toBeInTheDocument()
  })

  // Error category: logic — conditional rendering branch (badge absent)
  it('F2 negative: omits badge when not provided', () => {
    render(<OfferCard {...baseProps({ badge: undefined })} />)

    expect(screen.queryByText('Recommended')).not.toBeInTheDocument()
  })
})

// ---------------------------------------------------------------------------
// F3–F4: Recommended visual treatment
// ---------------------------------------------------------------------------

describe('OfferCard — recommended styling', () => {
  // Error category: logic — conditional class application
  it('F3: recommended=true applies ring-1 class', () => {
    const { container } = render(<OfferCard {...baseProps({ recommended: true })} />)

    const card = container.firstElementChild as HTMLElement
    expect(card.className).toContain('ring-1')
  })

  // Error category: logic — inverse conditional
  it('F4: recommended=false applies border-gray-200, no ring', () => {
    const { container } = render(<OfferCard {...baseProps({ recommended: false })} />)

    const card = container.firstElementChild as HTMLElement
    expect(card.className).toContain('border-gray-200')
    expect(card.className).not.toContain('ring-1')
  })
})

// ---------------------------------------------------------------------------
// F5–F6: Detail rows and signal colors
// ---------------------------------------------------------------------------

describe('OfferCard — detail rows', () => {
  // Error category: input/output — detail row structure
  it('F5: renders label, value, and a signal color dot for each detail', () => {
    render(<OfferCard {...baseProps()} />)

    expect(screen.getByText('Price (per unit)')).toBeInTheDocument()
    expect(screen.getByText('$12.50/k')).toBeInTheDocument()

    // Signal dot: the span with the bg color class should be a sibling
    const priceRow = screen
      .getByText('Price (per unit)')
      .closest('.flex.items-center') as HTMLElement
    const dot = priceRow.querySelector('span[class*="rounded-full"]') as HTMLElement
    expect(dot).toBeTruthy()
    expect(dot.className).toContain('bg-emerald-400')
  })

  // Error category: computation — mapping correctness for all 3 signal values
  it('F6: signal mapping — good=emerald, neutral=amber, weak=red', () => {
    render(<OfferCard {...baseProps()} />)

    // We rely on the fixture: price=good, delivery=neutral, contract=weak
    const rows = document.querySelectorAll('.flex.items-center.gap-3')

    // Price row (good) → bg-emerald-400
    const priceDot = rows[0].querySelector('span[class*="rounded-full"]') as HTMLElement
    expect(priceDot.className).toContain('bg-emerald-400')

    // Delivery row (neutral) → bg-amber-400
    const deliveryDot = rows[1].querySelector('span[class*="rounded-full"]') as HTMLElement
    expect(deliveryDot.className).toContain('bg-amber-400')

    // Contract row (weak) → bg-red-400
    const contractDot = rows[3].querySelector('span[class*="rounded-full"]') as HTMLElement
    expect(contractDot.className).toContain('bg-red-400')
  })

  // Error category: input/output — ordering preservation
  it('F13: details render in array order', () => {
    const details = [
      { label: 'Alpha', value: '1', signal: 'good' as const },
      { label: 'Beta', value: '2', signal: 'neutral' as const },
      { label: 'Gamma', value: '3', signal: 'weak' as const },
    ]
    render(<OfferCard {...baseProps({ details })} />)

    const labels = screen.getAllByText(/Alpha|Beta|Gamma/)
    expect(labels[0]).toHaveTextContent('Alpha')
    expect(labels[1]).toHaveTextContent('Beta')
    expect(labels[2]).toHaveTextContent('Gamma')
  })

  // Error category: data — empty input boundary
  it('F14: empty details array renders without crashing', () => {
    render(<OfferCard {...baseProps({ details: [] })} />)

    // Card still renders its title
    expect(screen.getByText('Best Price')).toBeInTheDocument()
    // No detail rows
    expect(screen.queryByText('Price (per unit)')).not.toBeInTheDocument()
  })
})

// ---------------------------------------------------------------------------
// F7–F9: Action buttons — presence and disabled state
// ---------------------------------------------------------------------------

describe('OfferCard — action buttons', () => {
  // Error category: input/output — all buttons rendered
  it('F7: renders all 3 action buttons', () => {
    render(<OfferCard {...baseProps()} />)

    expect(screen.getByRole('button', { name: /agree/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /secure as fallback/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /improve terms/i })).toBeInTheDocument()
  })

  // Error category: logic — disabled prop propagation
  it('F8: disabled=true disables all buttons', () => {
    render(<OfferCard {...baseProps({ disabled: true })} />)

    expect(screen.getByRole('button', { name: /agree/i })).toBeDisabled()
    expect(screen.getByRole('button', { name: /secure as fallback/i })).toBeDisabled()
    expect(screen.getByRole('button', { name: /improve terms/i })).toBeDisabled()
  })

  // Error category: logic — inverse disabled state
  it('F9: disabled=false (default) enables all buttons', () => {
    render(<OfferCard {...baseProps()} />)

    expect(screen.getByRole('button', { name: /agree/i })).toBeEnabled()
    expect(screen.getByRole('button', { name: /secure as fallback/i })).toBeEnabled()
    expect(screen.getByRole('button', { name: /improve terms/i })).toBeEnabled()
  })
})

// ---------------------------------------------------------------------------
// F10–F12: Button click handlers
// ---------------------------------------------------------------------------

describe('OfferCard — button interactions', () => {
  // Error category: interface — callback invocation
  it('F10: "Agree" click calls onAgree exactly once', async () => {
    const user = userEvent.setup()
    const onAgree = vi.fn()
    render(<OfferCard {...baseProps({ onAgree })} />)

    await user.click(screen.getByRole('button', { name: /agree/i }))

    expect(onAgree).toHaveBeenCalledTimes(1)
  })

  // Error category: interface — callback invocation
  it('F11: "Secure as fallback" click calls onFallback', async () => {
    const user = userEvent.setup()
    const onFallback = vi.fn()
    render(<OfferCard {...baseProps({ onFallback })} />)

    await user.click(screen.getByRole('button', { name: /secure as fallback/i }))

    expect(onFallback).toHaveBeenCalledTimes(1)
  })

  // Error category: interface — callback invocation
  it('F12: "Improve terms" click calls onImprove', async () => {
    const user = userEvent.setup()
    const onImprove = vi.fn()
    render(<OfferCard {...baseProps({ onImprove })} />)

    await user.click(screen.getByRole('button', { name: /improve terms/i }))

    expect(onImprove).toHaveBeenCalledTimes(1)
  })
})
