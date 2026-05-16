import { useState } from 'react'
import { StyleSheet, Text, TextInput, View } from 'react-native'
import {
  AnswerSectionCard,
  CitationCard,
  DisclaimerCard,
  LoadingIndicator,
  PrimaryButton,
  ScreenScroll,
} from '@/components'
import { mockAnswer, type MockAnswer } from '@/lib/mockData'
import { colors, spacing, typography } from '@/theme'

const LANGUAGES = [
  { value: 'en', label: 'English' },
  { value: 'es', label: 'Spanish (coming soon)', disabled: true },
  { value: 'zh', label: 'Chinese (coming soon)', disabled: true },
]

export default function AskScreen() {
  const [question, setQuestion] = useState('')
  const [language, setLanguage] = useState('en')
  const [loading, setLoading] = useState(false)
  const [answer, setAnswer] = useState<MockAnswer | null>(null)

  const handleSubmit = () => {
    if (!question.trim() || loading) return
    setLoading(true)
    setAnswer(null)
    // Mock only — no API call, no local storage of questions
    setTimeout(() => {
      setAnswer(mockAnswer)
      setLoading(false)
    }, 1200)
  }

  return (
    <ScreenScroll>
      <DisclaimerCard title="Privacy note">
        Do not enter emergency information. Questions are not stored on this device or sent to a server in this
        mock build.
      </DisclaimerCard>

      <Text style={styles.label}>Your immigration question</Text>
      <TextInput
        style={styles.input}
        value={question}
        onChangeText={setQuestion}
        placeholder="Example: Can I apply for work authorization while my asylum case is pending?"
        placeholderTextColor={colors.textMuted}
        multiline
        textAlignVertical="top"
        editable={!loading}
      />

      <Text style={styles.label}>Language</Text>
      <View style={styles.languageRow}>
        {LANGUAGES.map((lang) => {
          const selected = language === lang.value
          const disabled = 'disabled' in lang && lang.disabled
          return (
            <PrimaryButton
              key={lang.value}
              label={lang.label}
              variant={selected ? 'primary' : 'secondary'}
              disabled={disabled || loading}
              onPress={() => !disabled && setLanguage(lang.value)}
            />
          )
        })}
      </View>

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
    borderRadius: 12,
    padding: spacing.md,
    fontSize: typography.body,
    color: colors.text,
    lineHeight: 24,
  },
  languageRow: {
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
