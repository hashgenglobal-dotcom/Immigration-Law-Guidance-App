import { useState } from 'react'
import {
  LayoutAnimation,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  UIManager,
  View,
} from 'react-native'
import { Ionicons } from '@expo/vector-icons'
import { LEGAL_DISCLAIMER_FULL, LEGAL_DISCLAIMER_SHORT } from '@/lib/legalCopy'
import { colors, fontFamily, radii, spacing, textStyles } from '@/theme'

if (Platform.OS === 'android' && UIManager.setLayoutAnimationEnabledExperimental) {
  UIManager.setLayoutAnimationEnabledExperimental(true)
}

const EXPANDED_SCROLL_MAX_HEIGHT = 200

export function DisclaimerAccordion() {
  const [expanded, setExpanded] = useState(false)

  const toggle = () => {
    LayoutAnimation.configureNext(LayoutAnimation.Presets.easeInEaseOut)
    setExpanded((v) => !v)
  }

  return (
    <View style={styles.wrap}>
      <Pressable
        onPress={toggle}
        accessibilityRole="button"
        accessibilityState={{ expanded }}
        style={({ pressed }) => [styles.banner, pressed && styles.bannerPressed]}
      >
        <View style={styles.row}>
          <View style={styles.iconCircle}>
            <Ionicons name="information-circle" size={20} color={colors.brandBronze} />
          </View>
          <View style={styles.textCol}>
            <Text style={styles.heading}>Important Information</Text>
            {!expanded ? (
              <Text style={styles.preview} numberOfLines={2}>
                {LEGAL_DISCLAIMER_SHORT}
              </Text>
            ) : null}
          </View>
          <Ionicons
            name={expanded ? 'chevron-up' : 'chevron-down'}
            size={18}
            color={colors.textMuted}
            style={styles.chevron}
          />
        </View>
        {!expanded ? <Text style={styles.tapHint}>Tap to read full disclaimer</Text> : null}
      </Pressable>

      {expanded ? (
        <ScrollView
          style={styles.expandedScroll}
          contentContainerStyle={styles.expandedContent}
          nestedScrollEnabled
          showsVerticalScrollIndicator
          accessibilityLabel="Full legal disclaimer"
        >
          <Text style={styles.fullText}>{LEGAL_DISCLAIMER_FULL}</Text>
        </ScrollView>
      ) : null}
    </View>
  )
}

const styles = StyleSheet.create({
  wrap: {
    backgroundColor: colors.parchmentTint,
    borderRadius: radii.card,
    overflow: 'hidden',
  },
  banner: {
    padding: spacing.md,
  },
  bannerPressed: {
    opacity: 0.94,
  },
  row: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: spacing.sm,
  },
  iconCircle: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: 'rgba(156, 123, 92, 0.12)',
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 1,
    flexShrink: 0,
  },
  textCol: {
    flex: 1,
    minWidth: 0,
  },
  heading: {
    ...textStyles.caption,
    fontFamily: fontFamily.heading,
    fontWeight: '600',
    color: colors.brandNavy,
    marginBottom: 4,
    letterSpacing: 0.2,
  },
  preview: {
    fontFamily: fontFamily.body,
    fontSize: 12,
    lineHeight: 18,
    color: colors.brandNavy,
  },
  chevron: {
    marginTop: 2,
    flexShrink: 0,
  },
  tapHint: {
    marginTop: spacing.sm,
    marginLeft: 32 + spacing.sm,
    fontFamily: fontFamily.body,
    fontSize: 10,
    lineHeight: 14,
    color: colors.brandNavy,
    opacity: 0.72,
    fontWeight: '400',
  },
  expandedScroll: {
    maxHeight: EXPANDED_SCROLL_MAX_HEIGHT,
    borderTopWidth: 1,
    borderTopColor: 'rgba(31, 40, 57, 0.08)',
  },
  expandedContent: {
    paddingHorizontal: spacing.md,
    paddingBottom: spacing.md,
    paddingTop: spacing.sm,
  },
  fullText: {
    fontFamily: fontFamily.body,
    fontSize: 12,
    lineHeight: 18,
    color: colors.brandNavy,
  },
})
