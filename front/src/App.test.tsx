import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import App from './App.js'
import type { OffersResponse } from './features/negotiation/types.js'

// ---------------------------------------------------------------------------
// Mock the API module — all functions replaced with vi.fn()
// ---------------------------------------------------------------------------

vi.mock('./api', () => ({
  ApiError: class ApiError extends Error {
    status: number
    detail: unknown
    constructor(status: number, detail: unknown) {
      super(`API error ${status}`)
      this.name = 'ApiError'
      this.status = status
      this.detail = detail
    }
  },
  getOffers: vi.fn(),
  agree: vi.fn(),
  secure: vi.fn(),
  improve: vi.fn(),
  endNegotiation: vi.fn(),
  resetNegotiation: vi.fn(),
}))

// Typed access to mocked functions
import * as api from './api.js'

const mockGetOffers = vi.mocked(api.getOffers)
const mockAgree = vi.mocked(api.agree)
const mockSecure = vi.mocked(api.secure)
const mockImprove = vi.mocked(api.improve)
const mockEndNegotiation = vi.mocked(api.endNegotiation)
const mockResetNegotiation = vi.mocked(api.resetNegotiation)

// ---------------------------------------------------------------------------
// Fixtures — realistic domain data
// ---------------------------------------------------------------------------

function makeOffersResponse(overrides: Partial<OffersResponse> = {}): OffersResponse {
  return {
    banner: 'Round 1 of 3',
    is_final_round: false,
    is_first_visit: true,
    cards: [
      {
        label: 'BEST PRICE',
        recommended: true,
        terms: {
          price: '$12.50/k',
          delivery: '10-day',
          payment: 'Net 30',
          contract: '24-month',
        },
        signals: {
          price: 'good',
          delivery: 'neutral',
          payment: 'neutral',
          contract: 'weak',
        },
      },
    ],
    secured_offer: null,
    actions_available: ['improve'],
    ...overrides,
  }
}

function makeMultiCardResponse(): OffersResponse {
  return makeOffersResponse({
    cards: [
      {
        label: 'BEST PRICE',
        recommended: true,
        terms: {
          price: '$12.50/k',
          delivery: '10-day',
          payment: 'Net 30',
          contract: '24-month',
        },
        signals: {
          price: 'good',
          delivery: 'neutral',
          payment: 'neutral',
          contract: 'weak',
        },
      },
      {
        label: 'MOST BALANCED',
        recommended: false,
        terms: {
          price: '$14.00/k',
          delivery: '7-day',
          payment: 'Net 15',
          contract: '12-month',
        },
        signals: {
          price: 'neutral',
          delivery: 'good',
          payment: 'good',
          contract: 'neutral',
        },
      },
    ],
  })
}

// ---------------------------------------------------------------------------
// Test lifecycle — reset mocks between tests
// ---------------------------------------------------------------------------

beforeEach(() => {
  vi.resetAllMocks()
})

// ---------------------------------------------------------------------------
// D1: Loading phase
// ---------------------------------------------------------------------------

describe('App — loading phase', () => {
  // Error category: input/output — initial render before API resolves
  it('D1: renders "Loading offers" while getOffers is pending', () => {
    // getOffers returns a never-resolving promise to keep loading state
    mockGetOffers.mockReturnValue(new Promise(() => {}))
    render(<App />)

    expect(screen.getByText(/loading offers/i)).toBeInTheDocument()
  })
})

// ---------------------------------------------------------------------------
// D2, D8–D12: Offers phase rendering
// ---------------------------------------------------------------------------

describe('App — offers phase rendering', () => {
  // Error category: input/output — cards rendered from API data
  it('D2: renders one OfferCard per card after getOffers resolves', async () => {
    const data = makeMultiCardResponse()
    mockGetOffers.mockResolvedValue(data)
    render(<App />)

    // Wait for offers to load — each card has an "Agree" button
    const agreeButtons = await screen.findAllByRole('button', { name: /agree/i })
    expect(agreeButtons).toHaveLength(2)
  })

  // Error category: input/output — banner text rendered
  it('D8: renders banner text from response', async () => {
    mockGetOffers.mockResolvedValue(makeOffersResponse({ banner: 'Round 2 of 3' }))
    render(<App />)

    expect(await screen.findByText('Round 2 of 3')).toBeInTheDocument()
  })

  // Error category: logic — secured offer indicator present
  it('D9: shows secured offer indicator when secured_offer is present', async () => {
    const data = makeOffersResponse({
      secured_offer: {
        label: 'BEST PRICE',
        terms: {
          price: '$12.50/k',
          delivery: '10-day',
          payment: 'Net 30',
          contract: '24-month',
        },
      },
    })
    mockGetOffers.mockResolvedValue(data)
    render(<App />)

    const indicator = await screen.findByText(/fallback secured/i)
    expect(indicator).toBeInTheDocument()
    // The price appears inside the same paragraph as "Fallback secured:"
    expect(indicator.textContent).toContain('$12.50/k')
  })

  // Error category: logic — secured offer indicator absent
  it('D10: no secured offer indicator when secured_offer is null', async () => {
    mockGetOffers.mockResolvedValue(makeOffersResponse({ secured_offer: null }))
    render(<App />)

    await screen.findByText(/round 1 of 3/i)
    expect(screen.queryByText(/fallback secured/i)).not.toBeInTheDocument()
  })

  // Error category: logic — conditional "End negotiation" button
  it('D11: final round shows "End negotiation" button', async () => {
    mockGetOffers.mockResolvedValue(makeOffersResponse({ is_final_round: true }))
    render(<App />)

    expect(await screen.findByRole('button', { name: /end negotiation/i })).toBeInTheDocument()
  })

  // Error category: logic — inverse conditional
  it('D12: non-final round hides "End negotiation" button', async () => {
    mockGetOffers.mockResolvedValue(makeOffersResponse({ is_final_round: false }))
    render(<App />)

    await screen.findByText(/round 1 of 3/i)
    expect(screen.queryByRole('button', { name: /end negotiation/i })).not.toBeInTheDocument()
  })
})

// ---------------------------------------------------------------------------
// D3, D7: Agreed phase
// ---------------------------------------------------------------------------

describe('App — agreed phase', () => {
  // Error category: input/output — agreed screen content
  it('D3: agreed phase shows "Deal agreed" and all 4 term values', async () => {
    const user = userEvent.setup()
    mockGetOffers.mockResolvedValue(makeOffersResponse())
    mockAgree.mockResolvedValue({
      status: 'agreed',
      agreed_terms: {
        price: '$11.00/k',
        delivery: '7-day',
        payment: 'Net 15',
        contract: '12-month',
      },
    })
    render(<App />)

    const agreeBtn = await screen.findByRole('button', { name: /^agree$/i })
    await user.click(agreeBtn)

    expect(await screen.findByText('Deal agreed')).toBeInTheDocument()
    expect(screen.getByText('$11.00/k')).toBeInTheDocument()
    expect(screen.getByText('7-day')).toBeInTheDocument()
    expect(screen.getByText('Net 15')).toBeInTheDocument()
    expect(screen.getByText('12-month')).toBeInTheDocument()
  })

  // Error category: input/output — "Reset demo" button presence
  it('D7: agreed phase has "Reset demo" button', async () => {
    const user = userEvent.setup()
    mockGetOffers.mockResolvedValue(makeOffersResponse())
    mockAgree.mockResolvedValue({
      status: 'agreed',
      agreed_terms: {
        price: '$11.00/k',
        delivery: '7-day',
        payment: 'Net 15',
        contract: '12-month',
      },
    })
    render(<App />)

    const agreeBtn = await screen.findByRole('button', { name: /^agree$/i })
    await user.click(agreeBtn)

    expect(await screen.findByRole('button', { name: /reset demo/i })).toBeInTheDocument()
  })
})

// ---------------------------------------------------------------------------
// D4: No-deal phase
// ---------------------------------------------------------------------------

describe('App — no-deal phase', () => {
  // Error category: input/output — no-deal screen content
  it('D4: no-deal phase shows "Negotiation ended"', async () => {
    const user = userEvent.setup()
    mockGetOffers.mockResolvedValue(makeOffersResponse({ is_final_round: true }))
    mockEndNegotiation.mockResolvedValue({ status: 'ended' })
    render(<App />)

    const endBtn = await screen.findByRole('button', { name: /end negotiation/i })
    await user.click(endBtn)

    expect(await screen.findByText('Negotiation ended')).toBeInTheDocument()
  })
})

// ---------------------------------------------------------------------------
// D5–D6: Error phase
// ---------------------------------------------------------------------------

describe('App — error phase', () => {
  // Error category: input/output — error message display
  it('D5: error phase shows "Something went wrong" and the error message', async () => {
    mockGetOffers.mockRejectedValue(new Error('Network failure'))
    render(<App />)

    expect(await screen.findByText('Something went wrong')).toBeInTheDocument()
    expect(screen.getByText('Network failure')).toBeInTheDocument()
  })

  // Error category: input/output — error phase button presence
  it('D6: error phase has "Retry" and "Reset demo" buttons', async () => {
    mockGetOffers.mockRejectedValue(new Error('Server down'))
    render(<App />)

    expect(await screen.findByRole('button', { name: /retry/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /reset demo/i })).toBeInTheDocument()
  })
})

// ---------------------------------------------------------------------------
// D13–D14: Acting phase — disabled state during API calls
// ---------------------------------------------------------------------------

describe('App — acting phase (disabled state)', () => {
  // Error category: logic — buttons disabled while action in flight
  it('D13: acting phase disables all card buttons', async () => {
    const user = userEvent.setup()
    // getOffers resolves, but agree never resolves — stays in acting state
    mockGetOffers.mockResolvedValue(makeOffersResponse())
    mockAgree.mockReturnValue(new Promise(() => {}))
    render(<App />)

    const agreeBtn = await screen.findByRole('button', { name: /^agree$/i })
    await user.click(agreeBtn)

    // After clicking agree, all buttons should be disabled
    await waitFor(() => {
      const buttons = screen.getAllByRole('button')
      for (const btn of buttons) {
        expect(btn).toBeDisabled()
      }
    })
  })

  // Error category: logic — "End negotiation" disabled during action
  it('D14: acting phase disables "End negotiation" button', async () => {
    const user = userEvent.setup()
    mockGetOffers.mockResolvedValue(makeOffersResponse({ is_final_round: true }))
    mockAgree.mockReturnValue(new Promise(() => {}))
    render(<App />)

    const agreeBtn = await screen.findByRole('button', { name: /^agree$/i })
    await user.click(agreeBtn)

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /end negotiation/i })).toBeDisabled()
    })
  })
})

// ---------------------------------------------------------------------------
// E1–E3: Interaction — API call arguments
// ---------------------------------------------------------------------------

describe('App — interaction API calls', () => {
  // Error category: interface — correct API call arguments
  it('E1: "Agree" calls api.agree with correct arguments', async () => {
    const user = userEvent.setup()
    mockGetOffers.mockResolvedValue(makeOffersResponse())
    mockAgree.mockResolvedValue({
      status: 'agreed',
      agreed_terms: {
        price: '$12.50/k',
        delivery: '10-day',
        payment: 'Net 30',
        contract: '24-month',
      },
    })
    render(<App />)

    const agreeBtn = await screen.findByRole('button', { name: /^agree$/i })
    await user.click(agreeBtn)

    expect(mockAgree).toHaveBeenCalledWith('demo', 'BEST_PRICE')
  })

  // Error category: interface — secure triggers getOffers chain
  it('E2: "Secure" calls api.secure then api.getOffers in sequence', async () => {
    const user = userEvent.setup()
    const initialData = makeOffersResponse()
    const refreshedData = makeOffersResponse({ banner: 'Round 1 of 3 — refreshed' })
    mockGetOffers.mockResolvedValueOnce(initialData).mockResolvedValueOnce(refreshedData)
    mockSecure.mockResolvedValue({
      secured_offer: {
        label: 'BEST PRICE',
        terms: initialData.cards[0].terms,
      },
    })
    render(<App />)

    const secureBtn = await screen.findByRole('button', { name: /secure as fallback/i })
    await user.click(secureBtn)

    await waitFor(() => {
      expect(mockSecure).toHaveBeenCalledWith('demo', 'BEST_PRICE')
      // getOffers called: once on mount + once after secure
      expect(mockGetOffers).toHaveBeenCalledTimes(2)
    })
  })

  // Error category: interface — improve API call
  it('E3: "Improve" calls api.improve when in actions_available', async () => {
    const user = userEvent.setup()
    const updatedData = makeOffersResponse({ banner: 'Round 2 of 3' })
    mockGetOffers.mockResolvedValue(makeOffersResponse({ actions_available: ['improve'] }))
    mockImprove.mockResolvedValue(updatedData)
    render(<App />)

    const improveBtn = await screen.findByRole('button', { name: /improve terms/i })
    await user.click(improveBtn)

    await waitFor(() => {
      expect(mockImprove).toHaveBeenCalledWith('demo', 'BEST_PRICE')
    })
  })
})

// ---------------------------------------------------------------------------
// E5–E6: Successful transitions
// ---------------------------------------------------------------------------

describe('App — successful transitions', () => {
  // Error category: logic — state transition: offers → agreed
  it('E5: successful agree transitions to "Deal agreed" screen', async () => {
    const user = userEvent.setup()
    mockGetOffers.mockResolvedValue(makeOffersResponse())
    mockAgree.mockResolvedValue({
      status: 'agreed',
      agreed_terms: {
        price: '$10.00/k',
        delivery: '5-day',
        payment: 'Net 10',
        contract: '6-month',
      },
    })
    render(<App />)

    const agreeBtn = await screen.findByRole('button', { name: /^agree$/i })
    await user.click(agreeBtn)

    expect(await screen.findByText('Deal agreed')).toBeInTheDocument()
  })

  // Error category: logic — state transition: offers → no_deal
  it('E6: successful end transitions to "Negotiation ended" screen', async () => {
    const user = userEvent.setup()
    mockGetOffers.mockResolvedValue(makeOffersResponse({ is_final_round: true }))
    mockEndNegotiation.mockResolvedValue({ status: 'ended' })
    render(<App />)

    const endBtn = await screen.findByRole('button', { name: /end negotiation/i })
    await user.click(endBtn)

    expect(await screen.findByText('Negotiation ended')).toBeInTheDocument()
  })
})

// ---------------------------------------------------------------------------
// E7–E9: Error handling and recovery
// ---------------------------------------------------------------------------

describe('App — error handling and recovery', () => {
  // Error category: integration — API failure → error screen
  it('E7: failed API call shows error screen with extracted message', async () => {
    const user = userEvent.setup()
    mockGetOffers.mockResolvedValue(makeOffersResponse())
    mockAgree.mockRejectedValue(new Error('Connection refused'))
    render(<App />)

    const agreeBtn = await screen.findByRole('button', { name: /^agree$/i })
    await user.click(agreeBtn)

    expect(await screen.findByText('Something went wrong')).toBeInTheDocument()
    expect(screen.getByText('Connection refused')).toBeInTheDocument()
  })

  // Error category: logic — retry from error state
  it('E8: "Retry" calls getOffers and returns to offers phase', async () => {
    const user = userEvent.setup()
    const offersData = makeOffersResponse()
    // First call fails → error screen; second call (retry) succeeds
    mockGetOffers.mockRejectedValueOnce(new Error('Timeout')).mockResolvedValueOnce(offersData)
    render(<App />)

    // Wait for error screen
    await screen.findByText('Something went wrong')
    const retryBtn = screen.getByRole('button', { name: /retry/i })
    await user.click(retryBtn)

    // Should return to offers phase
    expect(await screen.findByText('Round 1 of 3')).toBeInTheDocument()
    // getOffers called twice: once on mount (failed), once on retry
    expect(mockGetOffers).toHaveBeenCalledTimes(2)
  })

  // Error category: logic — reset from error state
  it('E9: "Reset" calls resetNegotiation then getOffers', async () => {
    const user = userEvent.setup()
    const offersData = makeOffersResponse()
    mockGetOffers.mockRejectedValueOnce(new Error('Bad state')).mockResolvedValueOnce(offersData)
    mockResetNegotiation.mockResolvedValue({ status: 'reset' })
    render(<App />)

    await screen.findByText('Something went wrong')
    const resetBtn = screen.getByRole('button', { name: /reset demo/i })
    await user.click(resetBtn)

    expect(await screen.findByText('Round 1 of 3')).toBeInTheDocument()
    expect(mockResetNegotiation).toHaveBeenCalledWith('demo')
    // getOffers: once on mount (failed), once after reset
    expect(mockGetOffers).toHaveBeenCalledTimes(2)
  })
})

// ---------------------------------------------------------------------------
// E10–E12: Handler guards and mount behavior
// ---------------------------------------------------------------------------

describe('App — handler guards and mount', () => {
  // Error category: logic — phase guard prevents actions in wrong phase
  it('E10: handlers guard against non-offers phase (no API call when acting)', async () => {
    const user = userEvent.setup()
    // Lock in acting state — agree never resolves
    mockGetOffers.mockResolvedValue(makeOffersResponse({ is_final_round: true }))
    mockAgree.mockReturnValue(new Promise(() => {}))
    render(<App />)

    // Click agree to enter acting state
    const agreeBtn = await screen.findByRole('button', { name: /^agree$/i })
    await user.click(agreeBtn)

    // Wait for buttons to be disabled (acting state)
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /end negotiation/i })).toBeDisabled()
    })

    // endNegotiation should NOT have been called — we are in acting phase
    expect(mockEndNegotiation).not.toHaveBeenCalled()
  })

  // Error category: interface — mount calls getOffers exactly once
  it('E11: mount calls getOffers exactly once with "demo"', async () => {
    mockGetOffers.mockResolvedValue(makeOffersResponse())
    render(<App />)

    await screen.findByText('Round 1 of 3')
    expect(mockGetOffers).toHaveBeenCalledTimes(1)
    expect(mockGetOffers).toHaveBeenCalledWith('demo')
  })

  // Error category: integration — mount failure shows error screen
  it('E12: mount failure shows error screen', async () => {
    mockGetOffers.mockRejectedValue(new Error('Service unavailable'))
    render(<App />)

    expect(await screen.findByText('Something went wrong')).toBeInTheDocument()
    expect(screen.getByText('Service unavailable')).toBeInTheDocument()
  })
})

// ---------------------------------------------------------------------------
// G1–G5: Edge cases
// ---------------------------------------------------------------------------

describe('App — edge cases', () => {
  // Error category: data — empty cards boundary
  it('G1: empty cards array renders without crashing', async () => {
    mockGetOffers.mockResolvedValue(makeOffersResponse({ cards: [] }))
    render(<App />)

    // Banner still renders
    expect(await screen.findByText('Round 1 of 3')).toBeInTheDocument()
    // No agree buttons — no cards
    expect(screen.queryByRole('button', { name: /^agree$/i })).not.toBeInTheDocument()
  })

  // Error category: logic — unknown label gets fallback icon
  it('G2: unknown card label uses fallback icon', async () => {
    const data = makeOffersResponse({
      cards: [
        {
          label: 'MYSTERY_OPTION',
          recommended: false,
          terms: {
            price: '$99.00/k',
            delivery: '30-day',
            payment: 'Net 60',
            contract: '36-month',
          },
          signals: {
            price: 'weak',
            delivery: 'weak',
            payment: 'neutral',
            contract: 'neutral',
          },
        },
      ],
    })
    mockGetOffers.mockResolvedValue(data)
    render(<App />)

    // The fallback icon is '📋' — verify it renders
    expect(await screen.findByText('📋')).toBeInTheDocument()
  })

  // Error category: integration — secure failure should NOT call getOffers
  it('G4: secure failure does NOT call getOffers afterward', async () => {
    const user = userEvent.setup()
    mockGetOffers.mockResolvedValue(makeOffersResponse())
    mockSecure.mockRejectedValue(new Error('Secure failed'))
    render(<App />)

    const secureBtn = await screen.findByRole('button', { name: /secure as fallback/i })
    await user.click(secureBtn)

    await screen.findByText('Something went wrong')
    // getOffers called only once — on mount. NOT after failed secure.
    expect(mockGetOffers).toHaveBeenCalledTimes(1)
  })

  // Error category: integration — resetNegotiation failure should NOT call getOffers
  it('G5: resetNegotiation failure does NOT call getOffers afterward', async () => {
    const user = userEvent.setup()
    mockGetOffers.mockRejectedValueOnce(new Error('Initial fail'))
    mockResetNegotiation.mockRejectedValue(new Error('Reset failed'))
    render(<App />)

    await screen.findByText('Something went wrong')
    const resetBtn = screen.getByRole('button', { name: /reset demo/i })
    await user.click(resetBtn)

    // Should show error again
    await waitFor(() => {
      expect(screen.getByText('Something went wrong')).toBeInTheDocument()
    })
    // getOffers called only once — the initial mount. NOT after failed reset.
    expect(mockGetOffers).toHaveBeenCalledTimes(1)
  })
})
