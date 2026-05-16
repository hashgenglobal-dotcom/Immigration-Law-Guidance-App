import { StyleSheet, Text, TextInput, View } from 'react-native'
import { PrimaryButton } from './PrimaryButton'
import { colors, radii, spacing, typography } from '@/theme'

const MAX_CHARS = 500

export function ChatComposer({
  value,
  onChangeText,
  onSend,
  disabled,
  loading,
}: {
  value: string
  onChangeText: (text: string) => void
  onSend: () => void
  disabled?: boolean
  loading?: boolean
}) {
  const canSend = value.trim().length > 0 && !disabled && !loading

  return (
    <View style={styles.wrap}>
      <View style={styles.inputRow}>
        <TextInput
          style={styles.input}
          value={value}
          onChangeText={(t) => onChangeText(t.slice(0, MAX_CHARS))}
          placeholder="Ask about immigration topics…"
          placeholderTextColor={colors.textMuted}
          multiline
          maxLength={MAX_CHARS}
          editable={!disabled && !loading}
          textAlignVertical="top"
        />
      </View>
      <View style={styles.footer}>
        <Text style={styles.hint}>{value.length}/{MAX_CHARS}</Text>
        <PrimaryButton
          label={loading ? 'Sending…' : 'Send'}
          onPress={onSend}
          disabled={!canSend}
          compact
        />
      </View>
    </View>
  )
}

const styles = StyleSheet.create({
  wrap: {
    borderTopWidth: 1,
    borderTopColor: colors.border,
    backgroundColor: colors.surface,
    paddingHorizontal: spacing.md,
    paddingTop: spacing.sm,
    paddingBottom: spacing.sm,
  },
  inputRow: {
    backgroundColor: colors.creamMuted,
    borderRadius: radii.md,
    borderWidth: 1,
    borderColor: colors.border,
    minHeight: 44,
    maxHeight: 120,
    paddingHorizontal: spacing.sm + 2,
    paddingVertical: spacing.sm,
  },
  input: {
    fontSize: typography.small,
    lineHeight: 20,
    color: colors.text,
    minHeight: 36,
  },
  footer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginTop: spacing.sm,
    gap: spacing.sm,
  },
  hint: {
    flex: 1,
    fontSize: typography.caption,
    color: colors.textMuted,
  },
})
