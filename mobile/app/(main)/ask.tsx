import { useCallback, useRef, useState } from 'react'
import { useAuth } from '@/context/AuthContext'
import { GuestLimitModal } from '@/components/auth/GuestLimitModal'
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
  ChatComposer,
  ChatMessage,
  ChatUserText,
} from '@/components'
import { WelcomeCard } from '@/components/chat'
import { DigitalBackdrop } from '@/components/digital'
import { mockAnswer, type MockAnswer } from '@/lib/mockData'
import { colors, fontFamily, spacing, typography } from '@/theme'

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
  const { isGuest, canSendGuestChat, recordGuestChat } = useAuth()
  const [draft, setDraft] = useState('')
  const [turns, setTurns] = useState<Turn[]>([])
  const [loading, setLoading] = useState(false)
  const [limitModal, setLimitModal] = useState(false)
  const scrollRef = useRef<ScrollView>(null)

  const scrollToEnd = useCallback(() => {
    requestAnimationFrame(() => scrollRef.current?.scrollToEnd({ animated: true }))
  }, [])

  const handleSend = useCallback(async () => {
    const text = draft.trim()
    if (!text || loading) return

    if (isGuest) {
      if (!canSendGuestChat) {
        setLimitModal(true)
        return
      }
      const allowed = await recordGuestChat()
      if (!allowed) {
        setLimitModal(true)
        return
      }
    }

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
  }, [draft, loading, scrollToEnd, isGuest, canSendGuestChat, recordGuestChat])

  const isEmpty = turns.length === 0

  return (
    <SafeAreaView style={styles.safe} edges={['bottom']}>
      <DigitalBackdrop variant="ask" />
      <KeyboardAvoidingView
        style={styles.flex}
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
        keyboardVerticalOffset={Platform.OS === 'ios' ? 88 : 0}
      >
        <ScrollView
          ref={scrollRef}
          style={styles.messages}
          contentContainerStyle={[styles.messagesContent, isEmpty && styles.messagesEmpty]}
          keyboardShouldPersistTaps="handled"
          onContentSizeChange={() => {
            if (!isEmpty) scrollToEnd()
          }}
          showsVerticalScrollIndicator={false}
        >
          {isEmpty ? <WelcomeCard /> : null}

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
                    <ActivityIndicator size="small" color={colors.brandNavy} />
                    <Text style={styles.pendingText}>Reviewing official sources…</Text>
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
          onSuggestionPress={setDraft}
          disabled={loading}
          loading={loading}
        />
      </KeyboardAvoidingView>
      <GuestLimitModal visible={limitModal} onClose={() => setLimitModal(false)} />
    </SafeAreaView>
  )
}

const styles = StyleSheet.create({
  safe: {
    flex: 1,
    backgroundColor: colors.parchment,
  },
  flex: {
    flex: 1,
    zIndex: 1,
  },
  messages: {
    flex: 1,
  },
  messagesContent: {
    padding: spacing.md,
    paddingBottom: spacing.sm,
    flexGrow: 1,
    backgroundColor: colors.parchment,
  },
  messagesEmpty: {
    justifyContent: 'center',
  },
  pendingRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
  },
  pendingText: {
    fontFamily: fontFamily.body,
    fontSize: typography.caption,
    color: colors.brandNavy,
    opacity: 0.65,
    fontStyle: 'italic',
  },
})
