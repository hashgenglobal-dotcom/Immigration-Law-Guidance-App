import { Text, StyleSheet, View } from 'react-native'
import { useRouter } from 'expo-router'
import {
  DisclaimerCard,
  PrimaryButton,
  ScreenScroll,
} from '@/components'
import { colors, spacing, typography } from '@/theme'

export default function HomeScreen() {
  const router = useRouter()

  return (
    <ScreenScroll>
      <View style={styles.hero}>
        <Text style={styles.eyebrow}>HashGen Global LLC · MVP</Text>
        <Text style={styles.title}>Immigration Law Guidance</Text>
        <Text style={styles.subtitle}>
          Privacy-first legal information grounded in official sources—not unchecked AI memory.
        </Text>
      </View>

      <DisclaimerCard title="Important">
        {`GENERAL LEGAL INFORMATION, NOT LEGAL ADVICE.\nHIGH-RISK SITUATIONS - TAKE A LEGAL ADVICE FROM ATTORNEY`}
      </DisclaimerCard>

      <View style={styles.actions}>
        <PrimaryButton label="Ask a Question" onPress={() => router.push('/ask')} />
        <PrimaryButton
          label="Browse Scenarios"
          variant="secondary"
          onPress={() => router.push('/scenarios')}
        />
        <PrimaryButton label="About" variant="secondary" onPress={() => router.push('/about')} />
      </View>

      <Text style={styles.footer}>
        This app does not provide legal advice and does not replace an immigration attorney.
      </Text>
    </ScreenScroll>
  )
}

const styles = StyleSheet.create({
  hero: {
    backgroundColor: colors.primary,
    borderRadius: 16,
    padding: spacing.lg,
    marginBottom: spacing.lg,
  },
  eyebrow: {
    fontSize: typography.caption,
    fontWeight: '600',
    color: '#bfdbfe',
    letterSpacing: 1,
    textTransform: 'uppercase',
    marginBottom: spacing.sm,
  },
  title: {
    fontSize: typography.title,
    fontWeight: '800',
    color: colors.white,
    marginBottom: spacing.sm,
  },
  subtitle: {
    fontSize: typography.body,
    lineHeight: 24,
    color: '#e0e7ff',
  },
  actions: {
    marginTop: spacing.lg,
    marginBottom: spacing.md,
  },
  footer: {
    fontSize: typography.small,
    lineHeight: 22,
    color: colors.textMuted,
    textAlign: 'center',
    marginTop: spacing.md,
  },
})
