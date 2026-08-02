import { useState, useEffect } from 'react'
import { Target, ChevronDown, ChevronUp, Loader, X, Check, BookOpen } from 'lucide-react'
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
    try {
      const data = await analyzeSkillGap(selectedResume, jobTitle, jobDescription)
      setResult(data)
      const gaps = await getSkillGaps(selectedResume)
      setPastGaps(gaps)
    } catch (err) {
      setError('Analysis failed. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const getScoreColor = (score) => {
    if (score >= 70) return 'text-green-400'
    if (score >= 40) return 'text-yellow-400'
    return 'text-red-400'
  }

  const getScoreGradient = (score) => {
    if (score >= 70) return 'from-green-500 to-emerald-500'
    if (score >= 40) return 'from-yellow-500 to-orange-500'
    return 'from-red-500 to-rose-500'
  }

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white mb-1">Skill Gap Analysis</h1>
        <p className="text-gray-600 text-sm">Compare your resume against any job description using AI and vector embeddings.</p>
      </div>

      {error && (
        <div className="bg-red-500/10 border border-red-500/20 text-red-400 text-sm px-4 py-3 rounded-xl mb-6 flex items-center justify-between">
          {error}
          <button onClick={() => setError('')}><X size={14} /></button>
        </div>
      )}

      {/* Input section */}
      <div className="glass rounded-2xl p-6 mb-6">
        <h2 className="text-sm font-semibold text-white mb-4">New Analysis</h2>
        <div className="grid grid-cols-2 gap-4 mb-4">
          <div>
            <label className="text-xs text-gray-500 uppercase tracking-wider mb-1.5 block">Select Resume</label>
            <select
              value={selectedResume}
              onChange={e => setSelectedResume(e.target.value)}
              className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white text-sm focus:outline-none focus:border-indigo-500 transition"
            >
              <option value="" className="bg-gray-900">Choose a resume...</option>
              {resumes.map(r => (
                <option key={r.id} value={r.id} className="bg-gray-900">
                  {r.file_name} (ATS: {r.ats_score})
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="text-xs text-gray-500 uppercase tracking-wider mb-1.5 block">Job Title</label>
            <input
              type="text"
              placeholder="e.g. Backend Engineer"
              value={jobTitle}
              onChange={e => setJobTitle(e.target.value)}
              className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white text-sm focus:outline-none focus:border-indigo-500 transition placeholder-gray-700"
            />
          </div>
        </div>
        <div className="mb-4">
          <label className="text-xs text-gray-500 uppercase tracking-wider mb-1.5 block">Job Description</label>
          <textarea
            rows={5}
            placeholder="Paste the job description here..."
            value={jobDescription}
            onChange={e => setJobDescription(e.target.value)}
            className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white text-sm focus:outline-none focus:border-indigo-500 transition placeholder-gray-700 resize-none"
          />
        </div>
        <button
          onClick={handleAnalyze}
          disabled={loading}
          className="bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white text-sm px-6 py-2.5 rounded-xl transition flex items-center gap-2"
        >
          {loading ? <><Loader size={14} className="animate-spin" /> Analyzing...</> : <><Target size={14} /> Analyze skill gap</>}
        </button>
      </div>

      {/* Result */}
      {result && (
        <div className="glass rounded-2xl p-6 mb-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-base font-semibold text-white">Analysis Result — {result.job_title}</h2>
            <span className={`text-2xl font-bold ${getScoreColor(result.match_score)}`}>
              {result.match_score}%
            </span>
          </div>

          <div className="mb-6">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs text-gray-600">Match score</span>
              <span className={`text-xs font-medium ${getScoreColor(result.match_score)}`}>
                {result.match_score >= 70 ? 'Strong match' : result.match_score >= 40 ? 'Partial match' : 'Low match'}
              </span>
            </div>
            <div className="h-2 bg-white/5 rounded-full overflow-hidden">
              <div
                className={`h-full bg-gradient-to-r ${getScoreGradient(result.match_score)} rounded-full transition-all`}
                style={{ width: `${result.match_score}%` }}
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-6">
            <div>
              <h3 className="text-sm font-medium text-green-400 mb-3 flex items-center gap-2">
                <Check size={14} /> Skills you have ({result.matched_skills?.length})
              </h3>
              <div className="flex flex-wrap gap-2">
                {result.matched_skills?.map(skill => (
                  <span key={skill} className="text-xs bg-green-500/10 border border-green-500/20 text-green-300 px-2.5 py-1 rounded-lg capitalize">
                    {skill}
                  </span>
                ))}
              </div>
            </div>
            <div>
              <h3 className="text-sm font-medium text-red-400 mb-3 flex items-center gap-2">
                <X size={14} /> Skills you're missing ({result.missing_skills?.length})
              </h3>
              <div className="flex flex-wrap gap-2">
                {result.missing_skills?.map(skill => (
                  <span key={skill} className="text-xs bg-red-500/10 border border-red-500/20 text-red-300 px-2.5 py-1 rounded-lg capitalize">
                    {skill}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Past analyses */}
      {pastGaps.length > 0 && (
        <div className="glass rounded-2xl p-6">
          <h2 className="text-sm font-semibold text-white mb-4">Past Analyses</h2>
          <div className="flex flex-col gap-3">
            {pastGaps.map(gap => (
              <div key={gap.id} className="bg-white/5 rounded-xl p-4 flex items-center gap-4">
                <div className="flex-1">
                  <p className="text-sm font-medium text-white">{gap.job_title || 'Untitled'}</p>
                  <p className="text-xs text-gray-600 mt-0.5">{new Date(gap.created_at).toLocaleDateString()}</p>
                </div>
                <div className="text-right">
                  <p className={`text-lg font-bold ${getScoreColor(gap.match_score)}`}>{gap.match_score}%</p>
                  <p className="text-xs text-gray-600">match</p>
                </div>
                <div className="w-24">
                  <div className="h-1.5 bg-white/5 rounded-full overflow-hidden">
                    <div
                      className={`h-full bg-gradient-to-r ${getScoreGradient(gap.match_score)} rounded-full`}
                      style={{ width: `${gap.match_score}%` }}
                    />
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}