import { motion } from 'framer-motion'
import { Lightbulb } from 'lucide-react'

const tone = (earned, max) => {
  const pct = max ? earned / max : 0
  if (pct >= 1) return 'text-emerald-400'
  if (pct >= 0.5) return 'text-amber-400'
  return 'text-red-400'
}

/**
 * Itemised ATS score. Every number here is deterministic and comes straight
 * from the rule-based scorer — no LLM generated any of it.
 */
export default function AtsBreakdown({ breakdown }) {
  if (!breakdown?.components?.length) return null

  const improvements = breakdown.components.filter(c => c.suggestion)

  return (
    <div>
      <div className="flex items-center justify-between mb-5">
        <span className="label">Score breakdown</span>
        <span className="text-[11px] text-mistDim">
          {breakdown.total} / 100 points
        </span>
      </div>

      <div className="flex flex-col mb-8">
        {breakdown.components.map((c, i) => (
          <motion.div
            key={c.key}
            initial={{ opacity: 0, x: -6 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.25, delay: i * 0.04 }}
            className="py-3 border-b border-line last:border-b-0"
          >
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-mist font-light">{c.label}</span>
              <span className="text-[11px] tabular-nums">
                <span className={tone(c.earned, c.max)}>{c.earned}</span>
                <span className="text-mistDim"> / {c.max}</span>
              </span>
            </div>
            <div className="meter">
              <motion.div
                className="meter-fill"
                initial={{ width: 0 }}
                animate={{ width: `${(c.earned / c.max) * 100}%` }}
                transition={{ duration: 0.5, delay: i * 0.04, ease: 'easeOut' }}
              />
            </div>
          </motion.div>
        ))}
      </div>

      {improvements.length > 0 && (
        <>
          <div className="flex items-center gap-2.5 mb-4">
            <Lightbulb size={13} className="text-accent" />
            <span className="label">How to improve</span>
          </div>
          <div className="flex flex-col gap-3">
            {improvements.map(c => (
              <div key={c.key} className="border border-line px-4 py-3">
                <span className="label block mb-1.5">
                  {c.label} · +{c.max - c.earned} available
                </span>
                <p className="text-xs text-mist font-light leading-relaxed">
                  {c.suggestion}
                </p>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  )
}
