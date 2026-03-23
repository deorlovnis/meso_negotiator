export const config = {
  api: {
    baseUrl: import.meta.env.VITE_API_BASE_URL ?? '',
  },
  negotiationId: import.meta.env.VITE_NEGOTIATION_ID ?? 'demo',
  appName: import.meta.env.VITE_APP_NAME ?? 'MESO Negotiator',
  isDev: import.meta.env.DEV,
  isProd: import.meta.env.PROD,
} as const
