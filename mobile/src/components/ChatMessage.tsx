import type { ReactNode } from 'react'
import { StyleSheet, Text, View } from 'react-native'
import { colors, radii, spacing, typography } from '@/theme'

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
        {!isUser ? <Text style={styles.roleLabel}>Assistant</Text> : null}
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
    marginBottom: spacing.sm,
    alignItems: 'flex-start',
  },
  rowUser: {
    alignItems: 'flex-end',
  },
  bubble: {
    maxWidth: '92%',
    borderRadius: radii.md,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm + 2,
  },
  bubbleUser: {
    backgroundColor: colors.navy,
    borderBottomRightRadius: 4,
  },
  bubbleAssistant: {
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
    borderBottomLeftRadius: 4,
  },
  roleLabel: {
    fontSize: typography.caption,
    fontWeight: '600',
    color: colors.bronzeDark,
    marginBottom: 4,
    textTransform: 'uppercase',
    letterSpacing: 0.3,
  },
  userText: {
    fontSize: typography.small,
    lineHeight: 20,
    color: colors.onNavy,
  },
  assistantText: {
    fontSize: typography.small,
    lineHeight: 20,
    color: colors.textSecondary,
  },
})
