import { useEffect, useRef, type ReactNode } from 'react'
import { Animated, type ViewStyle } from 'react-native'

export function FadeIn({
  children,
  delay = 0,
  style,
}: {
  children: ReactNode
  delay?: number
  style?: ViewStyle
}) {
  const opacity = useRef(new Animated.Value(0)).current
  const translateY = useRef(new Animated.Value(14)).current

  useEffect(() => {
    Animated.parallel([
      Animated.timing(opacity, {
        toValue: 1,
        duration: 480,
        delay,
        useNativeDriver: true,
      }),
      Animated.timing(translateY, {
        toValue: 0,
        duration: 520,
        delay,
        useNativeDriver: true,
      }),
    ]).start()
  }, [delay, opacity, translateY])

  return (
    <Animated.View style={[style, { opacity, transform: [{ translateY }] }]}>
      {children}
    </Animated.View>
  )
}
