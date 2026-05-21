/** Guest allowance — wire to backend quota when API is ready */
export const GUEST_CHAT_LIMIT = 5

export const STORAGE_KEYS = {
  onboardingComplete: '@sourcepath/onboarding_complete',
  /** Guest only: `{ mode: 'guest', guestChatsUsed: number }` — never user PII */
  session: '@sourcepath/session',
  /** JWT from POST /api/auth/* — secure store only */
  accessToken: 'sourcepath_access_token',
} as const
