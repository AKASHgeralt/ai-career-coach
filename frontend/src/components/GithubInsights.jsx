import { motion } from 'framer-motion'
import { Check, AlertTriangle, ArrowRight, Info } from 'lucide-react'

/**
 * Strengths / weaknesses / recommended actions.
 *
 * Everything rendered here is derived server-side from repository data GitHub
 * actually returned, so nothing claims knowledge of READMEs, tests or pinned
 * repositories, which are never fetched.
 */
export default function GithubInsights({ insights }) {
  if (!insights) return null

  const { strengths = [], weaknesses = [], actions = [] } = insights
  if (!strengths.length && !weaknesses.length && !actions.length) return null

  const columns = [
    { key: 'strengths', title: 'Strengths', items: strengths, Icon: Check, tone: 'text-emerald-400' },
    { key: 'weaknesses', title: 'Weaknesses', items: weaknesses, Icon: AlertTriangle, tone: 'text-amber-400' },
    { key: 'actions', title: 'Recommended actions', items: actions, Icon: ArrowRight, tone: 'text-accent' },
  ]

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-px bg-line mb-8">
      {columns.map(({ key, title, items, Icon, tone }, ci) => (
        <motion.div
          key={key}
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, delay: ci * 0.06 }}
          className="bg-ink p-7"
        >
          <div className="flex items-center gap-2.5 mb-6">
            <Icon size={13} className={tone} />
            <span className="label">{title}</span>
          </div>

          {items.length === 0 ? (
            <p className="text-mistDim text-xs font-light">
              {key === 'weaknesses'
                ? 'Nothing flagged from the available data.'
                : 'Nothing to show yet.'}
            </p>
          ) : (
            <ul className="flex flex-col">
              {items.map((item, i) => (
                <li
                  key={i}
                  className="flex items-start gap-3 py-3 border-b border-line last:border-b-0"
                >
                  <span className={`w-1 h-1 rounded-full flex-shrink-0 mt-2 ${tone.replace('text-', 'bg-')}`} />
                  <span className="text-mist text-xs font-light leading-relaxed">{item}</span>
                </li>
              ))}
            </ul>
          )}
        </motion.div>
      ))}
    </div>
  )
}

/** Small note explaining where the displayed data came from and when. */
export function SyncStatus({ profile, cacheMinutes = 60 }) {
  if (!profile?.synced_at) return null
  const when = new Date(profile.synced_at)
  return (
    <div className="flex items-start gap-2.5 border border-line px-4 py-3 mb-8">
      <Info size={12} className="text-accent flex-shrink-0 mt-0.5" />
      <p className="text-[11px] text-mistDim font-light leading-relaxed">
        {profile.cached ? 'Showing stored data from ' : 'Synced from GitHub at '}
        {when.toLocaleString()}.
        {profile.cached && ` GitHub data is reused for ${cacheMinutes} minutes to stay within API rate limits — use Refresh to force an update.`}
      </p>
    </div>
  )
}
