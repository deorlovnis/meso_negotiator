// Re-export shim — App.test.tsx mocks this path; the hook imports it via ../../../api
export {
  ApiError,
  agree,
  agreeSecured,
  endNegotiation,
  getOffers,
  improve,
  resetNegotiation,
  secure,
} from './features/negotiation/api/negotiation-api'
