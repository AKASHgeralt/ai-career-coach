import { motion } from 'framer-motion'
import { Check, AlertTriangle, Target, Info } from 'lucide-react'

const tone = (score) => {
  if (score === null || score === undefined) return 'text-mistDim'
  if (score >= 7) return 'text-emerald-400'
  if (score >= 4) return 'text-amber-400'
  return 'text-red-400'
}

/**
 * Per-dimension interview breakdown.
 *
 * Three dimensions are graded because a written answer evidences them.
 * Confidence is intentionally absent — it's a delivery trait and this
 * interview is typed, so scoring it would assert something never measured.
 */
export default function InterviewAnalytics({ analytics }) {
  if (!analytics) return null

  const { dimensions = [], summary, strengths = [], weaknesses = [],
          recommended_practice = [], weakest_dimension } = analytics

  const measured = dimensions.filter(d => d.score !== null && d.score !== undefined)

  return (
    <div className="text-left">
      {/* Dimensions */}
      <div className="mb-8">
        <span className="label">Performance breakdown</span>
        {measured.length === 0 ? (
          <p className="text-mistDim text-xs font-light mt-4">
            This session was graded before dimension scoring was available, so
            only the overall score is shown.
          </p>
        ) : (
          <div className="flex flex-col mt-5">
            {dimensions.map((d, i) => (
              <motion.div
                key={d.key}
                initial={{ opacity: 0, x: -6 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.3, delay: i * 0.07 }}
                className="py-4 border-b border-line last:border-b-0"
              >
                <div className="flex items-baseline justify-between gap-4 mb-2.5">
                  <span className={`text-sm font-light ${d.key === weakest_dimension ? 'text-white' : 'text-mist'}`}>
                    {d.label}
                    {d.key === weakest_dimension && (
                      <span className="label !text-amber-400 ml-3">Focus area</span>
                    )}
                  </span>
                  <span className={`text-sm font-light whitespace-nowrap ${tone(d.score)}`}>
                    {d.score === null || d.score === undefined
                      ? <span className="text-mistDim">Not measured</span>
                      : <>{d.score}<span className="text-mistDim"> / 10</span></>}
                  </span>
                </div>
                <div className="meter">
                  <motion.div
                    className="meter-fill"
                    initial={{ width: 0 }}
                    animate={{ width: `${((d.score || 0) / 10) * 100}%` }}
                    transition={{ duration: 0.6, delay: i * 0.07, ease: 'easeOut' }}
                  />
                </div>
                <p className="text-[11px] text-mistDim mt-2">{d.description}</p>
              </motion.div>
            ))}
          </div>
        )}
      </div>

      {summary && (
        <div className="flex items-start gap-2.5 border border-line px-4 py-3 mb-8">
          <Info size={12} className="text-accent flex-shrink-0 mt-0.5" />
          <p className="text-mist text-xs font-light leading-relaxed">{summary}</p>
        </div>
      )}

      {/* Strengths / weaknesses / practice */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-px bg-line">
        {[
          { title: 'Strengths', items: strengths, Icon: Check, colour: 'text-emerald-400',
            empty: 'No recurring strengths recorded.' },
          { title: 'Weaknesses', items: weaknesses, Icon: AlertTriangle, colour: 'text-amber-400',
            empty: 'No recurring weaknesses recorded.' },
          { title: 'Recommended practice', items: recommended_practice, Icon: Target, colour: 'text-accent',
            empty: 'Complete a graded session to get practice suggestions.' },
        ].map(({ title, items, Icon, colour, empty }) => (
          <div key={title} className="bg-ink p-6">
            <div className="flex items-center gap-2.5 mb-5">
              <Icon size={12} className={colour} />
              <span className="label">{title}</span>
            </div>
            {items.length === 0 ? (
              <p className="text-mistDim text-[11px] font-light">{empty}</p>
            ) : (
              <ul className="flex flex-col">
                {items.map((item, i) => (
                  <li key={i} className="flex items-start gap-2.5 py-2.5 border-b border-line last:border-b-0">
                    <span className={`w-1 h-1 rounded-full flex-shrink-0 mt-2 ${colour.replace('text-', 'bg-')}`} />
                    <span className="text-mist text-xs font-light leading-relaxed">{item}</span>
                  </li>
                ))}
              </ul>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
