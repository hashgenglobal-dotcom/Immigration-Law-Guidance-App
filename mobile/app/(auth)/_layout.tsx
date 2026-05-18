import { Redirect, Stack } from 'expo-router'
import { useAuth } from '@/context/AuthContext'

export default function AuthLayout() {
  const { session } = useAuth()

  if (session?.mode === 'user') {
    return <Redirect href="/(main)" />
  }

  return (
    <Stack
      screenOptions={{
        headerShown: false,
        animation: 'fade',
        contentStyle: { backgroundColor: '#1F2839' },
      }}
    />
  )
}
