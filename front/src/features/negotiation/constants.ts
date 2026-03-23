import type { CardLabel, Signal } from './types'

export const NEGOTIATION_ID = 'demo'

export const LABEL_DISPLAY_TO_ENUM: Record<string, CardLabel> = {
  'BEST PRICE': 'BEST_PRICE',
  'MOST BALANCED': 'MOST_BALANCED',
  'FASTEST PAYMENT': 'FASTEST_PAYMENT',
}

export const LABEL_ICON: Record<string, string> = {
  'BEST PRICE': '💰',
  'MOST BALANCED': '⚖️',
  'FASTEST PAYMENT': '⚡',
}

export const SIGNAL_COLOR: Record<Signal, string> = {
  good: 'bg-emerald-400',
  neutral: 'bg-amber-400',
  weak: 'bg-red-400',
}
