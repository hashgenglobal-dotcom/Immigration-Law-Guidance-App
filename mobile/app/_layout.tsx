import { Stack } from 'expo-router'
import { StatusBar } from 'expo-status-bar'
import { colors } from '@/theme'

export default function RootLayout() {
  return (
    <>
      <StatusBar style="light" />
      <Stack
        screenOptions={{
          headerStyle: { backgroundColor: colors.primary },
          headerTintColor: colors.white,
          headerTitleStyle: { fontWeight: '700' },
          contentStyle: { backgroundColor: colors.background },
        }}
      >
        <Stack.Screen name="index" options={{ title: 'Immigration Law Guidance' }} />
        <Stack.Screen name="ask" options={{ title: 'Ask a Question' }} />
        <Stack.Screen name="scenarios" options={{ title: 'Scenario Guides' }} />
        <Stack.Screen name="about" options={{ title: 'About' }} />
      </Stack>
    </>
  )
}
