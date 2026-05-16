import { useCallback, useRef, useState } from 'react'
import {
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native'
import { SafeAreaView } from 'react-native-safe-area-context'
import {
  AssistantAnswerContent,
  ChatAssistantText,
  ChatComposer,
  ChatMessage,
  ChatUserText,
  DisclaimerCard,
} from '@/components'
import { ASK_INTRO_MESSAGE } from '@/lib/legalCopy'
import { mockAnswer, type MockAnswer } from '@/lib/mockData'
import { colors, spacing, typography } from '@/theme'

type Turn =
  | { id: string; role: 'user'; text: string }
  | { id: string; role: 'assistant'; answer: MockAnswer }
  | { id: string; role: 'assistant'; pending: true }

let turnId = 0
function nextId() {
  turnId += 1
  return `turn-${turnId}`
}

export default function AskScreen() {
  const [draft, setDraft] = useState('')
  const [turns, setTurns] = useState<Turn[]>([])
  const [loading, setLoading] = useState(false)
  const scrollRef = useRef<ScrollView>(null)

  const scrollToEnd = useCallback(() => {
    requestAnimationFrame(() => scrollRef.current?.scrollToEnd({ animated: true }))
  }, [])

  const handleSend = () => {
    const text = draft.trim()
    if (!text || loading) return

    const userTurn: Turn = { id: nextId(), role: 'user', text }
    const pendingId = nextId()
    setDraft('')
    setLoading(true)
    setTurns((prev) => [...prev, userTurn, { id: pendingId, role: 'assistant', pending: true }])
    scrollToEnd()

    setTimeout(() => {
      setTurns((prev) =>
        prev.map((t) =>
          t.id === pendingId && t.role === 'assistant' && 'pending' in t
            ? { id: pendingId, role: 'assistant', answer: mockAnswer }
            : t,
        ),
      )
      setLoading(false)
      scrollToEnd()
    }, 1100)
  }

  return (
    <SafeAreaView style={styles.safe} edges={['bottom']}>
      <KeyboardAvoidingView
        style={styles.flex}
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
        keyboardVerticalOffset={Platform.OS === 'ios' ? 88 : 0}
      >
        <ScrollView
          ref={scrollRef}
          style={styles.messages}
          contentContainerStyle={styles.messagesContent}
          keyboardShouldPersistTaps="handled"
          onContentSizeChange={scrollToEnd}
          showsVerticalScrollIndicator={false}
        >
          <DisclaimerCard compact title="Privacy">
            Questions are not stored on this device or sent to a server in this preview build. Do not enter emergency
            details.
          </DisclaimerCard>

          <ChatMessage role="assistant">
            <ChatAssistantText>{ASK_INTRO_MESSAGE}</ChatAssistantText>
          </ChatMessage>

          {turns.map((turn) => {
            if (turn.role === 'user') {
              return (
                <ChatMessage key={turn.id} role="user">
                  <ChatUserText>{turn.text}</ChatUserText>
                </ChatMessage>
              )
            }
            if ('pending' in turn) {
              return (
                <ChatMessage key={turn.id} role="assistant">
                  <View style={styles.pendingRow}>
                    <ActivityIndicator size="small" color={colors.bronze} />
                    <Text style={styles.pendingText}>Reviewing official-style sources…</Text>
                  </View>
                </ChatMessage>
              )
            }
            return (
              <ChatMessage key={turn.id} role="assistant">
                <AssistantAnswerContent answer={turn.answer} />
              </ChatMessage>
            )
          })}
        </ScrollView>

        <ChatComposer
          value={draft}
          onChangeText={setDraft}
          onSend={handleSend}
          disabled={loading}
          loading={loading}
        />
      </KeyboardAvoidingView>
    </SafeAreaView>
  )
}

const styles = StyleSheet.create({
  safe: {
    flex: 1,
    backgroundColor: colors.creamMuted,
  },
  flex: {
    flex: 1,
  },
  messages: {
    flex: 1,
  },
  messagesContent: {
    padding: spacing.md,
    paddingBottom: spacing.sm,
  },
  pendingRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
  },
  pendingText: {
    fontSize: typography.caption,
    color: colors.textMuted,
    fontStyle: 'italic',
  },
})
