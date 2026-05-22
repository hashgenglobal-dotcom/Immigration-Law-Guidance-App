export type UpdateTopic = {
  id: string
  label: string
  description: string
}

export type OfficialUpdateItem = {
  id: number
  publisher: string
  title: string
  official_url: string
  published_at: string
  summary_bullets: string[]
  topic_tags: string[]
  topic_labels: string[]
  fetched_at: string
  has_official_excerpt: boolean
}

export type OfficialUpdateDetail = OfficialUpdateItem & {
  raw_excerpt: string | null
  ask_prefill_message: string
}

export type OfficialUpdatesListResponse = {
  status: string
  privacy_mode: string
  items: OfficialUpdateItem[]
  count: number
  total: number
  limit: number
  offset: number
  topics_filter: string[]
}

export type OfficialUpdateDetailResponse = {
  status: string
  privacy_mode: string
  item: OfficialUpdateDetail
}

export type UpdateTopicsResponse = {
  status: string
  topics: UpdateTopic[]
}
