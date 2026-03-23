import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import {
  ApiError,
  agree,
  endNegotiation,
  getOffers,
  improve,
  resetNegotiation,
  secure,
} from './negotiation-api'

// ---------------------------------------------------------------------------
// Mock fetch
// ---------------------------------------------------------------------------

function mockFetchOk(body: unknown): void {
  vi.stubGlobal(
    'fetch',
    vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(body),
    }),
  )
}

function mockFetchError(status: number, jsonBody: unknown): void {
  vi.stubGlobal(
    'fetch',
    vi.fn().mockResolvedValue({
      ok: false,
      status,
      json: () => Promise.resolve(jsonBody),
      text: () => Promise.resolve(JSON.stringify(jsonBody)),
    }),
  )
}

function mockFetchErrorTextFallback(status: number, textBody: string): void {
  vi.stubGlobal(
    'fetch',
    vi.fn().mockResolvedValue({
      ok: false,
      status,
      json: () => Promise.reject(new SyntaxError('Unexpected token')),
      text: () => Promise.resolve(textBody),
    }),
  )
}

function mockFetchNetworkFailure(message: string): void {
  vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError(message)))
}

beforeEach(() => {
  vi.restoreAllMocks()
})

afterEach(() => {
  vi.unstubAllGlobals()
})

// ---------------------------------------------------------------------------
// B1: Returns parsed JSON on 200
// Error category: Interface errors (happy path contract)
// ---------------------------------------------------------------------------
describe('B1: Returns parsed JSON on 200', () => {
  it('resolves with the parsed JSON body', async () => {
    const body = {
      banner: 'Round 1',
      cards: [],
      is_final_round: false,
      is_first_visit: true,
      secured_offer: null,
      actions_available: [],
    }
    mockFetchOk(body)
    const result = await getOffers('demo')
    expect(result).toEqual(body)
  })
})

// ---------------------------------------------------------------------------
// B2: Throws ApiError with status + parsed JSON detail on non-OK
// Error category: Interface errors (error contract)
// ---------------------------------------------------------------------------
describe('B2: Throws ApiError with status and JSON detail on non-OK', () => {
  it('throws ApiError with status and parsed JSON detail', async () => {
    const detail = { error: 'Negotiation is terminal' }
    mockFetchError(409, detail)

    await expect(getOffers('demo')).rejects.toThrow(ApiError)

    try {
      await getOffers('demo')
    } catch (err) {
      expect(err).toBeInstanceOf(ApiError)
      if (err instanceof ApiError) {
        expect(err.status).toBe(409)
        expect(err.detail).toEqual(detail)
        expect(err.name).toBe('ApiError')
      }
    }
  })
})

// ---------------------------------------------------------------------------
// B3: Falls back to response.text() when error body isn't JSON
// Error category: Interface errors (fallback parsing)
// ---------------------------------------------------------------------------
describe('B3: Falls back to response.text() when error body is not JSON', () => {
  it('uses text body as detail when JSON parsing fails', async () => {
    mockFetchErrorTextFallback(502, 'Bad Gateway')

    try {
      await getOffers('demo')
      expect.unreachable('Should have thrown')
    } catch (err) {
      expect(err).toBeInstanceOf(ApiError)
      if (err instanceof ApiError) {
        expect(err.status).toBe(502)
        expect(err.detail).toBe('Bad Gateway')
      }
    }
  })
})

// ---------------------------------------------------------------------------
// B4: getOffers calls GET /api/negotiations/{id}/offers
// Error category: Interface errors (URL and method contract)
// ---------------------------------------------------------------------------
describe('B4: getOffers calls GET /api/negotiations/{id}/offers', () => {
  it('sends GET request to the correct URL', async () => {
    mockFetchOk({
      banner: '',
      cards: [],
      is_final_round: false,
      is_first_visit: true,
      secured_offer: null,
      actions_available: [],
    })

    await getOffers('session-42')

    expect(fetch).toHaveBeenCalledOnce()
    const [url, options] = (fetch as ReturnType<typeof vi.fn>).mock.calls[0]
    expect(url).toBe('/api/negotiations/session-42/offers')
    // GET is the default when no method is specified
    expect(options?.method).toBeUndefined()
  })
})

// ---------------------------------------------------------------------------
// B5: agree sends POST with {card_label: 'BEST_PRICE'}
// Error category: Interface errors (request body contract)
// ---------------------------------------------------------------------------
describe('B5: agree sends POST with card_label in body', () => {
  it('sends POST to /agree with JSON body containing card_label', async () => {
    mockFetchOk({
      status: 'agreed',
      agreed_terms: { price: '$42', delivery: '14d', payment: 'Net30', contract: '12m' },
    })

    await agree('demo', 'BEST_PRICE')

    expect(fetch).toHaveBeenCalledOnce()
    const [url, options] = (fetch as ReturnType<typeof vi.fn>).mock.calls[0]
    expect(url).toBe('/api/negotiations/demo/agree')
    expect(options.method).toBe('POST')
    expect(options.headers).toEqual({ 'Content-Type': 'application/json' })
    expect(JSON.parse(options.body)).toEqual({ card_label: 'BEST_PRICE' })
  })
})

// ---------------------------------------------------------------------------
// B6: secure sends POST to /secure
// Error category: Interface errors (URL contract)
// ---------------------------------------------------------------------------
describe('B6: secure sends POST to /secure', () => {
  it('sends POST to /secure with card_label in body', async () => {
    mockFetchOk({ secured_offer: { label: 'MOST_BALANCED', terms: {} } })

    await secure('demo', 'MOST_BALANCED')

    expect(fetch).toHaveBeenCalledOnce()
    const [url, options] = (fetch as ReturnType<typeof vi.fn>).mock.calls[0]
    expect(url).toBe('/api/negotiations/demo/secure')
    expect(options.method).toBe('POST')
    expect(JSON.parse(options.body)).toEqual({ card_label: 'MOST_BALANCED' })
  })
})

// ---------------------------------------------------------------------------
// B7: improve sends POST to /improve
// Error category: Interface errors (URL contract)
// ---------------------------------------------------------------------------
describe('B7: improve sends POST to /improve', () => {
  it('sends POST to /improve with card_label in body', async () => {
    mockFetchOk({
      banner: '',
      cards: [],
      is_final_round: false,
      is_first_visit: false,
      secured_offer: null,
      actions_available: [],
    })

    await improve('demo', 'FASTEST_PAYMENT')

    expect(fetch).toHaveBeenCalledOnce()
    const [url, options] = (fetch as ReturnType<typeof vi.fn>).mock.calls[0]
    expect(url).toBe('/api/negotiations/demo/improve')
    expect(options.method).toBe('POST')
    expect(JSON.parse(options.body)).toEqual({ card_label: 'FASTEST_PAYMENT' })
  })
})

// ---------------------------------------------------------------------------
// B8: endNegotiation sends POST with no body
// Error category: Interface errors (request shape)
// ---------------------------------------------------------------------------
describe('B8: endNegotiation sends POST with no body', () => {
  it('sends POST to /end with no body property', async () => {
    mockFetchOk({ status: 'ended' })

    await endNegotiation('demo')

    expect(fetch).toHaveBeenCalledOnce()
    const [url, options] = (fetch as ReturnType<typeof vi.fn>).mock.calls[0]
    expect(url).toBe('/api/negotiations/demo/end')
    expect(options.method).toBe('POST')
    expect(options.body).toBeUndefined()
  })
})

// ---------------------------------------------------------------------------
// B9: resetNegotiation sends POST to /reset
// Error category: Interface errors (URL contract)
// ---------------------------------------------------------------------------
describe('B9: resetNegotiation sends POST to /reset', () => {
  it('sends POST to /reset with no body', async () => {
    mockFetchOk({ status: 'reset' })

    await resetNegotiation('demo')

    expect(fetch).toHaveBeenCalledOnce()
    const [url, options] = (fetch as ReturnType<typeof vi.fn>).mock.calls[0]
    expect(url).toBe('/api/negotiations/demo/reset')
    expect(options.method).toBe('POST')
    expect(options.body).toBeUndefined()
  })
})

// ---------------------------------------------------------------------------
// B10: Network failure propagates as raw Error, not ApiError
// Error category: Interface errors (error type discrimination)
// ---------------------------------------------------------------------------
describe('B10: Network failure propagates as raw Error, not ApiError', () => {
  it('propagates TypeError from fetch, not wrapped in ApiError', async () => {
    mockFetchNetworkFailure('Failed to fetch')

    try {
      await getOffers('demo')
      expect.unreachable('Should have thrown')
    } catch (err) {
      expect(err).toBeInstanceOf(TypeError)
      expect(err).not.toBeInstanceOf(ApiError)
      if (err instanceof Error) {
        expect(err.message).toBe('Failed to fetch')
      }
    }
  })

  it('network failure on POST also propagates raw Error', async () => {
    mockFetchNetworkFailure('Network request failed')

    await expect(agree('demo', 'BEST_PRICE')).rejects.toThrow(TypeError)
    await expect(agree('demo', 'BEST_PRICE')).rejects.not.toThrow(ApiError)
  })
})

// ---------------------------------------------------------------------------
// Additional adversarial tests
// ---------------------------------------------------------------------------

describe('ApiError class properties', () => {
  // Error category: Interface errors (class contract)
  it('ApiError.name is "ApiError"', () => {
    const err = new ApiError(500, null)
    expect(err.name).toBe('ApiError')
  })

  it('ApiError extends Error', () => {
    const err = new ApiError(404, 'not found')
    expect(err).toBeInstanceOf(Error)
    expect(err).toBeInstanceOf(ApiError)
  })

  it('ApiError.message contains status code', () => {
    const err = new ApiError(422, { error: 'validation' })
    expect(err.message).toBe('API error 422')
  })

  it('ApiError preserves status and detail as readonly', () => {
    const detail = { error: 'conflict' }
    const err = new ApiError(409, detail)
    expect(err.status).toBe(409)
    expect(err.detail).toBe(detail)
  })
})
