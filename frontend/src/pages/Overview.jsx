import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Upload } from 'lucide-react'
import { getSummary, getReadiness, getTimeline } from '../api/analytics'
import { ReadinessHero, ReadinessComponents } from '../components/CareerReadiness'
import NextBestAction, { TopSkillGaps, RoadmapProgressCard } from '../components/NextBestAction'
import CareerTimeline, { CareerProgressChart } from '../components/CareerTimeline'
import { PATH_FOR } from './dashboardSections'

/**
 * The dashboard overview. Its own route component rather than a branch inside
 * the layout, so every section — including this one — has a real URL.
 */
export default function Overview() {
  const navigate = useNavigate()
  const [summary, setSummary] = useState(null)
  const [readiness, setReadiness] = useState(null)
  const [timeline, setTimeline] = useState(null)
  const [loading, setLoading] = useState(true)

  // Section CTAs navigate by label, keeping call sites unchanged.
  const go = (label) => navigate(PATH_FOR[label] || '/dashboard')

  useEffect(() => {
    let cancelled = false
    Promise.all([getSummary(), getReadiness(), getTimeline()])
      .then(([summaryData, readinessData, timelineData]) => {
        if (cancelled) return
        setSummary(summaryData)
        setReadiness(readinessData)
        setTimeline(timelineData)
      })
      .catch(() => { if (!cancelled) navigate('/login') })
      .finally(() => { if (!cancelled) setLoading(false) })
    return () => { cancelled = true }
  }, [navigate])

  if (loading) {
    return (
      <div className="p-5 sm:p-8 lg:p-10">
        <div className="panel ticked p-8 mb-px animate-pulse">
          <div className="h-2.5 w-32 bg-white/[0.06] mb-5" />
          <div className="h-14 w-40 bg-white/[0.06]" />
        </div>
      </div>
    )
  }

  return (
      <motion.div className="p-5 sm:p-8 lg:p-10" initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} transition={{ duration: 0.2 }}>
        <div className="flex items-start justify-between mb-10 flex-wrap gap-6">
          <div>
            <div className="flex items-center gap-3">
              <span className="label">Target role</span>
              {summary?.user?.target_role_label ? (
                <span className="text-[11px] uppercase tracking-[0.18em] text-accent border border-line2 px-3 py-1">
                  {summary.user.target_role_label}
                </span>
              ) : (
                <button
                  onClick={() => go('Settings')}
                  className="text-[11px] uppercase tracking-[0.18em] text-amber-400 border border-amber-500/30 px-3 py-1 hover:border-amber-400 transition"
                >
                  Not set — choose one
                </button>
              )}
            </div>
            <h1 className="display text-4xl text-white mt-4">
              Good morning, {summary?.user?.full_name?.split(' ')[0]}
            </h1>
            <p className="text-mistDim text-sm font-light mt-2">
              Here's what's happening with your career today.
            </p>
          </div>
          <motion.button
            whileTap={{ scale: 0.97 }}
            onClick={() => go('Resumes')}
            className="btn-primary text-xs uppercase tracking-[0.18em] px-5 py-3 flex items-center gap-2.5"
          >
            <Upload size={13} /> Upload resume
          </motion.button>
        </div>

        {!summary?.user?.target_role && (
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            className="panel ticked p-7 mb-px flex items-center justify-between gap-6 flex-wrap"
          >
            <div>
              <span className="label !text-amber-400">Set up required</span>
              <p className="text-white font-light mt-2">
                Choose a target role to unlock personalized analysis
              </p>
              <p className="text-mistDim text-xs font-light mt-1.5">
                Your target role drives skill-gap baselines, roadmaps and interview questions.
              </p>
            </div>
            <button
              onClick={() => go('Settings')}
              className="btn-primary text-xs uppercase tracking-[0.18em] px-6 py-3 whitespace-nowrap"
            >
              Choose target role
            </button>
          </motion.div>
        )}

        <ReadinessHero readiness={readiness} />

        <ReadinessComponents readiness={readiness} onNavigate={go} />

        <NextBestAction readiness={readiness} onNavigate={go} />

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-px bg-line">
          <div className="lg:col-span-2">
            <CareerProgressChart timeline={timeline} />
          </div>

          <CareerTimeline timeline={timeline} />

          <RoadmapProgressCard readiness={readiness} onNavigate={go} />

          <div className="lg:col-span-2">
            <TopSkillGaps readiness={readiness} onNavigate={go} />
          </div>
        </div>
      </motion.div>
  )
}
