import { StyleSheet, Text, View } from 'react-native'
import { colors, fontFamily, radii, spacing } from '@/theme'

export function AccessBadge({ variant }: { variant: 'full' | 'limited' }) {
  const isFull = variant === 'full'

  return (
    <View style={[styles.badge, isFull ? styles.full : styles.limited]}>
      <Text style={[styles.text, isFull ? styles.fullText : styles.limitedText]}>
        {isFull ? 'Full access' : 'Limited access'}
      </Text>
    </View>
  )
}

const styles = StyleSheet.create({
  badge: {
    alignSelf: 'flex-start',
    paddingHorizontal: spacing.sm,
    paddingVertical: 4,
    borderRadius: radii.sm,
    marginBottom: spacing.sm,
  },
  full: {
    backgroundColor: 'rgba(255, 255, 255, 0.15)',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.25)',
  },
  limited: {
    backgroundColor: 'rgba(156, 123, 92, 0.25)',
    borderWidth: 1,
    borderColor: 'rgba(156, 123, 92, 0.5)',
  },
  text: {
    fontFamily: fontFamily.body,
    fontSize: 10,
    fontWeight: '700',
    letterSpacing: 0.6,
    textTransform: 'uppercase',
  },
  fullText: {
    color: colors.surfaceWhite,
  },
  limitedText: {
    color: colors.brandBronzeLight,
  },
})
