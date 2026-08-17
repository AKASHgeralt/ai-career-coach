import { useState } from 'react'
import { motion } from 'framer-motion'
import { TrendingUp, TrendingDown, Minus, GitCompare, Check, X, Loader, ArrowRight } from 'lucide-react'
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'

const deltaTone = (d) =>
  d > 0 ? 'text-emerald-400' : d < 0 ? 'text-red-400' : 'text-mistDim'

const DeltaIcon = ({ delta, size = 12 }) => {
  const Icon = delta > 0 ? TrendingUp : delta < 0 ? TrendingDown : Minus
  return <Icon size={size} className={deltaTone(delta)} />
}

/** ATS score across resume versions. Only rendered with 2+ versions. */
export function VersionChart({ history }) {
  if (!history || history.count < 2) return null

  const data = history.versions.map(v => ({
    label: `v${v.version}`,
    score: v.ats_score,
    file: v.file_name,
  }))
  const improvement = history.improvement ?? 0

  return (
    <div className="panel ticked p-8 mb-8">
      <div className="flex items-start justify-between mb-7 flex-wrap gap-4">
        <div>
          <span className="label">Resume improvement</span>
          <p className="text-mistDim text-xs font-light mt-2">
            ATS score across {history.count} versions
          </p>
        </div>
        <div className="text-right">
          <div className={`display text-3xl ${deltaTone(improvement)}`}>
            {improvement > 0 ? '+' : ''}{improvement}
          </div>
          <span className="label mt-1 block">Since v1</span>
        </div>
      </div>

      <ResponsiveContainer width="100%" height={190}>
        <AreaChart data={data}>
          <defs>
            <linearGradient id="versionGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#4da6ff" stopOpacity={0.35} />
              <stop offset="95%" stopColor="#4da6ff" stopOpacity={0} />
            </linearGradient>
          </defs>
          <XAxis dataKey="label" tick={{ fill: '#5c748f', fontSize: 11 }} axisLine={false} tickLine={false} />
          <YAxis domain={[0, 100]} tick={{ fill: '#5c748f', fontSize: 10 }} axisLine={false} tickLine={false} />
          <Tooltip
            contentStyle={{
              background: '#060d1a',
              border: '1px solid rgba(125,190,255,0.26)',
              borderRadius: 0, color: '#e6f0fb', fontSize: 12, fontWeight: 300,
            }}
            formatter={(value, _n, p) => [value, p.payload.file]}
          />
          <Area type="monotone" dataKey="score" stroke="#4da6ff" strokeWidth={1.5} fill="url(#versionGrad)" dot={{ r: 3 }} />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  )
}

/** Version picker plus the resulting comparison. */
export default function VersionCompare({ history, comparison, onCompare, loading, error }) {
  const [base, setBase] = useState('')
  const [target, setTarget] = useState('')

  if (!history || history.count < 2) return null

  const canCompare = base && target && base !== target

  return (
    <div className="panel ticked p-8 mb-8">
      <div className="flex items-center gap-2.5 mb-6">
        <GitCompare size={14} className="text-accent" />
        <span className="label">Compare versions</span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        {[
          { value: base, set: setBase, label: 'From', exclude: target },
          { value: target, set: setTarget, label: 'To', exclude: base },
        ].map(({ value, set, label, exclude }) => (
          <div key={label}>
            <label className="label block mb-2.5">{label}</label>
            <select
              value={value}
              onChange={e => set(e.target.value)}
              className="field w-full px-4 py-3.5 text-sm font-light"
            >
              <option value="" className="bg-ink2">Choose a version…</option>
              {history.versions
                .filter(v => v.id !== exclude)
                .map(v => (
                  <option key={v.id} value={v.id} className="bg-ink2">
                    v{v.version} — {v.file_name} (ATS {v.ats_score})
                  </option>
                ))}
            </select>
          </div>
        ))}
        <div className="flex items-end">
          <motion.button
            whileTap={{ scale: 0.97 }}
            onClick={() => onCompare(base, target)}
            disabled={!canCompare || loading}
            className="btn-primary w-full text-xs uppercase tracking-[0.18em] px-6 py-3.5 flex items-center justify-center gap-2.5"
          >
            {loading
              ? <><Loader size={13} className="animate-spin" /> Comparing…</>
              : <>Compare <ArrowRight size={13} /></>}
          </motion.button>
        </div>
      </div>

      {error && (
        <p className="text-red-300 text-xs font-light mb-4">{error}</p>
      )}

      {comparison && <ComparisonResult comparison={comparison} />}
    </div>
  )
}

function ComparisonResult({ comparison }) {
  const {
    base, target, ats_delta, skills_gained = [], skills_lost = [],
    still_missing = [], categories = [], summary,
  } = comparison

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="pt-7 border-t border-line"
    >
      {/* Headline */}
      <div className="flex items-center justify-between gap-6 mb-6 flex-wrap">
        <div className="flex items-center gap-5">
          <div className="text-center">
            <div className="display text-3xl text-white">{base.ats_score}</div>
            <span className="label mt-1 block">v{base.version}</span>
          </div>
          <ArrowRight size={16} className="text-mistDim" />
          <div className="text-center">
            <div className="display text-3xl text-white">{target.ats_score}</div>
            <span className="label mt-1 block">v{target.version}</span>
          </div>
        </div>
        <div className={`flex items-center gap-2.5 ${deltaTone(ats_delta)}`}>
          <DeltaIcon delta={ats_delta} size={16} />
          <span className="display text-3xl">
            {ats_delta > 0 ? '+' : ''}{ats_delta}
          </span>
        </div>
      </div>

      <p className="text-mist text-xs font-light leading-relaxed mb-8">{summary}</p>

      {/* Skill movement */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-px bg-line mb-8">
        {[
          { title: 'What improved', items: skills_gained, Icon: Check, tone: 'text-emerald-400',
            border: 'border-emerald-500/30', text: 'text-emerald-300',
            empty: 'No new skills detected in the newer version.' },
          { title: 'No longer detected', items: skills_lost, Icon: X, tone: 'text-red-400',
            border: 'border-red-500/30', text: 'text-red-300',
            empty: 'Nothing was dropped — good.' },
          { title: 'Still missing', items: still_missing, Icon: Minus, tone: 'text-amber-400',
            border: 'border-amber-500/30', text: 'text-amber-300',
            empty: 'Nothing outstanding for your target role.' },
        ].map(({ title, items, Icon, tone, border, text, empty }) => (
          <div key={title} className="bg-ink p-6">
            <div className="flex items-center gap-2.5 mb-5">
              <Icon size={12} className={tone} />
              <span className="label">{title}</span>
              {items.length > 0 && (
                <span className="text-[10px] text-mistDim ml-auto">{items.length}</span>
              )}
            </div>
            {items.length === 0 ? (
              <p className="text-mistDim text-[11px] font-light">{empty}</p>
            ) : (
              <div className="flex flex-wrap gap-2">
                {items.map(skill => (
                  <span key={skill} className={`text-[11px] border ${border} ${text} px-2.5 py-1 capitalize font-light`}>
                    {skill}
                  </span>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Category movement */}
      <span className="label">ATS categories</span>
      <div className="flex flex-col mt-5">
        {categories.map(c => (
          <div key={c.key} className="flex items-center gap-5 py-3 border-b border-line last:border-b-0">
            <span className="text-sm text-mist font-light w-28 flex-shrink-0">{c.label}</span>
            <div className="meter flex-1">
              <div className="meter-fill" style={{ width: `${(c.after / c.max) * 100}%` }} />
            </div>
            <span className="text-[11px] text-mistDim w-20 text-right flex-shrink-0">
              {c.before} → {c.after}/{c.max}
            </span>
            <span className={`text-[11px] w-12 text-right flex-shrink-0 flex items-center justify-end gap-1.5 ${deltaTone(c.delta)}`}>
              {c.delta !== 0 && <DeltaIcon delta={c.delta} size={10} />}
              {c.delta > 0 ? '+' : ''}{c.delta !== 0 ? c.delta : '—'}
            </span>
          </div>
        ))}
      </div>
    </motion.div>
  )
}
