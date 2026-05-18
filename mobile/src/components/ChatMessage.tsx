import type { ReactNode } from 'react'
import { StyleSheet, Text, View } from 'react-native'
import { colors, fontFamily, radii, shadows, spacing, typography } from '@/theme'

export function ChatMessage({
  role,
  children,
}: {
  role: 'user' | 'assistant'
  children: ReactNode
}) {
  const isUser = role === 'user'
  return (
    <View style={[styles.row, isUser && styles.rowUser]}>
      <View style={[styles.bubble, isUser ? styles.bubbleUser : styles.bubbleAssistant]}>
        {!isUser ? (
          <View style={styles.assistantLabelRow}>
            <View style={styles.assistantDot} />
            <Text style={styles.roleLabel}>SourcePath</Text>
          </View>
        ) : null}
        {children}
      </View>
    </View>
  )
}

export function ChatUserText({ children }: { children: string }) {
  return <Text style={styles.userText}>{children}</Text>
}

export function ChatAssistantText({ children }: { children: string }) {
  return <Text style={styles.assistantText}>{children}</Text>
}

const styles = StyleSheet.create({
  row: {
    marginBottom: spacing.md,
    alignItems: 'flex-start',
  },
  rowUser: {
    alignItems: 'flex-end',
  },
  bubble: {
    maxWidth: '90%',
    borderRadius: radii.card,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm + 4,
  },
  bubbleUser: {
    backgroundColor: colors.brandNavy,
    borderBottomRightRadius: 6,
    ...shadows.soft,
  },
  bubbleAssistant: {
    backgroundColor: colors.surfaceWhite,
    borderWidth: 1,
    borderColor: 'rgba(31, 40, 57, 0.08)',
    borderBottomLeftRadius: 6,
    ...shadows.soft,
  },
  assistantLabelRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginBottom: spacing.xs,
  },
  assistantDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: colors.brandBronze,
  },
  roleLabel: {
    fontFamily: fontFamily.body,
    fontSize: typography.caption,
    fontWeight: '600',
    color: colors.brandNavy,
    letterSpacing: 0.2,
  },
  userText: {
    fontFamily: fontFamily.body,
    fontSize: typography.small,
    lineHeight: 21,
    color: colors.surfaceWhite,
    fontWeight: '400',
  },
  assistantText: {
    fontFamily: fontFamily.body,
    fontSize: typography.small,
    lineHeight: 20,
    color: colors.brandNavy,
    opacity: 0.88,
  },
})
