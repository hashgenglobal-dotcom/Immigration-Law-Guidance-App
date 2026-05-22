import { useCallback, useRef, useState } from 'react'
import { useAuth } from '@/context/AuthContext'
import { GuestLimitModal } from '@/components/auth/GuestLimitModal'
import {
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native'
import { SafeAreaView } from 'react-native-safe-area-context'
import {
  AssistantChatContent,
  ChatComposer,
  ChatMessage,
  ChatUserText,
} from '@/components'
import { ClarificationOptions, WelcomeCard } from '@/components/chat'
import { DigitalBackdrop } from '@/components/digital'
import { buildConversationPayload } from '@/lib/conversationContext'
import { resolveCategoryFromTypedReply } from '@/lib/guidedIntakeClient'
import {
  ChatApiError,
  sendChatMessage,
  toAssistantContent,
  toClarificationContent,
} from '@/lib/chatApi'
import type { ChatAssistantContent, ChatClarificationContent, ClarificationOption } from '@/types/chat'
import { colors, fontFamily, spacing, typography } from '@/theme'

type Turn =
  | { id: string; role: 'user'; text: string }
  | { id: string; role: 'assistant'; content: ChatAssistantContent }
  | { id: string; role: 'assistant'; clarification: ChatClarificationContent }
  | { id: string; role: 'assistant'; pending: true }
  | { id: string; role: 'assistant'; error: string }

/** In-memory only — never written to AsyncStorage or the backend. */
type PendingClarification = {
  originalMessage: string
}

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
  const [pendingClarification, setPendingClarification] = useState<PendingClarification | null>(
    null,
  )
  const scrollRef = useRef<ScrollView>(null)

  const scrollToEnd = useCallback(() => {
    requestAnimationFrame(() => scrollRef.current?.scrollToEnd({ animated: true }))
  }, [])

  const completeGuestChatIfNeeded = useCallback(async () => {
    if (!isGuest) return
    const allowed = await recordGuestChat()
    if (!allowed) setLimitModal(true)
  }, [isGuest, recordGuestChat])

  const submitChat = useCallback(
    async (
      message: string,
      selectedCategory?: string | null,
      displayUserText?: string,
      priorTurns?: Turn[],
    ) => {
      const text = message.trim()
      if (!text || loading) return

      if (isGuest && !canSendGuestChat) {
        setLimitModal(true)
        return
      }

      const userLabel = displayUserText?.trim() || text
      const userTurn: Turn = { id: nextId(), role: 'user', text: userLabel }
      const pendingId = nextId()
      const conversation = buildConversationPayload(priorTurns ?? turns)
      setLoading(true)
      setTurns((prev) => [...prev, userTurn, { id: pendingId, role: 'assistant', pending: true }])
      scrollToEnd()

      try {
        const response = await sendChatMessage(text, 5, selectedCategory ?? null, conversation)

        if (response.status === 'needs_clarification') {
          setPendingClarification({ originalMessage: text })
          const clarification = toClarificationContent(response)
          setTurns((prev) =>
            prev.map((t) =>
              t.id === pendingId && t.role === 'assistant' && 'pending' in t
                ? { id: pendingId, role: 'assistant', clarification }
                : t,
            ),
          )
          return
        }

        setPendingClarification(null)
        const content = toAssistantContent(response)
        setTurns((prev) =>
          prev.map((t) =>
            t.id === pendingId && t.role === 'assistant' && 'pending' in t
              ? { id: pendingId, role: 'assistant', content }
              : t,
          ),
        )
        await completeGuestChatIfNeeded()
      } catch (err) {
        const errMessage =
          err instanceof ChatApiError
            ? err.message
            : 'Could not connect to the guidance service. Please check the backend and try again.'
        setTurns((prev) =>
          prev.map((t) =>
            t.id === pendingId && t.role === 'assistant' && 'pending' in t
              ? { id: pendingId, role: 'assistant', error: errMessage }
              : t,
          ),
        )
      } finally {
        setLoading(false)
        scrollToEnd()
      }
    },
    [loading, scrollToEnd, isGuest, canSendGuestChat, completeGuestChatIfNeeded, turns],
  )

  const handleSend = useCallback(async () => {
    const text = draft.trim()
    if (!text) return
    setDraft('')

    if (pendingClarification) {
      const { originalMessage } = pendingClarification
      const typedCategory = resolveCategoryFromTypedReply(text)
      setPendingClarification(null)
      if (typedCategory) {
        await submitChat(originalMessage, typedCategory, text, turns)
      } else {
        await submitChat(text, undefined, text, turns)
      }
      return
    }

    await submitChat(text, undefined, undefined, turns)
  }, [draft, submitChat, pendingClarification, turns])

  const startNewConversation = useCallback(() => {
    setTurns([])
    setPendingClarification(null)
    setDraft('')
  }, [])

  const handleClarificationSelect = useCallback(
    async (option: ClarificationOption) => {
      if (!pendingClarification || loading) return
      const { originalMessage } = pendingClarification
      setPendingClarification(null)
      await submitChat(originalMessage, option.value, option.label, turns)
    },
    [pendingClarification, loading, submitChat, turns],
  )

  const isEmpty = turns.length === 0

  return (
    <SafeAreaView style={styles.safe} edges={['bottom']}>
      <DigitalBackdrop variant="ask" />
      <KeyboardAvoidingView
        style={styles.flex}
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
        keyboardVerticalOffset={Platform.OS === 'ios' ? 88 : 0}
      >
        {!isEmpty ? (
          <View style={styles.threadBar}>
            <Pressable
              onPress={startNewConversation}
              style={({ pressed }) => [styles.newChatBtn, pressed && styles.newChatPressed]}
              accessibilityRole="button"
              accessibilityLabel="Start a new conversation"
            >
              <Text style={styles.newChatText}>New conversation</Text>
            </Pressable>
          </View>
        ) : null}

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
            if ('error' in turn) {
              return (
                <ChatMessage key={turn.id} role="assistant">
                  <View style={styles.errorBox}>
                    <Text style={styles.errorText}>{turn.error}</Text>
                  </View>
                </ChatMessage>
              )
            }
            if ('clarification' in turn) {
              return (
                <ChatMessage key={turn.id} role="assistant">
                  <ClarificationOptions
                    intro={turn.clarification.answer}
                    question={turn.clarification.clarifyingQuestion}
                    options={turn.clarification.options}
                    disclaimer={turn.clarification.disclaimer}
                    onSelect={handleClarificationSelect}
                    disabled={loading || !pendingClarification}
                  />
                  {pendingClarification ? (
                    <Text style={styles.clarifyHint}>
                      Or type your situation below (for example, F-1 OPT) and send.
                    </Text>
                  ) : null}
                </ChatMessage>
              )
            }
            return (
              <ChatMessage key={turn.id} role="assistant">
                <AssistantChatContent content={turn.content} />
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
  threadBar: {
    flexDirection: 'row',
    justifyContent: 'flex-end',
    paddingHorizontal: spacing.md,
    paddingTop: spacing.xs,
    zIndex: 1,
  },
  newChatBtn: {
    paddingVertical: spacing.xs,
    paddingHorizontal: spacing.sm,
  },
  newChatPressed: {
    opacity: 0.7,
  },
  newChatText: {
    fontFamily: fontFamily.body,
    fontSize: typography.caption,
    fontWeight: '600',
    color: colors.brandBronze,
  },
  clarifyHint: {
    fontFamily: fontFamily.body,
    fontSize: typography.caption,
    lineHeight: 18,
    color: colors.brandNavy,
    opacity: 0.65,
    marginTop: spacing.sm,
    fontStyle: 'italic',
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
  errorBox: {
    padding: spacing.sm,
    borderRadius: 8,
    backgroundColor: colors.bronzeTint,
    borderLeftWidth: 3,
    borderLeftColor: colors.brandBronze,
  },
  errorText: {
    fontFamily: fontFamily.body,
    fontSize: typography.small,
    lineHeight: 20,
    color: colors.brandNavy,
  },
})
