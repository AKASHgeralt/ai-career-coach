import { motion } from 'framer-motion'
import { FileText, BarChart2, MessageSquare, GitBranch, Info, ArrowRight } from 'lucide-react'

// Which dashboard section each component's call-to-action should jump to.
const SECTION_FOR = {
  resume: 'Resumes',
  skills: 'Skill Gap',
  interview: 'Interview',
  github: 'GitHub',
}

const ICON_FOR = {
  resume: FileText,
  skills: BarChart2,
  interview: MessageSquare,
  github: GitBranch,
}

const scoreTone = (score) => {
  if (score === null || score === undefined) return 'text-mistDim'
  if (score >= 70) return 'text-emerald-400'
  if (score >= 40) return 'text-amber-400'
  return 'text-red-400'
}

export function ReadinessHero({ readiness, loading }) {
  if (loading) {
    return (
      <div className="panel ticked p-8 mb-px animate-pulse">
        <div className="h-2.5 w-32 bg-white/[0.06] mb-5" />
        <div className="h-14 w-40 bg-white/[0.06] mb-5" />
        <div className="h-2 w-full bg-white/[0.04]" />
      </div>
    )
  }

  if (!readiness) return null

  const { score, explanation, available_count, total_components } = readiness
  const measured = score !== null

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="panel ticked p-8 mb-px"
    >
      <div className="flex items-start justify-between gap-10 flex-wrap">
        <div className="flex-1 min-w-[280px]">
          <span className="label">Career readiness</span>
          <div className="flex items-baseline gap-3 mt-4 mb-6">
            {measured ? (
              <>
                <span className={`display text-7xl ${scoreTone(score)}`}>{score}</span>
                <span className="text-mistDim text-2xl font-extralight">/ 100</span>
              </>
            ) : (
              <span className="display text-5xl text-mistDim">Not measured</span>
            )}
          </div>

          {measured && (
            <div className="meter mb-5">
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${score}%` }}
                transition={{ duration: 0.9, ease: 'easeOut' }}
                className="meter-fill"
              />
            </div>
          )}

          <div className="flex items-start gap-2.5">
            <Info size={13} className="text-accent flex-shrink-0 mt-0.5" />
            <p className="text-mist text-xs font-light leading-relaxed">{explanation}</p>
          </div>
        </div>

        <div className="text-right">
          <span className="label">Signals measured</span>
          <p className="display text-3xl text-white mt-3">
            {available_count}<span className="text-mistDim text-xl"> / {total_components}</span>
          </p>
        </div>
      </div>
    </motion.div>
  )
}

export function ReadinessComponents({ readiness, loading, onNavigate }) {
  if (loading) {
    return (
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-px bg-line mb-px">
        {[0, 1, 2, 3].map(i => (
          <div key={i} className="bg-ink p-7 animate-pulse">
            <div className="h-2.5 w-20 bg-white/[0.06] mb-6" />
            <div className="h-9 w-16 bg-white/[0.06]" />
          </div>
        ))}
      </div>
    )
  }

  if (!readiness) return null

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-px bg-line mb-px">
      {readiness.components.map((c, i) => {
        const Icon = ICON_FOR[c.key]
        return (
          <motion.div
            key={c.key}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.35, delay: i * 0.06 }}
            className="bg-ink p-7 flex flex-col"
          >
            <div className="flex items-center justify-between mb-6">
              <span className="label">{c.label}</span>
              <Icon size={14} className={c.available ? 'text-accent' : 'text-mistDim'} />
            </div>

            {c.available ? (
              <>
                <div className={`display text-4xl mb-2 ${scoreTone(c.score)}`}>{c.score}</div>
                <div className="meter mb-3">
                  <div className="meter-fill" style={{ width: `${c.score}%` }} />
                </div>
                <p className="text-[11px] text-mistDim">
                  {c.effective_weight}% of your score
                </p>
              </>
            ) : (
              <>
                <div className="display text-4xl text-mistDim/40 mb-2">—</div>
                <p className="text-[11px] text-mistDim mb-4 leading-relaxed flex-1">
                  {c.detail}
                </p>
                <button
                  onClick={() => onNavigate?.(SECTION_FOR[c.key])}
                  className="text-[10px] uppercase tracking-[0.15em] text-accent hover:text-accent2 transition flex items-center gap-1.5 text-left"
                >
                  {c.action?.replace(/ to score this\.$/, '')} <ArrowRight size={11} />
                </button>
              </>
            )}
          </motion.div>
        )
      })}
    </div>
  )
}
