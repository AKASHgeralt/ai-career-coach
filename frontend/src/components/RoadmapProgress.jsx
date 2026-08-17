import { motion } from 'framer-motion'
import { Check, Calendar, Loader } from 'lucide-react'

/**
 * Week-by-week roadmap with checkable tasks. Completion is persisted server
 * side; the parent owns the task list and handles optimistic updates.
 */
export default function RoadmapProgress({ tasks, progress, onToggle, pendingId, loading }) {
  if (loading) {
    return (
      <div className="panel ticked p-8 mb-8">
        <div className="h-2.5 w-40 bg-white/[0.06] mb-6 animate-pulse" />
        {[0, 1, 2].map(i => (
          <div key={i} className="h-10 w-full bg-white/[0.03] mb-3 animate-pulse" />
        ))}
      </div>
    )
  }

  if (!tasks?.length) return null

  // Preserve the server's week/position ordering.
  const weeks = []
  for (const task of tasks) {
    let bucket = weeks.find(w => w.week === task.week)
    if (!bucket) {
      bucket = { week: task.week, detail: task.detail, tasks: [] }
      weeks.push(bucket)
    }
    bucket.tasks.push(task)
  }

  return (
    <div className="panel ticked p-8 mb-8">
      <div className="flex items-start justify-between gap-8 mb-8 flex-wrap">
        <div className="flex items-center gap-2.5">
          <Calendar size={14} className="text-accent" />
          <span className="label">Week-by-week plan</span>
        </div>
        <div className="flex items-center gap-5 flex-1 min-w-[220px] max-w-md">
          <div className="meter flex-1">
            <motion.div
              className="meter-fill"
              initial={{ width: 0 }}
              animate={{ width: `${progress?.percent || 0}%` }}
              transition={{ duration: 0.6, ease: 'easeOut' }}
            />
          </div>
          <span className="text-sm font-light text-white whitespace-nowrap">
            {progress?.percent ?? 0}%
            <span className="text-mistDim text-xs ml-2">
              {progress?.completed ?? 0}/{progress?.total ?? 0}
            </span>
          </span>
        </div>
      </div>

      <div className="flex flex-col">
        {weeks.map((bucket, wi) => {
          const done = bucket.tasks.filter(t => t.completed).length
          const pct = Math.round((done / bucket.tasks.length) * 100)
          return (
            <div key={bucket.week} className={wi > 0 ? 'mt-7 pt-7 border-t border-line' : ''}>
              <div className="flex items-center gap-4 mb-4">
                <div className="w-11 h-11 border border-line2 flex items-center justify-center flex-shrink-0 text-[11px] tracking-widest text-accent">
                  W{bucket.week}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-light text-white">
                    {bucket.detail || `Week ${bucket.week}`}
                  </p>
                  <div className="flex items-center gap-3 mt-2">
                    <div className="meter w-32">
                      <div className="meter-fill" style={{ width: `${pct}%` }} />
                    </div>
                    <span className="text-[11px] text-mistDim">
                      {done}/{bucket.tasks.length}
                    </span>
                  </div>
                </div>
              </div>

              <div className="flex flex-col pl-15" style={{ paddingLeft: '3.75rem' }}>
                {bucket.tasks.map(task => (
                  <button
                    key={task.id}
                    onClick={() => onToggle(task)}
                    disabled={pendingId === task.id}
                    aria-pressed={task.completed}
                    className="flex items-start gap-3.5 py-2.5 text-left group disabled:opacity-60"
                  >
                    <span
                      className={`w-4 h-4 border flex items-center justify-center flex-shrink-0 mt-0.5 transition
                        ${task.completed
                          ? 'border-accent bg-accent/20 text-accent'
                          : 'border-line2 text-transparent group-hover:border-accent/60'}`}
                    >
                      {pendingId === task.id
                        ? <Loader size={9} className="animate-spin text-accent" />
                        : <Check size={10} />}
                    </span>
                    <span
                      className={`text-sm font-light transition
                        ${task.completed
                          ? 'text-mistDim line-through'
                          : 'text-mist group-hover:text-white'}`}
                    >
                      {task.title}
                    </span>
                  </button>
                ))}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
