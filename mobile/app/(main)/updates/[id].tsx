import { useCallback, useEffect, useState } from 'react'
import {
  ActivityIndicator,
  Linking,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native'
import { useLocalSearchParams } from 'expo-router'
import { Ionicons } from '@expo/vector-icons'
import { DisclaimerCard } from '@/components'
import { DigitalBackdrop } from '@/components/digital'
import { LEGAL_DISCLAIMER_SHORT } from '@/lib/legalCopy'
import { UpdatesApiError, fetchUpdateDetail } from '@/lib/updatesApi'
import type { OfficialUpdateDetail } from '@/types/updates'
import { colors, fontFamily, radii, spacing, typography } from '@/theme'

const PUBLISHER_LABEL: Record<string, string> = {
  uscis: 'USCIS',
  dhs: 'DHS',
  federal_register: 'Federal Register',
}

function publisherLabel(publisher: string): string {
  return PUBLISHER_LABEL[publisher] ?? publisher.replace(/_/g, ' ').toUpperCase()
}

function formatDate(iso: string): string {
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return iso.slice(0, 10)
  return d.toLocaleDateString(undefined, {
    weekday: 'short',
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })
}

export default function UpdateDetailScreen() {
  const { id } = useLocalSearchParams<{ id: string }>()
  const updateId = Number(id)
  const [item, setItem] = useState<OfficialUpdateDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(async () => {
    if (!Number.isFinite(updateId)) {
      setError('Invalid update id.')
      setLoading(false)
      return
    }
    setLoading(true)
    setError(null)
    try {
      const response = await fetchUpdateDetail(updateId)
      setItem(response.item)
    } catch (err) {
      setItem(null)
      setError(err instanceof UpdatesApiError ? err.message : 'Could not load this update.')
    } finally {
      setLoading(false)
    }
  }, [updateId])

  useEffect(() => {
    load()
  }, [load])

  const openOfficial = useCallback(() => {
    if (item?.official_url) Linking.openURL(item.official_url)
  }, [item])

  return (
    <View style={styles.screen}>
      <DigitalBackdrop variant="updates" />
      {loading ? (
        <View style={styles.center}>
          <ActivityIndicator size="large" color={colors.brandNavy} />
        </View>
      ) : error || !item ? (
        <View style={styles.center}>
          <Text style={styles.errorText}>{error ?? 'Update not found.'}</Text>
          <Pressable onPress={load} style={styles.linkBtn}>
            <Text style={styles.linkText}>Try again</Text>
          </Pressable>
        </View>
      ) : (
        <ScrollView contentContainerStyle={styles.scroll} showsVerticalScrollIndicator={false}>
          <Text style={styles.publisher}>{publisherLabel(item.publisher)}</Text>
          <Text style={styles.date}>{formatDate(item.published_at)}</Text>
          <Text style={styles.title}>{item.title}</Text>

          <DisclaimerCard compact title="Plain-language summary">
            {`${LEGAL_DISCLAIMER_SHORT} This summary is not the official text.`}
          </DisclaimerCard>

          <View style={styles.bullets}>
            {item.summary_bullets.map((bullet, index) => (
              <View key={`${index}-${bullet.slice(0, 12)}`} style={styles.bulletRow}>
                <Text style={styles.bulletDot}>•</Text>
                <Text style={styles.bulletText}>{bullet}</Text>
              </View>
            ))}
          </View>

          {item.topic_labels.length > 0 ? (
            <View style={styles.tagRow}>
              {item.topic_labels.map((label) => (
                <View key={label} style={styles.tag}>
                  <Text style={styles.tagText}>{label}</Text>
                </View>
              ))}
            </View>
          ) : null}

          <Pressable
            onPress={openOfficial}
            style={({ pressed }) => [styles.primaryBtn, pressed && styles.btnPressed]}
            accessibilityRole="link"
          >
            <Ionicons name="open-outline" size={18} color={colors.surfaceWhite} />
            <Text style={styles.primaryBtnText}>Read official release</Text>
          </Pressable>

          <Text style={styles.officialNote}>
            Summaries are plain-language only. Always read the official release for complete and
            current information.
          </Text>
        </ScrollView>
      )}
    </View>
  )
}

const styles = StyleSheet.create({
  screen: {
    flex: 1,
    backgroundColor: colors.parchment,
  },
  scroll: {
    padding: spacing.md,
    paddingBottom: spacing.xl,
    gap: spacing.md,
    zIndex: 1,
  },
  center: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: spacing.lg,
    zIndex: 1,
  },
  publisher: {
    fontFamily: fontFamily.body,
    fontSize: typography.caption,
    fontWeight: '700',
    color: colors.brandBronze,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  date: {
    fontFamily: fontFamily.body,
    fontSize: typography.caption,
    color: colors.brandNavy,
    opacity: 0.6,
  },
  title: {
    fontFamily: fontFamily.heading,
    fontSize: typography.h3,
    fontWeight: '600',
    color: colors.brandNavy,
    lineHeight: 26,
  },
  bullets: {
    gap: spacing.sm,
  },
  bulletRow: {
    flexDirection: 'row',
    gap: spacing.sm,
  },
  bulletDot: {
    fontFamily: fontFamily.body,
    fontSize: typography.body,
    color: colors.brandBronze,
    lineHeight: 22,
  },
  bulletText: {
    flex: 1,
    fontFamily: fontFamily.body,
    fontSize: typography.small,
    lineHeight: 21,
    color: colors.brandNavy,
  },
  tagRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: spacing.xs,
  },
  tag: {
    backgroundColor: colors.bronzeTint,
    borderRadius: radii.full,
    paddingHorizontal: spacing.sm,
    paddingVertical: 4,
  },
  tagText: {
    fontFamily: fontFamily.body,
    fontSize: 10,
    fontWeight: '600',
    color: colors.brandNavy,
  },
  primaryBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: spacing.sm,
    backgroundColor: colors.brandNavy,
    borderRadius: radii.button,
    paddingVertical: spacing.md,
    paddingHorizontal: spacing.lg,
  },
  btnPressed: {
    opacity: 0.9,
  },
  primaryBtnText: {
    fontFamily: fontFamily.body,
    fontSize: typography.body,
    fontWeight: '700',
    color: colors.surfaceWhite,
  },
  officialNote: {
    fontFamily: fontFamily.body,
    fontSize: typography.caption,
    lineHeight: 18,
    color: colors.brandNavy,
    opacity: 0.6,
    fontStyle: 'italic',
  },
  errorText: {
    fontFamily: fontFamily.body,
    fontSize: typography.small,
    color: colors.brandNavy,
    textAlign: 'center',
  },
  linkBtn: {
    marginTop: spacing.md,
  },
  linkText: {
    fontFamily: fontFamily.body,
    fontWeight: '700',
    color: colors.brandBronze,
  },
})
