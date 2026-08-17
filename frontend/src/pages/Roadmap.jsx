import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { BookOpen, Loader, X, Sparkles, ExternalLink, Clock, Layers, GraduationCap } from 'lucide-react'
import { getResumes } from '../api/resumes'
import { getSkillGaps } from '../api/skills'
import { generateRoadmap, getRecommendation, getRoadmapTasks, setTaskCompleted } from '../api/recommendations'
import RoadmapProgress from '../components/RoadmapProgress'

export default function Roadmap() {
  const [resumes, setResumes] = useState([])
  const [selectedResume, setSelectedResume] = useState('')
  const [gaps, setGaps] = useState([])
  const [selectedGap, setSelectedGap] = useState(null)
  const [targetRole, setTargetRole] = useState('')
  const [loadingGaps, setLoadingGaps] = useState(false)
  const [generating, setGenerating] = useState(false)
  const [result, setResult] = useState(null)
  const [tasks, setTasks] = useState([])
  const [progress, setProgress] = useState(null)
  const [pendingTaskId, setPendingTaskId] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    getResumes().then(setResumes).catch(() => {})
  }, [])

  useEffect(() => {
    if (!selectedResume) {
      setGaps([])
      return
    }
    setLoadingGaps(true)
    getSkillGaps(selectedResume)
      .then(setGaps)
      .catch(() => setGaps([]))
      .finally(() => setLoadingGaps(false))
  }, [selectedResume])

  const handleSelectGap = async (gap) => {
    setSelectedGap(gap)
    setTargetRole(gap.job_title || '')
    setResult(null)
    setError('')
    try {
      const existing = await getRecommendation(gap.id)
      setResult(existing)
      await loadTasks(gap.id)
    } catch {
      // no roadmap generated yet for this gap — that's fine
    }
  }

  const loadTasks = async (gapId) => {
    try {
      const data = await getRoadmapTasks(gapId)
      setTasks(data.tasks)
      setProgress(data.progress)
    } catch {
      setTasks([]); setProgress(null)
    }
  }

  // Optimistic: tick immediately, roll back if the server rejects it.
  const handleToggleTask = async (task) => {
    const next = !task.completed
    setPendingTaskId(task.id)
    const updated = tasks.map(t => t.id === task.id ? { ...t, completed: next } : t)
    setTasks(updated)
    try {
      await setTaskCompleted(task.id, next)
      const done = updated.filter(t => t.completed).length
      setProgress(p => p && {
        ...p, completed: done,
        percent: p.total ? Math.round(done / p.total * 1000) / 10 : 0,
      })
    } catch {
      setTasks(prev => prev.map(t => t.id === task.id ? { ...t, completed: !next } : t))
      setError('Could not save that change. Please try again.')
    } finally {
      setPendingTaskId(null)
    }
  }

  const handleGenerate = async () => {
    if (!selectedGap || !targetRole.trim()) {
      setError('Select a skill gap analysis and enter a target role')
      return
    }
    setGenerating(true)
    setError('')
    try {
      const data = await generateRoadmap(selectedGap.id, targetRole)
      setResult(data)
      await loadTasks(selectedGap.id)
    } catch {
      setError('Failed to generate roadmap. Please try again.')
    } finally {
      setGenerating(false)
    }
  }

  return (
    <motion.div
      className="p-5 sm:p-8 lg:p-10"
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, ease: 'easeOut' }}
    >
      <div className="mb-10">
        <span className="label">Planning</span>
        <h1 className="display text-4xl text-white mt-3 mb-2">Learning Roadmap</h1>
        <p className="text-mistDim text-sm font-light">
          Turn any skill gap analysis into personalized courses, projects and a week-by-week plan.
        </p>
      </div>

      {error && (
        <div role="alert"
          className="border border-red-500/30 bg-red-500/[0.07] text-red-300 text-sm font-light px-4 py-3 mb-8 flex items-center justify-between">
          {error}
          <button onClick={() => setError('')} aria-label="Dismiss error"><X size={14} /></button>
        </div>
      )}

      <div className="panel ticked p-8 mb-8">
        <span className="label">01 — Choose a skill gap analysis</span>

        <div className="mt-6 mb-6">
          <label className="label block mb-2.5">Resume</label>
          <select
            value={selectedResume}
            onChange={e => { setSelectedResume(e.target.value); setSelectedGap(null); setResult(null) }}
            className="field w-full px-4 py-3.5 text-sm font-light"
          >
            <option value="" className="bg-ink2">Choose a resume…</option>
            {resumes.map(r => (
              <option key={r.id} value={r.id} className="bg-ink2">{r.file_name}</option>
            ))}
          </select>
        </div>

        {loadingGaps ? (
          <p className="text-mistDim text-sm font-light">Loading past analyses…</p>
        ) : selectedResume && gaps.length === 0 ? (
          <p className="text-mistDim text-sm font-light">
            No skill gap analyses for this resume yet. Run one from the Skill Gap tab first.
          </p>
        ) : gaps.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-px bg-line">
            {gaps.map(gap => (
              <button
                key={gap.id}
                onClick={() => handleSelectGap(gap)}
                className={`text-left p-5 transition
                  ${selectedGap?.id === gap.id
                    ? 'bg-accent/[0.08] text-white'
                    : 'bg-ink hover:bg-accent/[0.03]'}`}
              >
                <p className="text-sm font-light text-white">{gap.job_title || 'Untitled role'}</p>
                <p className="text-[11px] text-mistDim mt-1.5">
                  {gap.missing_skills?.length || 0} missing skills · {gap.match_score}% match
                </p>
              </button>
            ))}
          </div>
        ) : null}

        {selectedGap && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            className="mt-7 pt-7 border-t border-line"
          >
            <label className="label block mb-2.5">Target role</label>
            <div className="flex flex-col sm:flex-row gap-3">
              <input
                type="text"
                placeholder="e.g. Backend Engineer"
                value={targetRole}
                onChange={e => setTargetRole(e.target.value)}
                className="field flex-1 px-4 py-3.5 text-sm font-light"
              />
              <motion.button
                whileTap={{ scale: 0.97 }}
                onClick={handleGenerate}
                disabled={generating}
                className="btn-primary text-xs uppercase tracking-[0.18em] px-7 py-3.5 flex items-center gap-2.5 whitespace-nowrap"
              >
                {generating
                  ? <><Loader size={13} className="animate-spin" /> Generating…</>
                  : <><Sparkles size={13} /> Generate roadmap</>}
              </motion.button>
            </div>
          </motion.div>
        )}
      </div>

      <AnimatePresence>
        {result && (
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -12 }}
            transition={{ duration: 0.35 }}
          >
            <RoadmapProgress
              tasks={tasks}
              progress={progress}
              onToggle={handleToggleTask}
              pendingId={pendingTaskId}
            />

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
              <div className="panel p-8">
                <div className="flex items-center gap-2.5 mb-6">
                  <GraduationCap size={14} className="text-accent" />
                  <span className="label">Courses</span>
                </div>
                <div className="flex flex-col">
                  {result.courses?.map((c, i) => (
                    <a
                      key={i}
                      href={c.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="py-4 border-b border-line last:border-b-0 hover:bg-accent/[0.03] transition block px-2 -mx-2"
                    >
                      <div className="flex items-start justify-between gap-3">
                        <p className="text-sm font-light text-white">{c.title}</p>
                        <ExternalLink size={12} className="text-mistDim flex-shrink-0 mt-1" />
                      </div>
                      <p className="text-[11px] text-mistDim mt-1.5">
                        {c.platform} · {c.level} · {c.duration}
                      </p>
                    </a>
                  ))}
                  {!result.courses?.length && (
                    <p className="text-mistDim text-sm font-light">No courses generated</p>
                  )}
                </div>
              </div>

              <div className="panel p-8">
                <div className="flex items-center gap-2.5 mb-6">
                  <Layers size={14} className="text-accent" />
                  <span className="label">Projects</span>
                </div>
                <div className="flex flex-col">
                  {result.projects?.map((p, i) => (
                    <div key={i} className="py-4 border-b border-line last:border-b-0">
                      <div className="flex items-start justify-between gap-3">
                        <p className="text-sm font-light text-white">{p.title}</p>
                        <span className="text-[11px] text-mistDim flex items-center gap-1.5 flex-shrink-0">
                          <Clock size={10} /> {p.estimated_time}
                        </span>
                      </div>
                      <p className="text-xs text-mist font-light mt-1.5">{p.description}</p>
                      <p className="text-[11px] text-mistDim mt-2">{p.difficulty}</p>
                    </div>
                  ))}
                  {!result.projects?.length && (
                    <p className="text-mistDim text-sm font-light">No projects generated</p>
                  )}
                </div>
              </div>
            </div>

            <div className="panel p-8">
              <div className="flex items-center gap-2.5 mb-6">
                <BookOpen size={14} className="text-accent" />
                <span className="label">Books</span>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-px bg-line">
                {result.books?.map((b, i) => (
                  <div key={i} className="bg-ink p-5">
                    <p className="text-sm font-light text-white">{b.title}</p>
                    <p className="text-[11px] text-mistDim mt-1">{b.author}</p>
                    <p className="text-xs text-mist font-light mt-2.5">{b.why}</p>
                  </div>
                ))}
                {!result.books?.length && (
                  <p className="text-mistDim text-sm font-light">No books generated</p>
                )}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {!result && !selectedGap && gaps.length === 0 && !selectedResume && (
        <div className="panel ticked p-16 text-center">
          <div className="relative z-10">
            <BookOpen size={28} className="text-mistDim mx-auto mb-4" />
            <p className="text-mistDim text-sm font-light">
              Pick a resume and a past skill gap analysis above to generate your personalized roadmap.
            </p>
          </div>
        </div>
      )}
    </motion.div>
  )
}
