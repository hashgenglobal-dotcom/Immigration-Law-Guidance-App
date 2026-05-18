import { StyleSheet, View } from 'react-native'
import { ScreenScroll } from '@/components'
import {
  AboutFooter,
  AboutHero,
  AboutPrincipleCard,
  AboutPrinciplesPanel,
  AboutSectionTitle,
  LegalNoticeBanner,
} from '@/components/about'
import { AccountActions } from '@/components/auth/AccountActions'
import { DigitalBackdrop, FadeIn } from '@/components/digital'
import { colors, spacing } from '@/theme'

const PRINCIPLES = [
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

        <FadeIn delay={100}>
          <AboutPrinciplesPanel>
            <AboutSectionTitle
              title="Our principles"
              subtitle="How SourcePath earns your trust"
            />
            <View style={styles.principlesList}>
              {PRINCIPLES.map((feature, i) => (
                <FadeIn key={feature.title} delay={160 + i * 70}>
                  <AboutPrincipleCard
                    index={i + 1}
                    title={feature.title}
                    description={feature.description}
                    icon={feature.icon}
                    accent={feature.accent}
                  />
                </FadeIn>
              ))}
            </View>
          </AboutPrinciplesPanel>
        </FadeIn>

        <FadeIn delay={450}>
          <LegalNoticeBanner />
        </FadeIn>

        <FadeIn delay={500}>
          <AccountActions />
        </FadeIn>

        <FadeIn delay={520}>
          <AboutFooter />
        </FadeIn>
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
  principlesList: {
    gap: 2,
  },
})
