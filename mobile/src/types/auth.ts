export type AuthMode = 'guest' | 'user'

export type UserSession = {
  mode: 'user'
  email: string
  displayName: string
}

export type GuestSession = {
  mode: 'guest'
  guestChatsUsed: number
}

export type AppSession = UserSession | GuestSession
