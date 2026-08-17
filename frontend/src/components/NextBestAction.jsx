import { motion } from 'framer-motion'
import { Compass, ArrowRight, AlertTriangle, TrendingUp } from 'lucide-react'

/**
 * The single highest-value thing to do next, with the reasoning shown.
 * "setup" means a signal has no data yet; "improve" means optimising the
 * weakest measured signal.
 */
export default function NextBestAction({ readiness, loading, onNavigate }) {
  if (loading) {
    return (
      <div className="panel ticked p-8 mb-px animate-pulse">
        <div className="h-2.5 w-40 bg-white/[0.06] mb-5" />
        <div className="h-6 w-2/3 bg-white/[0.06] mb-4" />
        <div className="h-3 w-full bg-white/[0.04]" />
      </div>
    )
  }

  const next = readiness?.next_action
  if (!next) return null

  const isSetup = next.priority === 'setup'
  const Icon = isSetup ? AlertTriangle : TrendingUp
  const tone = isSetup ? 'text-amber-400' : 'text-accent'

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay: 0.1 }}
      className="panel ticked p-8 mb-px"
    >
      <div className="flex items-start justify-between gap-10 flex-wrap">
        <div className="flex-1 min-w-[320px]">
          <div className="flex items-center gap-2.5 mb-5">
            <Compass size={13} className="text-accent" />
            <span className="label">What should I do next?</span>
            <span className={`text-[10px] uppercase tracking-[0.15em] border px-2 py-0.5 ml-1
              ${isSetup ? 'border-amber-500/30 text-amber-400' : 'border-line2 text-accent'}`}>
              {isSetup ? 'Set up' : 'Improve'}
            </span>
          </div>

          <h2 className="text-2xl font-light text-white mb-4 leading-snug">
            {next.action}
          </h2>

          <div className="flex items-start gap-2.5 max-w-2xl">
            <Icon size={13} className={`${tone} flex-shrink-0 mt-0.5`} />
            <div>
              <span className="label block mb-1.5">Why</span>
              <p className="text-mist text-xs font-light leading-relaxed">{next.why}</p>
            </div>
          </div>
        </div>

        <button
          onClick={() => onNavigate?.(next.target_section)}
          className="btn-primary text-xs uppercase tracking-[0.18em] px-7 py-3.5 flex items-center gap-2.5 whitespace-nowrap self-center"
        >
          {next.cta_label} <ArrowRight size={13} />
        </button>
      </div>
    </motion.div>
  )
}

/** Roadmap completion. Shows a truthful empty state rather than a fake 0%. */
export function RoadmapProgressCard({ readiness, onNavigate }) {
  const p = readiness?.roadmap_progress
  if (!p) return null

  return (
    <div className="bg-ink p-7">
      <div className="flex items-center justify-between mb-6">
        <span className="label">Roadmap progress</span>
        <button
          onClick={() => onNavigate?.('Roadmap')}
          className="text-[10px] uppercase tracking-[0.15em] text-accent hover:text-accent2 transition flex items-center gap-1.5"
        >
          Open <ArrowRight size={11} />
        </button>
      </div>

      {p.has_roadmap ? (
        <>
          <div className="display text-4xl text-white mb-1">{p.percent}%</div>
          <p className="text-[11px] text-mistDim mb-4">
            {p.completed} of {p.total} tasks complete
          </p>
          <div className="meter">
            <motion.div
              className="meter-fill"
              initial={{ width: 0 }}
              animate={{ width: `${p.percent}%` }}
              transition={{ duration: 0.7, ease: 'easeOut' }}
            />
          </div>
        </>
      ) : (
        <>
          <div className="display text-4xl text-mistDim/40 mb-2">—</div>
          <p className="text-[11px] text-mistDim leading-relaxed">
            No roadmap yet. Generate one from a skill gap analysis to start
            tracking weekly progress.
          </p>
        </>
      )}
    </div>
  )
}

/** Highest-priority missing skills, ranked. Feeds directly from the readiness payload. */
export function TopSkillGaps({ readiness, loading, onNavigate }) {
  if (loading) {
    return (
      <div className="bg-ink p-7">
        <div className="h-2.5 w-32 bg-white/[0.06] mb-6 animate-pulse" />
        {[0, 1, 2].map(i => (
          <div key={i} className="h-3 w-full bg-white/[0.04] mb-4 animate-pulse" />
        ))}
      </div>
    )
  }

  const skills = readiness?.top_missing_skills || []
  const max = skills.length ? Math.max(...skills.map(s => s.count)) : 1

  return (
    <div className="bg-ink p-7">
      <div className="flex items-center justify-between mb-7">
        <div>
          <span className="label">Top skill gaps</span>
          <p className="text-mistDim text-xs font-light mt-2">
            {readiness?.target_role_label
              ? `Most often missing for ${readiness.target_role_label}`
              : 'Based on your skill gap analyses'}
          </p>
        </div>
        {skills.length > 0 && (
          <button
            onClick={() => onNavigate?.('Roadmap')}
            className="text-[10px] uppercase tracking-[0.15em] text-accent hover:text-accent2 transition flex items-center gap-1.5"
          >
            Build roadmap <ArrowRight size={11} />
          </button>
        )}
      </div>

      {skills.length === 0 ? (
        <div className="py-6 text-center">
          <p className="text-mistDim text-sm font-light mb-4">
            No skill gaps identified yet.
          </p>
          <button
            onClick={() => onNavigate?.('Skill Gap')}
            className="text-[10px] uppercase tracking-[0.15em] text-accent hover:text-accent2 transition inline-flex items-center gap-1.5"
          >
            Run a skill gap analysis <ArrowRight size={11} />
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-x-10 gap-y-5">
          {skills.map(({ skill, count }, i) => (
            <motion.div
              key={skill}
              initial={{ opacity: 0, x: -6 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.3, delay: i * 0.05 }}
            >
              <div className="flex items-center justify-between mb-2.5">
                <span className="text-sm text-mist font-light capitalize">
                  <span className="text-mistDim mr-2.5">{String(i + 1).padStart(2, '0')}</span>
                  {skill}
                </span>
                <span className="text-[11px] text-mistDim">
                  {count}× missing
                </span>
              </div>
              <div className="meter">
                <div className="meter-fill" style={{ width: `${(count / max) * 100}%` }} />
              </div>
            </motion.div>
          ))}
        </div>
      )}
    </div>
  )
}
