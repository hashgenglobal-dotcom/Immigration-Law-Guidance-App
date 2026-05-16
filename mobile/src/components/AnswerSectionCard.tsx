import type { ReactNode } from 'react'
import { StyleSheet, Text, View } from 'react-native'
import { colors, spacing, typography } from '@/theme'

export function AnswerSectionCard({
  title,
  children,
  variant = 'default',
}: {
  title: string
  children: ReactNode
  variant?: 'default' | 'risks' | 'steps'
}) {
  const variantStyle =
    variant === 'risks'
      ? styles.risks
      : variant === 'steps'
        ? styles.steps
        : styles.default

  return (
    <View style={[styles.card, variantStyle]}>
      <Text style={styles.title}>{title}</Text>
      {children}
    </View>
  )
}

const styles = StyleSheet.create({
  card: {
    borderRadius: 14,
    borderWidth: 1,
    padding: spacing.md,
    marginBottom: spacing.md,
  },
  default: {
    backgroundColor: colors.surface,
    borderColor: colors.border,
  },
  risks: {
    backgroundColor: colors.riskMediumBg,
    borderColor: colors.riskMediumBorder,
  },
  steps: {
    backgroundColor: colors.disclaimerBg,
    borderColor: colors.disclaimerBorder,
  },
  title: {
    fontSize: typography.subheading,
    fontWeight: '700',
    color: colors.text,
    marginBottom: spacing.sm,
  },
})
