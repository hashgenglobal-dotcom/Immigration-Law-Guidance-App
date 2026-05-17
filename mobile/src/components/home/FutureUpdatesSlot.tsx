import { StyleSheet, View } from 'react-native'

/**
 * Intentional layout reserve on Home — no UI in preview builds.
 *
 * Planned for live / full product (see #future-updates-dashboard):
 * 1. Immigration law news & updates feed
 * 2. Sign-in — saved docs, personalized reminders, account settings (TBD)
 */
export function FutureUpdatesSlot() {
  return (
    <>
      {/*
        <section id="future-updates-dashboard" className="flex flex-col gap-4">
          <!-- News / updates + login entry — ship when backend is ready -->
        </section>
      */}
      <View
        nativeID="future-updates-dashboard"
        style={styles.slot}
        accessibilityElementsHidden
        importantForAccessibility="no-hide-descendants"
      />
    </>
  )
}

const styles = StyleSheet.create({
  slot: {
    flex: 1,
    minHeight: 32,
  },
})
