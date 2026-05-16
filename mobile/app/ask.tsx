import { useState } from 'react'
import { StyleSheet, Text, TextInput, View } from 'react-native'
import {
  AnswerSectionCard,
  Chip,
  ChipRow,
  CitationCard,
  DisclaimerCard,
  LoadingIndicator,
  PrimaryButton,
  ScreenScroll,
} from '@/components'
import { mockAnswer, type MockAnswer } from '@/lib/mockData'
import { colors, radii, spacing, typography } from '@/theme'

const LANGUAGES = [
  { value: 'en', label: 'English' },
  { value: 'es', label: 'Spanish (soon)', disabled: true },
  { value: 'zh', label: 'Chinese (soon)', disabled: true },
] as const

const MAX_CHARS = 500

export default function AskScreen() {
  const [question, setQuestion] = useState('')
  const [language, setLanguage] = useState('en')
  const [loading, setLoading] = useState(false)
  const [answer, setAnswer] = useState<MockAnswer | null>(null)

  const handleSubmit = () => {
    if (!question.trim() || loading) return
    setLoading(true)
    setAnswer(null)
    setTimeout(() => {
      setAnswer(mockAnswer)
      setLoading(false)
    }, 1200)
  }

  const charCount = question.length

  return (
    <ScreenScroll>
      <DisclaimerCard title="Privacy note">
        Do not enter emergency information. Questions are not stored on this device or sent to a server in this mock
        build.
      </DisclaimerCard>

      <Text style={styles.label}>Your immigration question</Text>
      <TextInput
        style={[styles.input, question.trim().length > 0 && styles.inputActive]}
        value={question}
        onChangeText={(t) => setQuestion(t.slice(0, MAX_CHARS))}
        placeholder="Example: Can I apply for work authorization while my asylum case is pending?"
        placeholderTextColor={colors.textMuted}
        multiline
        textAlignVertical="top"
        editable={!loading}
      />
      <Text style={styles.charCount}>
        {charCount}/{MAX_CHARS}
      </Text>

      <Text style={styles.label}>Language</Text>
      <ChipRow>
        {LANGUAGES.map((lang) => (
          <Chip
            key={lang.value}
            label={lang.label}
            selected={language === lang.value}
            disabled={'disabled' in lang && lang.disabled}
            onPress={() => !('disabled' in lang && lang.disabled) && setLanguage(lang.value)}
          />
        ))}
      </ChipRow>

      <PrimaryButton
        label={loading ? 'Processing…' : 'Get information'}
        onPress={handleSubmit}
        disabled={!question.trim() || loading}
      />

      {loading ? <LoadingIndicator /> : null}

      {answer && !loading ? (
        <View style={styles.answer}>
          <AnswerSectionCard title="Short answer">
            <Text style={styles.body}>{answer.shortAnswer}</Text>
          </AnswerSectionCard>

          <AnswerSectionCard title="Simple explanation">
            <Text style={styles.body}>{answer.simpleExplanation}</Text>
          </AnswerSectionCard>

          <AnswerSectionCard title="Possible risks" variant="risks">
            {answer.possibleRisks.map((risk, i) => (
              <Text key={i} style={styles.listItem}>
                • {risk}
              </Text>
            ))}
          </AnswerSectionCard>

          <AnswerSectionCard title="What to do next" variant="steps">
            {answer.whatToDoNext.map((step, i) => (
              <Text key={i} style={styles.listItem}>
                {i + 1}. {step}
              </Text>
            ))}
          </AnswerSectionCard>

          <Text style={styles.sourcesHeading}>Official sources</Text>
          {answer.sources.map((source, i) => (
            <CitationCard key={i} source={source} />
          ))}

          <DisclaimerCard title="Legal disclaimer">{answer.disclaimer}</DisclaimerCard>
        </View>
      ) : null}
    </ScreenScroll>
  )
}

const styles = StyleSheet.create({
  label: {
    fontSize: typography.body,
    fontWeight: '600',
    color: colors.text,
    marginBottom: spacing.sm,
    marginTop: spacing.md,
  },
  input: {
    minHeight: 120,
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderWidth: 1,
    borderRadius: radii.md,
    padding: spacing.md,
    fontSize: typography.body,
    color: colors.text,
    lineHeight: 24,
  },
  inputActive: {
    borderColor: colors.gold,
  },
  charCount: {
    fontSize: typography.caption,
    color: colors.textMuted,
    textAlign: 'right',
    marginTop: spacing.xs,
    marginBottom: spacing.sm,
  },
  answer: {
    marginTop: spacing.md,
  },
  body: {
    fontSize: typography.body,
    lineHeight: 24,
    color: colors.textSecondary,
  },
  listItem: {
    fontSize: typography.body,
    lineHeight: 24,
    color: colors.textSecondary,
    marginBottom: spacing.sm,
  },
  sourcesHeading: {
    fontSize: typography.subheading,
    fontWeight: '700',
    color: colors.text,
    marginBottom: spacing.sm,
    marginTop: spacing.sm,
  },
})
