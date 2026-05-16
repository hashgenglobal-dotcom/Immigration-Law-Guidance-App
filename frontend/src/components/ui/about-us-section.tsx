'use client'

import type React from 'react'
import { useEffect, useRef, useState } from 'react'
import Link from 'next/link'
import {
  Scale,
  Shield,
  BookOpen,
  FileText,
  Map,
  Server,
  Users,
  Calendar,
  CheckCircle,
  Sparkles,
  Star,
  ArrowRight,
  Zap,
  TrendingUp,
  Lock,
} from 'lucide-react'
import {
  motion,
  useScroll,
  useTransform,
  useInView,
  useSpring,
  useMotionValueEvent,
  type MotionValue,
  type Variants,
} from 'framer-motion'

const easeOut = [0.16, 1, 0.3, 1] as const

const containerVariants: Variants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.2,
      delayChildren: 0.3,
    },
  },
}

const itemVariants: Variants = {
  hidden: { y: 20, opacity: 0 },
  visible: {
    y: 0,
    opacity: 1,
    transition: { duration: 0.6, ease: easeOut },
  },
}

const pillars = [
  {
    icon: <Scale className="h-6 w-6" />,
    secondaryIcon: <Sparkles className="absolute -right-1 -top-1 h-4 w-4 text-sage-400" />,
    title: 'Citation-first answers',
    description:
      'Every response is designed to trace back to retrieved USCIS guidance, eCFR regulations, and INA provisions—not unchecked model memory.',
    position: 'left' as const,
  },
  {
    icon: <Shield className="h-6 w-6" />,
    secondaryIcon: <CheckCircle className="absolute -right-1 -top-1 h-4 w-4 text-sage-400" />,
    title: 'Privacy-first by design',
    description:
      'We minimize data collection and avoid sending your personal facts to external AI APIs. Questions are not stored by default.',
    position: 'left' as const,
  },
  {
    icon: <BookOpen className="h-6 w-6" />,
    secondaryIcon: <Star className="absolute -right-1 -top-1 h-4 w-4 text-sage-400" />,
    title: 'Plain-language guidance',
    description:
      'Complex immigration rules explained clearly so you can understand rights, deadlines, and next steps before speaking with counsel.',
    position: 'left' as const,
  },
  {
    icon: <Map className="h-6 w-6" />,
    secondaryIcon: <Sparkles className="absolute -right-1 -top-1 h-4 w-4 text-sage-400" />,
    title: 'Scenario guides',
    description:
      'Structured overviews for common situations—from asylum and work authorization to notices to appear and adjustment of status.',
    position: 'right' as const,
  },
  {
    icon: <FileText className="h-6 w-6" />,
    secondaryIcon: <CheckCircle className="absolute -right-1 -top-1 h-4 w-4 text-sage-400" />,
    title: 'Official source links',
    description:
      'Direct paths to authoritative materials you can verify yourself, supporting informed decisions with your attorney.',
    position: 'right' as const,
  },
  {
    icon: <Server className="h-6 w-6" />,
    secondaryIcon: <Star className="absolute -right-1 -top-1 h-4 w-4 text-sage-400" />,
    title: 'Local-first architecture',
    description:
      'Built for on-device or controlled infrastructure with local LLMs and embeddings—keeping sensitive queries off public cloud AI.',
    position: 'right' as const,
  },
]

const stats = [
  { icon: <FileText className="h-6 w-6" />, value: 8, label: 'Title 8 CFR scope', suffix: '+' },
  { icon: <Users className="h-6 w-6" />, value: 6, label: 'Scenario guides', suffix: '+' },
  { icon: <Calendar className="h-6 w-6" />, value: 100, label: 'Privacy commitment', suffix: '%' },
  { icon: <TrendingUp className="h-6 w-6" />, value: 3, label: 'Core principles', suffix: '' },
]

const HERO_IMAGE =
  'https://images.unsplash.com/photo-1450101499163-c8848c66ca85?w=800&q=80&auto=format&fit=crop'

export default function AboutUsSection() {
  const sectionRef = useRef<HTMLDivElement>(null)
  const statsRef = useRef<HTMLDivElement>(null)
  const isInView = useInView(sectionRef, { once: false, amount: 0.1 })
  const isStatsInView = useInView(statsRef, { once: false, amount: 0.3 })

  const { scrollYProgress } = useScroll({
    target: sectionRef,
    offset: ['start end', 'end start'],
  })

  const y1 = useTransform(scrollYProgress, [0, 1], [0, -50])
  const y2 = useTransform(scrollYProgress, [0, 1], [0, 50])
  const rotate1 = useTransform(scrollYProgress, [0, 1], [0, 20])
  const rotate2 = useTransform(scrollYProgress, [0, 1], [0, -20])

  return (
    <section
      id="about-section"
      ref={sectionRef}
      className="relative w-full overflow-hidden bg-gradient-to-b from-cream-200 to-cream-100 px-4 py-24 text-forest-900"
    >
      <motion.div
        className="absolute left-10 top-20 h-64 w-64 rounded-full bg-sage-500/10 blur-3xl"
        style={{ y: y1, rotate: rotate1 }}
        aria-hidden
      />
      <motion.div
        className="absolute bottom-20 right-10 h-80 w-80 rounded-full bg-forest-900/5 blur-3xl"
        style={{ y: y2, rotate: rotate2 }}
        aria-hidden
      />
      <motion.div
        className="absolute left-1/4 top-1/2 h-4 w-4 rounded-full bg-sage-500/30"
        animate={{ y: [0, -15, 0], opacity: [0.5, 1, 0.5] }}
        transition={{ duration: 3, repeat: Infinity, ease: 'easeInOut' }}
        aria-hidden
      />
      <motion.div
        className="absolute bottom-1/3 right-1/4 h-6 w-6 rounded-full bg-sage-300/40"
        animate={{ y: [0, 20, 0], opacity: [0.5, 1, 0.5] }}
        transition={{ duration: 4, repeat: Infinity, ease: 'easeInOut', delay: 1 }}
        aria-hidden
      />

      <motion.div
        className="relative z-10 mx-auto max-w-6xl"
        initial="hidden"
        animate={isInView ? 'visible' : 'hidden'}
        variants={containerVariants}
      >
        <motion.div className="mb-6 flex flex-col items-center" variants={itemVariants}>
          <motion.span
            className="mb-2 flex items-center gap-2 font-medium text-sage-600"
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
          >
            <Zap className="h-4 w-4" />
            OUR MISSION
          </motion.span>
          <h2 className="mb-4 text-center text-4xl font-light md:text-5xl">About Us</h2>
          <motion.div
            className="h-1 bg-sage-500"
            initial={{ width: 0 }}
            animate={{ width: 96 }}
            transition={{ duration: 1, delay: 0.5 }}
          />
        </motion.div>

        <motion.p
          className="mx-auto mb-16 max-w-2xl text-center text-forest-900/80"
          variants={itemVariants}
        >
          HashGen Global LLC is building a privacy-first immigration law information assistant—grounded in official
          sources, designed for clarity, and built so you can verify every citation before relying on it.
        </motion.p>

        <div className="relative grid grid-cols-1 gap-8 md:grid-cols-3">
          <div className="space-y-16">
            {pillars
              .filter((p) => p.position === 'left')
              .map((pillar, index) => (
                <PillarItem key={`left-${pillar.title}`} {...pillar} delay={index * 0.2} direction="left" />
              ))}
          </div>

          <div className="order-first mb-8 flex items-center justify-center md:order-none md:mb-0">
            <motion.div className="relative w-full max-w-xs" variants={itemVariants}>
              <motion.div
                className="overflow-hidden rounded-md shadow-xl"
                initial={{ scale: 0.9, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                transition={{ duration: 0.8, delay: 0.3 }}
                whileHover={{ scale: 1.03, transition: { duration: 0.3 } }}
              >
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  src={HERO_IMAGE}
                  alt="Legal documents and research materials"
                  className="h-full w-full object-cover"
                  width={400}
                  height={500}
                />
                <motion.div
                  className="absolute inset-0 flex items-end justify-center bg-gradient-to-t from-forest-900/60 to-transparent p-4"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ duration: 0.8, delay: 0.9 }}
                >
                  <Link
                    href="/ask"
                    className="flex items-center gap-2 rounded-full bg-cream-50 px-4 py-2 text-sm font-medium text-forest-900 transition hover:bg-cream-100"
                  >
                    Ask a question <ArrowRight className="h-4 w-4" />
                  </Link>
                </motion.div>
              </motion.div>
              <motion.div
                className="absolute inset-0 -m-3 z-[-1] rounded-md border-4 border-sage-300"
                initial={{ opacity: 0, scale: 1.1 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.8, delay: 0.6 }}
                aria-hidden
              />
              <motion.div
                className="absolute -right-8 -top-4 h-16 w-16 rounded-full bg-sage-500/15"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 1, delay: 0.9 }}
                style={{ y: y1 }}
                aria-hidden
              />
              <motion.div
                className="absolute -bottom-6 -left-10 h-20 w-20 rounded-full bg-sage-200/40"
                initial={{ opacity: 0, y: -20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 1, delay: 1.1 }}
                style={{ y: y2 }}
                aria-hidden
              />
            </motion.div>
          </div>

          <div className="space-y-16">
            {pillars
              .filter((p) => p.position === 'right')
              .map((pillar, index) => (
                <PillarItem key={`right-${pillar.title}`} {...pillar} delay={index * 0.2} direction="right" />
              ))}
          </div>
        </div>

        <motion.div
          ref={statsRef}
          className="mt-24 grid grid-cols-1 gap-8 sm:grid-cols-2 lg:grid-cols-4"
          initial="hidden"
          animate={isStatsInView ? 'visible' : 'hidden'}
          variants={containerVariants}
        >
          {stats.map((stat, index) => (
            <StatCounter key={stat.label} {...stat} delay={index * 0.1} />
          ))}
        </motion.div>

        <motion.div
          className="mt-20 flex flex-col items-center justify-between gap-6 rounded-xl bg-forest-900 p-8 text-cream-50 md:flex-row"
          initial={{ opacity: 0, y: 30 }}
          animate={isStatsInView ? { opacity: 1, y: 0 } : { opacity: 0, y: 30 }}
          transition={{ duration: 0.8, delay: 0.5 }}
        >
          <div className="flex-1">
            <h3 className="mb-2 flex items-center gap-2 text-2xl font-medium">
              <Lock className="h-5 w-5 text-sage-400" />
              Ready to explore your options?
            </h3>
            <p className="text-cream-200/85">
              General legal information only—not legal advice. Consult an immigration attorney for your specific case.
            </p>
          </div>
          <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
            <Link href="/ask" className="btn-primary btn-md inline-flex whitespace-nowrap">
              <span className="btn-inner">
                Get started <ArrowRight className="h-4 w-4" />
              </span>
            </Link>
          </motion.div>
        </motion.div>
      </motion.div>
    </section>
  )
}

function PillarItem({
  icon,
  secondaryIcon,
  title,
  description,
  delay,
  direction,
}: {
  icon: React.ReactNode
  secondaryIcon?: React.ReactNode
  title: string
  description: string
  delay: number
  direction: 'left' | 'right'
}) {
  return (
    <motion.div
      className="group flex flex-col"
      variants={itemVariants}
      transition={{ delay }}
      whileHover={{ y: -5, transition: { duration: 0.2 } }}
    >
      <motion.div
        className="mb-3 flex items-center gap-3"
        initial={{ x: direction === 'left' ? -20 : 20, opacity: 0 }}
        animate={{ x: 0, opacity: 1 }}
        transition={{ duration: 0.6, delay: delay + 0.2 }}
      >
        <motion.div
          className="relative rounded-lg bg-sage-500/10 p-3 text-sage-600 transition-colors duration-300 group-hover:bg-sage-500/20"
          whileHover={{ rotate: [0, -8, 8, -4, 0], transition: { duration: 0.5 } }}
        >
          {icon}
          {secondaryIcon}
        </motion.div>
        <h3 className="text-xl font-medium text-forest-900 transition-colors duration-300 group-hover:text-sage-700">
          {title}
        </h3>
      </motion.div>
      <motion.p
        className="pl-12 text-sm leading-relaxed text-forest-900/80"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.6, delay: delay + 0.4 }}
      >
        {description}
      </motion.p>
      <motion.div className="mt-3 pl-12 text-xs font-medium text-sage-600 opacity-0 transition-opacity duration-300 group-hover:opacity-100">
        <span className="flex items-center gap-1">
          Learn more <ArrowRight className="h-3 w-3" />
        </span>
      </motion.div>
    </motion.div>
  )
}

function AnimatedNumber({ value }: { value: MotionValue<number> }) {
  const [display, setDisplay] = useState(0)
  useMotionValueEvent(value, 'change', (latest) => setDisplay(Math.floor(latest)))
  return <>{display}</>
}

function StatCounter({
  icon,
  value,
  label,
  suffix,
  delay,
}: {
  icon: React.ReactNode
  value: number
  label: string
  suffix: string
  delay: number
}) {
  const countRef = useRef(null)
  const isInView = useInView(countRef, { once: false })
  const [hasAnimated, setHasAnimated] = useState(false)

  const springValue = useSpring(0, { stiffness: 50, damping: 10 })

  useEffect(() => {
    if (isInView && !hasAnimated) {
      springValue.set(value)
      setHasAnimated(true)
    } else if (!isInView && hasAnimated) {
      springValue.set(0)
      setHasAnimated(false)
    }
  }, [isInView, value, springValue, hasAnimated])

  const displayValue = useTransform(springValue, (latest) => Math.floor(latest))

  return (
    <motion.div
      className="group flex flex-col items-center rounded-xl bg-cream-50/80 p-6 text-center backdrop-blur-sm transition-colors duration-300 hover:bg-cream-50"
      variants={{
        hidden: { opacity: 0, y: 20 },
        visible: {
          opacity: 1,
          y: 0,
          transition: { duration: 0.6, delay },
        },
      }}
      whileHover={{ y: -5, transition: { duration: 0.2 } }}
    >
      <motion.div
        className="mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-forest-900/5 text-sage-600 transition-colors duration-300 group-hover:bg-sage-500/15"
        whileHover={{ rotate: 360, transition: { duration: 0.8 } }}
      >
        {icon}
      </motion.div>
      <div ref={countRef} className="flex items-center text-3xl font-bold text-forest-900">
        <AnimatedNumber value={displayValue} />
        <span>{suffix}</span>
      </div>
      <p className="mt-1 text-sm text-forest-900/70">{label}</p>
      <motion.div className="mt-3 h-0.5 w-10 bg-sage-500 transition-all duration-300 group-hover:w-16" />
    </motion.div>
  )
}
