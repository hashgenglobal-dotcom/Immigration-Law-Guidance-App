import { useState } from 'react'
import {
  Alert,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native'
import { Ionicons } from '@expo/vector-icons'
import type { ComponentProps } from 'react'
import { colors, fontFamily, layout, radii, spacing, typography } from '@/theme'

const MAX_CHARS = 500

const DEFAULT_SUGGESTIONS = [
  'How to apply for EAD?',
  'What is a Notice to Appear?',
  'Can I adjust status in the US?',
] as const

type IoniconName = ComponentProps<typeof Ionicons>['name']

const INPUT_SHADOW = {
  shadowColor: '#1F2839',
  shadowOffset: { width: 0, height: 8 },
  shadowOpacity: 0.14,
  shadowRadius: 16,
  elevation: 8,
}

function ToolButton({
  icon,
  onPress,
  disabled,
  active,
  activeTint,
  accessibilityLabel,
}: {
  icon: IoniconName
  onPress: () => void
  disabled?: boolean
  active?: boolean
  activeTint?: 'recording'
  accessibilityLabel: string
}) {
  return (
    <Pressable
      onPress={onPress}
      disabled={disabled}
      accessibilityRole="button"
      accessibilityLabel={accessibilityLabel}
      accessibilityState={{ disabled: !!disabled, selected: !!active }}
      style={({ pressed }) => [
        styles.toolBtn,
        active && activeTint === 'recording' && styles.toolBtnRecording,
        active && activeTint !== 'recording' && styles.toolBtnActive,
        pressed && !disabled && styles.toolBtnPressed,
        disabled && styles.toolBtnDisabled,
      ]}
    >
      <Ionicons
        name={icon}
        size={22}
        color={
          active && activeTint === 'recording'
            ? '#C0392B'
            : active
              ? colors.surfaceWhite
              : colors.brandBronze
        }
      />
    </Pressable>
  )
}

export function ChatComposer({
  value,
  onChangeText,
  onSend,
  onSuggestionPress,
  disabled,
  loading,
  suggestions = DEFAULT_SUGGESTIONS,
}: {
  value: string
  onChangeText: (text: string) => void
  onSend: () => void
  onSuggestionPress?: (text: string) => void
  disabled?: boolean
  loading?: boolean
  suggestions?: readonly string[]
}) {
  const [recording, setRecording] = useState(false)
  const canSend = value.trim().length > 0 && !disabled && !loading
  const controlsDisabled = disabled || loading

  const handleUploadPress = () => {
    Alert.alert(
      'Upload document',
      'Document upload is not available in this preview. Type your question or use a suggested prompt.',
      [{ text: 'OK' }],
    )
  }

  const handleMicPress = () => {
    if (recording) {
      setRecording(false)
      Alert.alert(
        'Voice recording',
        'Voice-to-text is not available in this preview. Your recording was not saved.',
        [{ text: 'OK' }],
      )
      return
    }
    setRecording(true)
  }

  return (
    <View style={styles.dock}>
      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={styles.suggestionsRow}
        keyboardShouldPersistTaps="handled"
      >
        {suggestions.map((label) => (
          <Pressable
            key={label}
            onPress={() => onSuggestionPress?.(label)}
            disabled={controlsDisabled}
            style={({ pressed }) => [styles.suggestion, pressed && styles.suggestionPressed]}
            accessibilityRole="button"
          >
            <Text style={styles.suggestionText} numberOfLines={1}>
              {label}
            </Text>
          </Pressable>
        ))}
      </ScrollView>

      {recording ? (
        <View style={styles.recordingBanner}>
          <View style={styles.recordingDot} />
          <Text style={styles.recordingText}>Listening… tap mic to stop</Text>
        </View>
      ) : null}

      <View style={styles.inputShell}>
        <View style={styles.inputRow}>
          <ToolButton
            icon="attach-outline"
            onPress={handleUploadPress}
            disabled={controlsDisabled}
            accessibilityLabel="Upload document"
          />
          <ToolButton
            icon={recording ? 'stop-circle' : 'mic-outline'}
            onPress={handleMicPress}
            disabled={controlsDisabled}
            active={recording}
            activeTint="recording"
            accessibilityLabel={recording ? 'Stop recording' : 'Start voice recording'}
          />
          <TextInput
            style={styles.input}
            value={value}
            onChangeText={(t) => onChangeText(t.slice(0, MAX_CHARS))}
            placeholder="Message…"
            placeholderTextColor={colors.textMuted}
            multiline={false}
            maxLength={MAX_CHARS}
            editable={!controlsDisabled}
            returnKeyType="send"
            onSubmitEditing={() => {
              if (canSend) onSend()
            }}
            blurOnSubmit={false}
          />
          <Pressable
            onPress={onSend}
            disabled={!canSend}
            accessibilityRole="button"
            accessibilityLabel="Send message"
            style={({ pressed }) => [
              styles.sendBtn,
              canSend && styles.sendBtnActive,
              pressed && canSend && styles.sendBtnPressed,
              !canSend && styles.sendBtnDisabled,
            ]}
          >
            <Ionicons
              name="send"
              size={20}
              color={canSend ? colors.surfaceWhite : 'rgba(31, 40, 57, 0.35)'}
            />
          </Pressable>
        </View>
        <Text style={styles.counter}>
          {value.length}/{MAX_CHARS}
        </Text>
      </View>
    </View>
  )
}

const styles = StyleSheet.create({
  dock: {
    paddingHorizontal: spacing.md,
    paddingTop: spacing.sm,
    paddingBottom: spacing.md,
    backgroundColor: colors.parchment,
    borderTopWidth: 1,
    borderTopColor: 'rgba(31, 40, 57, 0.06)',
  },
  suggestionsRow: {
    gap: spacing.sm,
    paddingBottom: spacing.sm,
    paddingRight: spacing.sm,
  },
  suggestion: {
    backgroundColor: colors.surfaceWhite,
    borderRadius: radii.full,
    paddingVertical: 8,
    paddingHorizontal: spacing.md,
    borderWidth: 1,
    borderColor: 'rgba(31, 40, 57, 0.12)',
  },
  suggestionPressed: {
    opacity: 0.78,
    borderColor: colors.brandBronze,
  },
  suggestionText: {
    fontFamily: fontFamily.body,
    fontSize: typography.caption,
    fontWeight: '500',
    color: colors.brandNavy,
  },
  recordingBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
    marginBottom: spacing.sm,
    paddingHorizontal: spacing.sm,
    paddingVertical: spacing.xs + 2,
    borderRadius: radii.button,
    backgroundColor: 'rgba(192, 57, 43, 0.08)',
  },
  recordingDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: '#C0392B',
  },
  recordingText: {
    fontFamily: fontFamily.body,
    fontSize: typography.caption,
    fontWeight: '500',
    color: '#8B3A3A',
  },
  inputShell: {
    alignItems: 'stretch',
  },
  inputRow: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.surfaceWhite,
    borderRadius: radii.card,
    borderWidth: 2,
    borderColor: colors.brandNavy,
    minHeight: layout.minTouchTarget + 4,
    paddingVertical: 4,
    paddingHorizontal: 4,
    gap: 2,
    ...INPUT_SHADOW,
  },
  input: {
    flex: 1,
    fontFamily: fontFamily.body,
    fontSize: typography.body,
    lineHeight: Platform.OS === 'ios' ? 20 : 22,
    color: colors.brandNavy,
    backgroundColor: 'transparent',
    paddingVertical: Platform.OS === 'ios' ? 10 : 8,
    paddingHorizontal: spacing.xs,
    height: layout.minTouchTarget - 4,
  },
  toolBtn: {
    minWidth: layout.minTouchTarget,
    minHeight: layout.minTouchTarget,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: radii.button,
  },
  toolBtnPressed: {
    backgroundColor: colors.bronzeTint,
  },
  toolBtnActive: {
    backgroundColor: colors.brandNavy,
  },
  toolBtnRecording: {
    backgroundColor: 'rgba(192, 57, 43, 0.12)',
    borderWidth: 1,
    borderColor: 'rgba(192, 57, 43, 0.35)',
  },
  toolBtnDisabled: {
    opacity: 0.45,
  },
  sendBtn: {
    minWidth: layout.minTouchTarget,
    minHeight: layout.minTouchTarget,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: radii.button,
    backgroundColor: colors.bronzeTint,
  },
  sendBtnActive: {
    backgroundColor: colors.brandNavy,
  },
  sendBtnPressed: {
    opacity: 0.9,
    transform: [{ scale: 0.96 }],
  },
  sendBtnDisabled: {
    backgroundColor: 'rgba(31, 40, 57, 0.06)',
  },
  counter: {
    alignSelf: 'flex-end',
    marginTop: 4,
    marginRight: spacing.xs,
    fontFamily: fontFamily.body,
    fontSize: 10,
    color: colors.brandNavy,
    opacity: 0.45,
  },
})
