import { Redirect, Stack } from 'expo-router'
import { GuestStackHeader } from '@/components/auth/GuestStackHeader'
import { useAuth } from '@/context/AuthContext'
import { brand } from '@/lib/brand'
import { colors, fontFamily } from '@/theme'

const memberHeaderOptions = {
  headerStyle: { backgroundColor: colors.brandNavy },
  headerTintColor: colors.onNavy,
  headerTitleStyle: {
    fontFamily: fontFamily.heading,
    fontWeight: '600' as const,
    fontSize: 17,
    color: colors.onNavy,
  },
  headerShadowVisible: true,
  headerBackTitle: 'Back',
}

export default function MainLayout() {
  const { session, onboardingComplete, isGuest } = useAuth()

  if (!session) {
    if (!onboardingComplete) return <Redirect href="/welcome" />
    return <Redirect href="/choice" />
  }

  return (
    <Stack
      screenOptions={{
        contentStyle: { backgroundColor: colors.backgroundBase },
        ...(isGuest
          ? {
              header: (props) => <GuestStackHeader {...props} />,
            }
          : memberHeaderOptions),
      }}
    >
      <Stack.Screen name="index" options={{ title: brand.name }} />
      <Stack.Screen name="ask" options={{ title: 'Ask a question' }} />
      <Stack.Screen name="scenarios" options={{ title: 'Scenario Guides' }} />
      <Stack.Screen name="about" options={{ title: 'About' }} />
    </Stack>
  )
}
