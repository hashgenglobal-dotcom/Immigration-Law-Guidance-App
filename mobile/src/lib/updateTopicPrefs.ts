import AsyncStorage from '@react-native-async-storage/async-storage'

const STORAGE_KEY = '@sourcepath/official_update_topic_filters'

/** Topic ids the user selected; empty = show all (no API filter). */
export async function loadSavedTopicFilters(): Promise<string[]> {
  try {
    const raw = await AsyncStorage.getItem(STORAGE_KEY)
    if (!raw) return []
    const parsed = JSON.parse(raw) as unknown
    if (!Array.isArray(parsed)) return []
    return parsed.filter((t): t is string => typeof t === 'string' && t.length > 0)
  } catch {
    return []
  }
}

export async function saveTopicFilters(topicIds: string[]): Promise<void> {
  await AsyncStorage.setItem(STORAGE_KEY, JSON.stringify(topicIds))
}

export async function clearTopicFilters(): Promise<void> {
  await AsyncStorage.removeItem(STORAGE_KEY)
}
