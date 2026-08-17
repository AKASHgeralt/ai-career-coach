import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Target, Loader, X, Check, Info } from 'lucide-react'
import SkillClassification from '../components/SkillClassification'
import { getResumes } from '../api/resumes'
import { analyzeSkillGap, getSkillGaps } from '../api/skills'

export default function SkillGap() {
  const [resumes, setResumes] = useState([])
  const [selectedResume, setSelectedResume] = useState('')
  const [jobTitle, setJobTitle] = useState('')
  const [jobDescription, setJobDescription] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [pastGaps, setPastGaps] = useState([])
  const [error, setError] = useState('')
  // A cold backend loads the matching model on first use. Surfacing that after
  // a few seconds stops a legitimate 30s wait from reading as a hung request.
  const [slow, setSlow] = useState(false)

  useEffect(() => {
    getResumes().then(setResumes)
  }, [])

  useEffect(() => {
    if (selectedResume) {
      getSkillGaps(selectedResume).then(setPastGaps).catch(() => {})
    }
  }, [selectedResume])

  const handleAnalyze = async () => {
    if (!selectedResume || !jobDescription.trim()) {
      setError('Please select a resume and enter a job description')
      return
    }
    setLoading(true)
    setError('')
    setResult(null)
    const slowTimer = setTimeout(() => setSlow(true), 4000)
    try {
      const data = await analyzeSkillGap(selectedResume, jobTitle, jobDescription)
      setResult(data)
      const gaps = await getSkillGaps(selectedResume)
      setPastGaps(gaps)
    } catch {
      setError('Analysis failed. Please try again.')
    } finally {
      clearTimeout(slowTimer)
      setSlow(false)
      setLoading(false)
    }
  }

  const getScoreColor = (score) => {
    if (score >= 70) return 'text-emerald-400'
    if (score >= 40) return 'text-amber-400'
    return 'text-red-400'
  }

  return (
    <div className="p-5 sm:p-8 lg:p-10">
      <div className="mb-10">
        <span className="label">Analysis</span>
        <h1 className="display text-4xl text-white mt-3 mb-2">Skill Gap Analysis</h1>
        <p className="text-mistDim text-sm font-light">
          Compare your resume against any job description using AI and vector embeddings.
        </p>
      </div>

      {error && (
        <div role="alert"
          className="border border-red-500/30 bg-red-500/[0.07] text-red-300 text-sm font-light px-4 py-3 mb-8 flex items-center justify-between">
          {error}
          <button onClick={() => setError('')} aria-label="Dismiss error"><X size={14} /></button>
        </div>
      )}

      {/* Input section */}
      <div className="panel ticked p-8 mb-8">
        <span className="label">New Analysis</span>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 mt-6 mb-6">
          <div>
            <label className="label block mb-2.5">Select Resume</label>
            <select
              value={selectedResume}
              onChange={e => setSelectedResume(e.target.value)}
              className="field w-full px-4 py-3.5 text-sm font-light"
            >
              <option value="" className="bg-ink2">Choose a resume…</option>
              {resumes.map(r => (
                <option key={r.id} value={r.id} className="bg-ink2">
                  {r.file_name} (ATS: {r.ats_score})
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="label block mb-2.5">Job Title</label>
            <input
              type="text"
              placeholder="e.g. Backend Engineer"
              value={jobTitle}
              onChange={e => setJobTitle(e.target.value)}
              className="field w-full px-4 py-3.5 text-sm font-light"
            />
          </div>
        </div>
        <div className="mb-6">
          <label className="label block mb-2.5">Job Description</label>
          <textarea
            rows={5}
            placeholder="Paste the job description here…"
            value={jobDescription}
            onChange={e => setJobDescription(e.target.value)}
            className="field w-full px-4 py-3.5 text-sm font-light resize-none"
          />
        </div>
        <motion.button
          whileTap={{ scale: 0.97 }}
          onClick={handleAnalyze}
          disabled={loading}
          className="btn-primary text-xs uppercase tracking-[0.18em] px-7 py-3.5 flex items-center gap-2.5"
        >
          {loading
            ? <><Loader size={13} className="animate-spin" /> Analyzing…</>
            : <><Target size={13} /> Analyze skill gap</>}
        </motion.button>

        {slow && (
          <p className="text-[11px] text-mistDim font-light mt-4 leading-relaxed">
            Still working — the first analysis after a server restart loads the
            semantic matching model, which can take up to 30 seconds. Later
            analyses take under a second.
          </p>
        )}
      </div>

      {/* Result */}
      <AnimatePresence>
      {result && (
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -12 }}
          transition={{ duration: 0.3 }}
          className="panel ticked p-8 mb-8"
        >
          <div className="flex items-start justify-between mb-8">
            <div>
              <span className="label">Analysis Result</span>
              <h2 className="text-lg font-light text-white mt-2">{result.job_title}</h2>
            </div>
            <div className="text-right">
              <span className={`display text-5xl ${getScoreColor(result.match_score)}`}>
                {result.match_score}%
              </span>
            </div>
          </div>

          {result.used_role_fallback && (
            <div className="flex items-start gap-3 border border-line2 bg-accent/[0.04] text-mist text-xs font-light px-4 py-3.5 mb-8">
              <Info size={13} className="flex-shrink-0 mt-0.5 text-accent" />
              <span>
                Your job description didn't mention specific skills, so this compares against
                the typical skill set for "{result.job_title}" instead. Paste the actual job
                posting for a more precise match.
              </span>
            </div>
          )}

          <div className="mb-8">
            <div className="flex items-center justify-between mb-3">
              <span className="label">Match score</span>
              <span className={`text-[11px] uppercase tracking-[0.15em] ${getScoreColor(result.match_score)}`}>
                {result.match_score >= 70 ? 'Strong match' : result.match_score >= 40 ? 'Partial match' : 'Low match'}
              </span>
            </div>
            <div className="meter">
              <div className="meter-fill" style={{ width: `${result.match_score}%` }} />
            </div>
          </div>

          {result.skill_details?.length > 0 ? (
            <SkillClassification details={result.skill_details} />
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-10">
              <div>
                <div className="flex items-center gap-2.5 mb-4">
                  <Check size={13} className="text-emerald-400" />
                  <span className="label !text-emerald-400">
                    Skills you have ({result.matched_skills?.length})
                  </span>
                </div>
                <div className="flex flex-wrap gap-2">
                  {result.matched_skills?.map(skill => (
                    <span key={skill} className="text-[11px] border border-emerald-500/30 text-emerald-300 px-3 py-1.5 capitalize font-light">
                      {skill}
                    </span>
                  ))}
                </div>
              </div>
              <div>
                <div className="flex items-center gap-2.5 mb-4">
                  <X size={13} className="text-red-400" />
                  <span className="label !text-red-400">
                    Skills you're missing ({result.missing_skills?.length})
                  </span>
                </div>
                <div className="flex flex-wrap gap-2">
                  {result.missing_skills?.map(skill => (
                    <span key={skill} className="text-[11px] border border-red-500/30 text-red-300 px-3 py-1.5 capitalize font-light">
                      {skill}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          )}
        </motion.div>
      )}
      </AnimatePresence>

      {/* Past analyses */}
      {pastGaps.length > 0 && (
        <div className="panel p-8">
          <span className="label">Past Analyses</span>
          <div className="flex flex-col mt-6">
            {pastGaps.map((gap, i) => (
              <motion.div
                key={gap.id}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3, delay: i * 0.05 }}
                className="flex items-center gap-6 py-4 border-b border-line last:border-b-0"
              >
                <div className="flex-1">
                  <p className="text-sm font-light text-white">{gap.job_title || 'Untitled'}</p>
                  <p className="text-[11px] text-mistDim mt-1">
                    {new Date(gap.created_at).toLocaleDateString()}
                  </p>
                </div>
                <div className="text-right">
                  <p className={`display text-2xl ${getScoreColor(gap.match_score)}`}>{gap.match_score}%</p>
                  <span className="label">match</span>
                </div>
                <div className="w-28">
                  <div className="meter">
                    <div className="meter-fill" style={{ width: `${gap.match_score}%` }} />
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
