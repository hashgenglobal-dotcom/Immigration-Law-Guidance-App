import { StyleSheet, View } from 'react-native'
import { ScreenScroll } from '@/components'
import {
  AboutFeatureCard,
  AboutFooter,
  AboutHero,
  AboutSectionTitle,
  LegalNoticeBanner,
} from '@/components/about'
import { DigitalBackdrop, FadeIn } from '@/components/digital'
import { colors, spacing } from '@/theme'

const FEATURES = [
  {
    title: 'What this app does',
    description:
      'Plain-language immigration information, common procedures, and links to official government sources—built for a citation-first experience.',
    icon: 'checkmark-circle' as const,
    accent: 'navy' as const,
  },
  {
    title: 'What this app does not do',
    description:
      'No legal advice, representation, or attorney–client relationship. Does not replace an attorney or handle emergencies.',
    icon: 'close-circle' as const,
    accent: 'bronze' as const,
  },
  {
    title: 'Privacy-first design',
    description:
      'Minimal data collection with strong privacy controls. Answers grounded in retrieved official materials—not model memory alone.',
    icon: 'shield-checkmark' as const,
    accent: 'bronze' as const,
  },
  {
    title: 'Official sources first',
    description:
      'Cites regulations, statutes, and agency guidance you can verify. Always read the linked source and confirm it applies to your facts.',
    icon: 'library' as const,
    accent: 'navy' as const,
  },
] as const

export default function AboutScreen() {
  return (
    <View style={styles.screen}>
      <DigitalBackdrop variant="about" />
      <ScreenScroll contentStyle={styles.scroll}>
        <FadeIn>
          <AboutHero />
        </FadeIn>

        <AboutSectionTitle
          title="Our principles"
          subtitle="How SourcePath earns your trust"
        />

        <View style={styles.grid}>
          {FEATURES.map((feature, i) => (
            <AboutFeatureCard
              key={feature.title}
              index={i + 1}
              title={feature.title}
              description={feature.description}
              icon={feature.icon}
              accent={feature.accent}
            />
          ))}
        </View>

        <LegalNoticeBanner />

        <AboutFooter />
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
    paddingTop: spacing.sm,
    paddingBottom: spacing.xl,
    backgroundColor: 'transparent',
    zIndex: 1,
  },
  grid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
    rowGap: spacing.md,
    columnGap: spacing.sm,
    marginBottom: spacing.xs,
  },
})
