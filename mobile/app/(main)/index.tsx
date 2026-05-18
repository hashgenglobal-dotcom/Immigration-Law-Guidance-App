import { Pressable, StyleSheet, Text, View } from 'react-native'
import { useRouter } from 'expo-router'
import { ScreenScroll } from '@/components'
import { SessionBanner } from '@/components/auth/SessionBanner'
import { DigitalBackdrop, FadeIn } from '@/components/digital'
import { DisclaimerAccordion, HomeExploreSection, HomeHero } from '@/components/home'
import { colors, spacing, textStyles } from '@/theme'

export default function HomeScreen() {
  const router = useRouter()

  return (
    <View style={styles.screen}>
      <DigitalBackdrop variant="home" />
      <ScreenScroll contentStyle={styles.scroll}>
        <View style={styles.main}>
          <FadeIn>
            <SessionBanner />
          </FadeIn>
          <FadeIn delay={60}>
            <HomeHero onOpenAssistant={() => router.push('/ask')} />
          </FadeIn>

          <HomeExploreSection onNavigate={(route) => router.push(route)} />
        </View>

        <View style={styles.pageEnd}>
          <DisclaimerAccordion />
          <View style={styles.footer}>
            <View style={styles.footerRule} />
            <Pressable
              onPress={() => router.push('/about')}
              style={({ pressed }) => [styles.aboutLink, pressed && styles.aboutPressed]}
              accessibilityRole="link"
            >
              <Text style={styles.aboutText}>About SourcePath</Text>
            </Pressable>
          </View>
        </View>
      </ScreenScroll>
    </View>
  )
}

const styles = StyleSheet.create({
  screen: {
    flex: 1,
    backgroundColor: colors.parchment,
  },
  scroll: {
    flexGrow: 1,
    paddingTop: spacing.md,
    paddingBottom: spacing.xl,
    backgroundColor: 'transparent',
    zIndex: 1,
  },
  main: {
    flexGrow: 1,
  },
  pageEnd: {
    marginTop: spacing.lg,
  },
  footer: {
    alignItems: 'center',
    paddingTop: spacing.md,
  },
  footerRule: {
    alignSelf: 'stretch',
    height: 1,
    backgroundColor: 'rgba(156, 123, 92, 0.2)',
    marginBottom: spacing.md,
  },
  aboutLink: {
    minHeight: 48,
    justifyContent: 'center',
    paddingHorizontal: spacing.md,
  },
  aboutPressed: {
    opacity: 0.65,
  },
  aboutText: {
    ...textStyles.small,
    fontWeight: '600',
    color: colors.brandBronze,
    textAlign: 'center',
  },
})
