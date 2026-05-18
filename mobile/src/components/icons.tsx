import { Ionicons } from '@expo/vector-icons'
import type { ComponentProps } from 'react'
import { colors } from '@/theme'

type IoniconName = ComponentProps<typeof Ionicons>['name']

export function AppIcon({
  name,
  size = 20,
  color = colors.navy,
}: {
  name: IoniconName
  size?: number
  color?: string
}) {
  return <Ionicons name={name} size={size} color={color} />
}
