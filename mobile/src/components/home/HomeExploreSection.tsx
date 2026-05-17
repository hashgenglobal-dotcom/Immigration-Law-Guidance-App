import { StyleSheet, Text, View } from 'react-native'
import { FadeIn } from '@/components/digital'
import { HomeActionTile } from './HomeActionTile'
import { colors, fontFamily, spacing, typography } from '@/theme'

const ACTIONS = [
  {
    id: 'ask',
    title: 'Ask a question',
    subtitle: 'Chat with the assistant—plain language, citation-first answers.',
    icon: 'chatbubble-ellipses-outline' as const,
    variant: 'secondary' as const,
    route: '/ask' as const,
  },
  {
    id: 'scenarios',
    title: 'Browse scenarios',
    subtitle: 'Step-by-step guides for common immigration situations.',
    icon: 'library-outline' as const,
    variant: 'secondary' as const,
    route: '/scenarios' as const,
  },
] as const

export function HomeExploreSection({
  onNavigate,
}: {
  onNavigate: (route: '/ask' | '/scenarios') => void
}) {
  return (
    <View style={styles.wrap} nativeID="home-explore-section">
      <View style={styles.header}>
        <View style={styles.headerAccent} />
        <View>
          <Text style={styles.eyebrow}>Explore</Text>
          <Text style={styles.title}>Where would you like to go?</Text>
        </View>
      </View>

      <View style={styles.list} accessibilityRole="menu">
        {ACTIONS.map((action, index) => (
          <FadeIn key={action.id} delay={80 + index * 90}>
            <HomeActionTile
              title={action.title}
              subtitle={action.subtitle}
              icon={action.icon}
              variant={action.variant}
              onPress={() => onNavigate(action.route)}
            />
          </FadeIn>
        ))}
      </View>

      {/*
        <section id="future-updates-dashboard" className="flex flex-col gap-4">
          News + login tiles above replace this slot in preview; expand when live.
        </section>
      */}
      <View nativeID="future-updates-dashboard" style={styles.futureAnchor} />
    </View>
  )
}

const styles = StyleSheet.create({
  wrap: {
    marginTop: spacing.lg,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: spacing.sm,
    marginBottom: spacing.md,
  },
  headerAccent: {
    width: 4,
    alignSelf: 'stretch',
    minHeight: 36,
    borderRadius: 2,
    backgroundColor: colors.brandNavy,
  },
  eyebrow: {
    fontFamily: fontFamily.body,
    fontSize: typography.caption,
    fontWeight: '600',
    color: colors.brandBronze,
    textTransform: 'uppercase',
    letterSpacing: 0.8,
    marginBottom: 2,
  },
  title: {
    fontFamily: fontFamily.heading,
    fontSize: typography.h3,
    fontWeight: '600',
    color: colors.brandNavy,
    letterSpacing: -0.2,
  },
  list: {
    gap: spacing.sm + 2,
  },
  futureAnchor: {
    height: 0,
  },
})
