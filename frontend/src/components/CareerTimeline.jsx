import { motion } from 'framer-motion'
import { FileText, BarChart2, MessageSquare, GitBranch, CheckSquare, Clock } from 'lucide-react'
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend } from 'recharts'

const KIND = {
  resume: { Icon: FileText, label: 'Resume', colour: '#4da6ff' },
  skills: { Icon: BarChart2, label: 'Skill match', colour: '#8fd0ff' },
  interview: { Icon: MessageSquare, label: 'Interview', colour: '#facc15' },
  github: { Icon: GitBranch, label: 'GitHub', colour: '#34d399' },
  task: { Icon: CheckSquare, label: 'Roadmap', colour: '#a78bfa' },
}

const fmtDate = (iso) =>
  new Date(iso).toLocaleDateString(undefined, { day: '2-digit', month: 'short' })

/** Reverse-chronological list of real recorded career events. */
export default function CareerTimeline({ timeline, loading, limit = 8 }) {
  if (loading) {
    return (
      <div className="bg-ink p-7">
        <div className="h-2.5 w-32 bg-white/[0.06] mb-6 animate-pulse" />
        {[0, 1, 2].map(i => (
          <div key={i} className="h-8 w-full bg-white/[0.03] mb-3 animate-pulse" />
        ))}
      </div>
    )
  }

  const events = timeline?.events || []

  return (
    <div className="bg-ink p-7">
      <div className="flex items-center gap-2.5 mb-7">
        <Clock size={13} className="text-accent" />
        <span className="label">Career timeline</span>
      </div>

      {events.length === 0 ? (
        <p className="text-mistDim text-sm font-light">
          No activity recorded yet. Upload a resume to start your timeline.
        </p>
      ) : (
        <div className="flex flex-col">
          {events.slice(0, limit).map((e, i) => {
            const { Icon, colour } = KIND[e.kind] || KIND.resume
            return (
              <motion.div
                key={`${e.kind}-${e.at}-${i}`}
                initial={{ opacity: 0, x: -6 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.3, delay: i * 0.04 }}
                className="flex gap-4 py-3.5 border-b border-line last:border-b-0"
              >
                <span className="label w-12 flex-shrink-0 pt-0.5">{fmtDate(e.at)}</span>
                <Icon size={13} className="flex-shrink-0 mt-0.5" style={{ color: colour }} />
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-mist font-light">{e.title}</p>
                  {e.detail && (
                    <p className="text-[11px] text-mistDim mt-1 truncate">{e.detail}</p>
                  )}
                </div>
                {e.metric_value !== null && e.metric_value !== undefined && (
                  <div className="text-right flex-shrink-0">
                    <p className="text-sm font-light text-white">{e.metric_value}</p>
                    <p className="text-[10px] text-mistDim uppercase tracking-wider">
                      {e.metric_label}
                    </p>
                  </div>
                )}
              </motion.div>
            )
          })}
        </div>
      )}
    </div>
  )
}

/**
 * Measured signals plotted over time.
 *
 * Only signals with two or more data points are returned by the API, so a
 * single measurement is never drawn as if it were a trend. Readiness itself is
 * absent by design: it's computed live and has never been snapshotted, so a
 * historical line would be fabricated.
 */
export function CareerProgressChart({ timeline, loading }) {
  if (loading) {
    return (
      <div className="bg-ink p-7">
        <div className="h-2.5 w-40 bg-white/[0.06] mb-6 animate-pulse" />
        <div className="h-[200px] w-full bg-white/[0.02] animate-pulse" />
      </div>
    )
  }

  const series = timeline?.series || {}
  const kinds = Object.keys(series)

  if (kinds.length === 0) {
    return (
      <div className="bg-ink p-7">
        <span className="label">Career progress</span>
        <div className="h-[200px] flex items-center justify-center text-center">
          <p className="text-mistDim text-sm font-light max-w-xs">
            Not enough history yet. Once any signal has two or more
            measurements, its trend appears here.
          </p>
        </div>
      </div>
    )
  }

  // Merge every series onto a shared date axis.
  const byDate = new Map()
  for (const kind of kinds) {
    for (const point of series[kind]) {
      const key = fmtDate(point.at)
      const row = byDate.get(key) || { label: key, _t: new Date(point.at).getTime() }
      row[kind] = point.value
      byDate.set(key, row)
    }
  }
  const data = [...byDate.values()].sort((a, b) => a._t - b._t)

  return (
    <div className="bg-ink p-7">
      <div className="mb-6">
        <span className="label">Career progress</span>
        <p className="text-mistDim text-xs font-light mt-2">
          Measured signals over time — {kinds.length} with enough history to plot
        </p>
      </div>
      <ResponsiveContainer width="100%" height={220}>
        <LineChart data={data}>
          <XAxis dataKey="label" tick={{ fill: '#5c748f', fontSize: 10 }} axisLine={false} tickLine={false} />
          <YAxis domain={[0, 100]} tick={{ fill: '#5c748f', fontSize: 10 }} axisLine={false} tickLine={false} />
          <Tooltip
            contentStyle={{
              background: '#060d1a',
              border: '1px solid rgba(125,190,255,0.26)',
              borderRadius: 0,
              color: '#e6f0fb',
              fontSize: 12,
              fontWeight: 300,
            }}
          />
          <Legend
            wrapperStyle={{ fontSize: 11, color: '#9db4cd', fontWeight: 300 }}
            formatter={(value) => KIND[value]?.label || value}
          />
          {kinds.map(kind => (
            <Line
              key={kind}
              type="monotone"
              dataKey={kind}
              stroke={KIND[kind]?.colour || '#4da6ff'}
              strokeWidth={1.5}
              dot={{ r: 2.5 }}
              connectNulls
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
