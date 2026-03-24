import { useEffect, useReducer } from 'react'
import * as api from '../../../api'
import { NEGOTIATION_ID } from '../constants'
import { errorMessage, toLabelEnum } from '../lib/format'
import { type NegotiationView, reducer } from '../lib/reducer'
import type { Card, TermType } from '../types'

export function useNegotiation(): {
  view: NegotiationView
  handleAgree: (card: Card) => void
  handleFallback: (card: Card) => void
  handleImprove: (improveTerm: TermType, tradeTerm: TermType | null) => void
  handleEndNegotiation: () => void
  handleCompareAgree: (index: number) => void
  handleReset: () => void
  handleRetry: () => void
} {
  const [view, dispatch] = useReducer(reducer, { phase: 'loading' })

  useEffect(() => {
    api
      .getOffers(NEGOTIATION_ID)
      .then((data) => dispatch({ type: 'OFFERS_LOADED', data }))
      .catch((err: unknown) => dispatch({ type: 'ERROR', message: errorMessage(err) }))
  }, [])

  function handleAgree(card: Card) {
    if (view.phase !== 'offers') return
    const currentData = view.data
    dispatch({ type: 'ACTION_START', data: currentData, pendingAction: 'agree' })
    api
      .agree(NEGOTIATION_ID, toLabelEnum(card.label))
      .then((res) => dispatch({ type: 'AGREED', terms: res.agreed_terms, cardLabel: card.label }))
      .catch((err: unknown) => dispatch({ type: 'ERROR', message: errorMessage(err) }))
  }

  function handleFallback(card: Card) {
    if (view.phase !== 'offers') return
    const currentData = view.data
    dispatch({ type: 'ACTION_START', data: currentData, pendingAction: 'secure' })
    api
      .secure(NEGOTIATION_ID, toLabelEnum(card.label))
      .then((data) => dispatch({ type: 'OFFERS_UPDATED', data }))
      .catch((err: unknown) => dispatch({ type: 'ERROR', message: errorMessage(err) }))
  }

  function handleImprove(improveTerm: TermType, tradeTerm: TermType | null) {
    if (view.phase !== 'offers') return
    const currentData = view.data
    dispatch({ type: 'ACTION_START', data: currentData, pendingAction: 'improve' })
    api
      .improve(NEGOTIATION_ID, improveTerm, tradeTerm)
      .then((data) => dispatch({ type: 'OFFERS_UPDATED', data }))
      .catch((err: unknown) => dispatch({ type: 'ERROR', message: errorMessage(err) }))
  }

  function handleCompareAgree(index: number) {
    if (view.phase !== 'offers') return
    const currentData = view.data
    dispatch({ type: 'ACTION_START', data: currentData, pendingAction: 'agree' })
    api
      .agreeSecured(NEGOTIATION_ID, index)
      .then((res) => dispatch({ type: 'AGREED', terms: res.agreed_terms }))
      .catch((err: unknown) => dispatch({ type: 'ERROR', message: errorMessage(err) }))
  }

  function handleEndNegotiation() {
    if (view.phase !== 'offers') return
    const currentData = view.data
    dispatch({ type: 'ACTION_START', data: currentData, pendingAction: 'end' })
    api
      .endNegotiation(NEGOTIATION_ID)
      .then(() => dispatch({ type: 'NO_DEAL' }))
      .catch((err: unknown) => dispatch({ type: 'ERROR', message: errorMessage(err) }))
  }

  function handleReset() {
    api
      .resetNegotiation(NEGOTIATION_ID)
      .then(() => api.getOffers(NEGOTIATION_ID))
      .then((data) => dispatch({ type: 'OFFERS_LOADED', data }))
      .catch((err: unknown) => dispatch({ type: 'ERROR', message: errorMessage(err) }))
  }

  function handleRetry() {
    api
      .getOffers(NEGOTIATION_ID)
      .then((data) => dispatch({ type: 'OFFERS_LOADED', data }))
      .catch((err: unknown) => dispatch({ type: 'ERROR', message: errorMessage(err) }))
  }

  return {
    view,
    handleAgree,
    handleFallback,
    handleImprove,
    handleEndNegotiation,
    handleCompareAgree,
    handleReset,
    handleRetry,
  }
}
