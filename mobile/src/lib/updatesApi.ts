import { getApiBaseUrl } from '@/constants/api'
import type {
  OfficialUpdateDetailResponse,
  OfficialUpdatesListResponse,
  UpdateTopicsResponse,
} from '@/types/updates'

export class UpdatesApiError extends Error {
  constructor(message: string) {
    super(message)
    this.name = 'UpdatesApiError'
  }
}

function parseDetail(body: unknown): string | null {
  if (!body || typeof body !== 'object') return null
  const detail = (body as { detail?: unknown }).detail
  if (typeof detail === 'string') return detail
  if (detail && typeof detail === 'object' && 'message' in detail) {
    const msg = (detail as { message?: unknown }).message
    if (typeof msg === 'string') return msg
  }
  return null
}

export async function fetchUpdateTopics(): Promise<UpdateTopicsResponse> {
  const baseUrl = getApiBaseUrl()
  const response = await fetch(`${baseUrl}/api/updates/topics`, {
    headers: { Accept: 'application/json' },
  })
  if (!response.ok) {
    throw new UpdatesApiError(
      parseDetail(await response.json().catch(() => null)) ??
        'Could not load update topics.',
    )
  }
  return response.json() as Promise<UpdateTopicsResponse>
}

export async function fetchUpdatesList(params?: {
  topics?: string[]
  limit?: number
  offset?: number
}): Promise<OfficialUpdatesListResponse> {
  const baseUrl = getApiBaseUrl()
  const search = new URLSearchParams()
  if (params?.topics?.length) search.set('topics', params.topics.join(','))
  if (params?.limit != null) search.set('limit', String(params.limit))
  if (params?.offset != null) search.set('offset', String(params.offset))
  const qs = search.toString()
  const url = `${baseUrl}/api/updates${qs ? `?${qs}` : ''}`
  const response = await fetch(url, { headers: { Accept: 'application/json' } })
  if (!response.ok) {
    const detail = parseDetail(await response.json().catch(() => null))
    if (response.status === 503) {
      throw new UpdatesApiError(
        detail ??
          'Official updates are not ready yet. Ask your admin to run the database migration and ingest script.',
      )
    }
    throw new UpdatesApiError(detail ?? 'Could not load official updates.')
  }
  return response.json() as Promise<OfficialUpdatesListResponse>
}

export async function fetchUpdateDetail(id: number): Promise<OfficialUpdateDetailResponse> {
  const baseUrl = getApiBaseUrl()
  const url = `${baseUrl}/api/updates/${id}`
  const response = await fetch(url, { headers: { Accept: 'application/json' } })
  if (!response.ok) {
    throw new UpdatesApiError(
      parseDetail(await response.json().catch(() => null)) ?? 'Could not load this update.',
    )
  }
  return response.json() as Promise<OfficialUpdateDetailResponse>
}
