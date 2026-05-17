import { StyleSheet, Text, View } from 'react-native'
import { colors, fontFamily, spacing, typography } from '@/theme'

export function AboutSectionTitle({
  title,
  subtitle,
}: {
  title: string
  subtitle?: string
}) {
  return (
    <View style={styles.wrap}>
      <View style={styles.accent} />
      <View style={styles.copy}>
        <Text style={styles.title}>{title}</Text>
        {subtitle ? <Text style={styles.subtitle}>{subtitle}</Text> : null}
      </View>
    </View>
  )
}

const styles = StyleSheet.create({
  wrap: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: spacing.sm,
    marginBottom: spacing.md,
  },
  accent: {
    width: 4,
    alignSelf: 'stretch',
    minHeight: 32,
    borderRadius: 2,
    backgroundColor: colors.brandNavy,
  },
  copy: {
    flex: 1,
    gap: 4,
  },
  title: {
    fontFamily: fontFamily.heading,
    fontSize: typography.h3,
    fontWeight: '600',
    color: colors.brandNavy,
    letterSpacing: -0.2,
  },
  subtitle: {
    fontFamily: fontFamily.body,
    fontSize: typography.caption,
    lineHeight: 17,
    color: colors.brandNavy,
    opacity: 0.65,
  },
})
