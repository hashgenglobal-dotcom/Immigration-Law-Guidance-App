import { useCallback, useEffect, useState } from 'react'
import {
  ActivityIndicator,
  Pressable,
  StyleSheet,
  Text,
  View,
} from 'react-native'
import { useRouter } from 'expo-router'
import { Ionicons } from '@expo/vector-icons'
import { DisclaimerCard, ScreenScroll } from '@/components'
import { DigitalBackdrop } from '@/components/digital'
import { TopicFilterPills, UpdateCard, UpdatesHeader } from '@/components/updates'
import { LEGAL_DISCLAIMER_SHORT } from '@/lib/legalCopy'
import { clearTopicFilters, loadSavedTopicFilters, saveTopicFilters } from '@/lib/updateTopicPrefs'
import { UpdatesApiError, fetchUpdateTopics, fetchUpdatesList } from '@/lib/updatesApi'
import type { OfficialUpdateItem, UpdateTopic } from '@/types/updates'
import { colors, fontFamily, spacing, typography } from '@/theme'

export default function UpdatesScreen() {
  const router = useRouter()
  const [topics, setTopics] = useState<UpdateTopic[]>([])
  const [selectedTopicIds, setSelectedTopicIds] = useState<string[]>([])
  const [items, setItems] = useState<OfficialUpdateItem[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadSavedTopicFilters().then(setSelectedTopicIds)
    fetchUpdateTopics()
      .then((r) => setTopics(r.topics))
      .catch(() => setTopics([]))
  }, [])

  const loadList = useCallback(async (topicIds: string[]) => {
    setLoading(true)
    setError(null)
    try {
      const response = await fetchUpdatesList({
        topics: topicIds.length ? topicIds : undefined,
        limit: 50,
      })
      setItems(response.items)
      setTotal(response.total)
    } catch (err) {
      setItems([])
      setTotal(0)
      setError(err instanceof UpdatesApiError ? err.message : 'Could not load official updates.')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadList(selectedTopicIds)
  }, [selectedTopicIds, loadList])

  const handleToggleTopic = useCallback(
    async (topicId: string) => {
      const next = selectedTopicIds.includes(topicId)
        ? selectedTopicIds.filter((id) => id !== topicId)
        : [...selectedTopicIds, topicId]
      setSelectedTopicIds(next)
      await saveTopicFilters(next)
    },
    [selectedTopicIds],
  )

  const handleClearAll = useCallback(async () => {
    setSelectedTopicIds([])
    await clearTopicFilters()
  }, [])

  return (
    <View style={styles.screen}>
      <DigitalBackdrop variant="updates" />
      <ScreenScroll contentStyle={styles.scroll}>
        <UpdatesHeader total={total} />

        <DisclaimerCard compact title="Not legal advice">
          {`${LEGAL_DISCLAIMER_SHORT} Summaries are generated from public excerpts only—always open the official release for complete information.`}
        </DisclaimerCard>

        {topics.length > 0 ? (
          <TopicFilterPills
            topics={topics}
            selectedIds={selectedTopicIds}
            onToggle={handleToggleTopic}
            onClearAll={handleClearAll}
          />
        ) : null}

        {loading ? (
          <View style={styles.center}>
            <ActivityIndicator size="large" color={colors.brandNavy} />
            <Text style={styles.centerText}>Loading official updates…</Text>
          </View>
        ) : error ? (
          <View style={styles.empty}>
            <Ionicons name="cloud-offline-outline" size={32} color={colors.brandBronze} />
            <Text style={styles.emptyTitle}>Updates unavailable</Text>
            <Text style={styles.emptyBody}>{error}</Text>
            <Pressable
              onPress={() => loadList(selectedTopicIds)}
              style={({ pressed }) => [styles.retryBtn, pressed && styles.retryPressed]}
            >
              <Text style={styles.retryText}>Try again</Text>
            </Pressable>
          </View>
        ) : items.length === 0 ? (
          <View style={styles.empty}>
            <Ionicons name="newspaper-outline" size={32} color={colors.brandBronze} />
            <Text style={styles.emptyTitle}>No updates match</Text>
            <Text style={styles.emptyBody}>
              Try clearing topic filters or run the ingest script on the backend.
            </Text>
            <Pressable
              onPress={handleClearAll}
              style={({ pressed }) => [styles.retryBtn, pressed && styles.retryPressed]}
            >
              <Text style={styles.retryText}>Show all topics</Text>
            </Pressable>
          </View>
        ) : (
          <View style={styles.list}>
            {items.map((item) => (
              <UpdateCard
                key={item.id}
                item={item}
                onPress={() =>
                  router.push({
                    pathname: '/updates/[id]',
                    params: { id: String(item.id) },
                  })
                }
              />
            ))}
          </View>
        )}
      </ScreenScroll>
    </View>
  )
}

const styles = StyleSheet.create({
  screen: {
    flex: 1,
    backgroundColor: colors.parchment,
  },
  scroll: {
    paddingTop: spacing.md,
    paddingBottom: spacing.xl,
    zIndex: 1,
  },
  list: {
    gap: spacing.sm,
    marginTop: spacing.sm,
  },
  center: {
    alignItems: 'center',
    paddingVertical: spacing.xl,
    gap: spacing.sm,
  },
  centerText: {
    fontFamily: fontFamily.body,
    fontSize: typography.caption,
    color: colors.brandNavy,
    opacity: 0.65,
  },
  empty: {
    alignItems: 'center',
    paddingVertical: spacing.xl,
    gap: spacing.sm,
  },
  emptyTitle: {
    fontFamily: fontFamily.heading,
    fontSize: typography.h3,
    fontWeight: '600',
    color: colors.brandNavy,
  },
  emptyBody: {
    fontFamily: fontFamily.body,
    fontSize: typography.small,
    lineHeight: 20,
    color: colors.brandNavy,
    opacity: 0.72,
    textAlign: 'center',
    paddingHorizontal: spacing.lg,
  },
  retryBtn: {
    marginTop: spacing.sm,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
  },
  retryPressed: {
    opacity: 0.7,
  },
  retryText: {
    fontFamily: fontFamily.body,
    fontSize: typography.caption,
    fontWeight: '700',
    color: colors.brandBronze,
  },
})
