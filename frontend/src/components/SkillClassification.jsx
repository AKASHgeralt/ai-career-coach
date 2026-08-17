import { motion } from 'framer-motion'
import { Check, AlertCircle, X } from 'lucide-react'

const STATUS = {
  MATCHED: {
    label: 'Matched', icon: Check,
    text: 'text-emerald-400', border: 'border-emerald-500/30',
    blurb: 'Found in your resume',
  },
  PARTIAL: {
    label: 'Partial', icon: AlertCircle,
    text: 'text-amber-400', border: 'border-amber-500/30',
    blurb: 'Related experience detected, but not a direct match',
  },
  MISSING: {
    label: 'Missing', icon: X,
    text: 'text-red-400', border: 'border-red-500/30',
    blurb: 'No evidence found — highest priority',
  },
}

const ORDER = ['MISSING', 'PARTIAL', 'MATCHED']

/**
 * Per-skill breakdown of a gap analysis. Similarity is the cosine score from
 * the sentence-transformer comparison; MATCHED skills found by exact name
 * match score 1.0 by definition.
 */
export default function SkillClassification({ details }) {
  if (!details?.length) return null

  const groups = ORDER.map(status => ({
    status,
    ...STATUS[status],
    // Weakest first inside each group, so the most urgent gap reads first.
    skills: details
      .filter(d => d.status === status)
      .sort((a, b) => a.similarity - b.similarity),
  })).filter(g => g.skills.length)

  return (
    <div>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-px bg-line mb-8">
        {ORDER.map(status => {
          const count = details.filter(d => d.status === status).length
          const cfg = STATUS[status]
          return (
            <div key={status} className="bg-ink2 p-5 text-center">
              <div className={`display text-3xl mb-2 ${cfg.text}`}>{count}</div>
              <span className="label">{cfg.label}</span>
            </div>
          )
        })}
      </div>

      <div className="flex flex-col gap-8">
        {groups.map(group => {
          const Icon = group.icon
          return (
            <div key={group.status}>
              <div className="flex items-center gap-2.5 mb-1.5">
                <Icon size={13} className={group.text} />
                <span className={`label !${group.text}`}>
                  {group.label} ({group.skills.length})
                </span>
              </div>
              <p className="text-[11px] text-mistDim mb-4">{group.blurb}</p>

              <div className="flex flex-col">
                {group.skills.map((d, i) => (
                  <motion.div
                    key={d.skill}
                    initial={{ opacity: 0, x: -6 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ duration: 0.25, delay: i * 0.03 }}
                    className="flex items-center gap-5 py-2.5 border-b border-line last:border-b-0"
                  >
                    <span className="text-sm text-mist font-light capitalize flex-1 min-w-0 truncate">
                      {d.skill}
                    </span>
                    <div className="w-28 flex-shrink-0">
                      <div className="meter">
                        <div
                          className="meter-fill"
                          style={{ width: `${Math.round(d.similarity * 100)}%` }}
                        />
                      </div>
                    </div>
                    <span className={`text-[11px] tabular-nums w-10 text-right ${group.text}`}>
                      {Math.round(d.similarity * 100)}%
                    </span>
                  </motion.div>
                ))}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
