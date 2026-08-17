import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Upload, FileText, Trash2, TrendingUp, X } from 'lucide-react'
import AtsBreakdown from '../components/AtsBreakdown'
import { uploadResume, getResumes, deleteResume, analyzeResume, getVersionHistory, compareVersions } from '../api/resumes'
import VersionCompare, { VersionChart } from '../components/ResumeVersions'

export default function Resumes() {
  const [resumes, setResumes] = useState([])
  const [loading, setLoading] = useState(true)
  const [uploading, setUploading] = useState(false)
  const [analyzing, setAnalyzing] = useState(null)
  const [analysis, setAnalysis] = useState(null)
  const [dragOver, setDragOver] = useState(false)
  const [error, setError] = useState('')
  const [history, setHistory] = useState(null)
  const [comparison, setComparison] = useState(null)
  const [comparing, setComparing] = useState(false)
  const [compareError, setCompareError] = useState('')

  useEffect(() => {
    fetchResumes()
  }, [])

  const fetchResumes = async () => {
    try {
      const data = await getResumes()
      setResumes(data)
      setHistory(await getVersionHistory())
    } catch {
      setError('Failed to load resumes')
    } finally {
      setLoading(false)
    }
  }

  const handleUpload = async (file) => {
    if (!file) return
    if (!file.name.endsWith('.pdf')) {
      setError('Only PDF files allowed')
      return
    }
    setUploading(true)
    setError('')
    try {
      await uploadResume(file)
      await fetchResumes()
    } catch {
      setError('Upload failed. Please try again.')
    } finally {
      setUploading(false)
    }
  }

  const handleDelete = async (id) => {
    try {
      await deleteResume(id)
      setResumes(resumes.filter(r => r.id !== id))
      if (analysis?.resume_id === id) setAnalysis(null)
      if (comparison?.base?.id === id || comparison?.target?.id === id) setComparison(null)
      setHistory(await getVersionHistory())
    } catch {
      setError('Failed to delete resume')
    }
  }

  const handleCompare = async (base, target) => {
    setComparing(true)
    setCompareError('')
    try {
      setComparison(await compareVersions(base, target))
    } catch (err) {
      setComparison(null)
      setCompareError(err.response?.data?.detail || 'Could not compare those versions')
    } finally {
      setComparing(false)
    }
  }

  const handleAnalyze = async (id) => {
    setAnalyzing(id)
    try {
      const data = await analyzeResume(id)
      setAnalysis(data)
    } catch {
      setError('Analysis failed')
    } finally {
      setAnalyzing(null)
    }
  }

  const getScoreColor = (score) => {
    if (score >= 75) return 'text-emerald-400'
    if (score >= 50) return 'text-amber-400'
    return 'text-red-400'
  }

  return (
    <div className="p-5 sm:p-8 lg:p-10">
      <div className="mb-10">
        <span className="label">Documents</span>
        <h1 className="display text-4xl text-white mt-3 mb-2">Resumes</h1>
        <p className="text-mistDim text-sm font-light">
          Upload and analyze your resumes with AI-powered ATS scoring.
        </p>
      </div>

      {error && (
        <div role="alert"
          className="border border-red-500/30 bg-red-500/[0.07] text-red-300 text-sm font-light px-4 py-3 mb-8 flex items-center justify-between">
          {error}
          <button onClick={() => setError('')} aria-label="Dismiss error"><X size={14} /></button>
        </div>
      )}

      {/* Upload zone */}
      <div
        className={`relative border border-dashed p-14 text-center mb-10 transition cursor-pointer dot-grid
          ${dragOver ? 'border-accent bg-accent/[0.05]' : 'border-line2 hover:border-accent/60 hover:bg-accent/[0.02]'}`}
        onDragOver={(e) => { e.preventDefault(); setDragOver(true) }}
        onDragLeave={() => setDragOver(false)}
        onDrop={(e) => {
          e.preventDefault()
          setDragOver(false)
          handleUpload(e.dataTransfer.files[0])
        }}
        onClick={() => document.getElementById('fileInput').click()}
      >
        <input
          id="fileInput"
          type="file"
          accept=".pdf"
          className="hidden"
          onChange={(e) => handleUpload(e.target.files[0])}
        />
        <div className="relative z-10">
          <div className="w-14 h-14 border border-line2 flex items-center justify-center mx-auto mb-6">
            <Upload size={20} className="text-accent" />
          </div>
          {uploading ? (
            <>
              <p className="text-white font-light mb-2">Uploading and analyzing…</p>
              <span className="label">This may take a few seconds</span>
            </>
          ) : (
            <>
              <p className="text-white font-light mb-2">Drop your PDF here or click to browse</p>
              <span className="label">PDF only · Max 5MB · AI-powered ATS scoring</span>
            </>
          )}
        </div>
      </div>

      {/* Resume list */}
      {loading ? (
        <div className="flex flex-col gap-px bg-line mb-10">
          {[0, 1].map(i => (
            <div key={i} className="bg-ink p-6 animate-pulse flex items-center gap-5">
              <div className="w-10 h-10 border border-line flex-shrink-0" />
              <div className="flex-1">
                <div className="h-3 w-40 bg-white/[0.06] mb-3" />
                <div className="h-2 w-24 bg-white/[0.04]" />
              </div>
            </div>
          ))}
        </div>
      ) : resumes.length === 0 ? (
        <div className="panel ticked p-14 text-center mb-10">
          <FileText size={28} className="text-mistDim mx-auto mb-4" />
          <p className="text-mistDim text-sm font-light">
            No resumes uploaded yet. Upload your first resume above!
          </p>
        </div>
      ) : (
        <div className="flex flex-col gap-px bg-line mb-10">
          {resumes.map((resume, i) => (
            <motion.div
              key={resume.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3, delay: i * 0.05 }}
              className="bg-ink p-6 hover:bg-accent/[0.03] transition-colors group"
            >
              <div className="flex items-center gap-5">
                <div className="w-10 h-10 border border-line2 flex items-center justify-center flex-shrink-0">
                  <FileText size={16} className="text-accent" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-white font-light text-sm truncate">{resume.file_name}</p>
                  <p className="text-[11px] text-mistDim mt-1">
                    Uploaded {new Date(resume.uploaded_at).toLocaleDateString()}
                  </p>
                </div>
                <div className="text-right mr-6">
                  <p className={`display text-3xl ${getScoreColor(resume.ats_score)}`}>{resume.ats_score}</p>
                  <span className="label">ATS Score</span>
                </div>
                <div className="flex items-center gap-2.5">
                  <motion.button
                    whileTap={{ scale: 0.96 }}
                    onClick={() => handleAnalyze(resume.id)}
                    disabled={analyzing === resume.id}
                    className="btn-ghost flex items-center gap-2 text-[11px] uppercase tracking-[0.15em] px-4 py-2.5"
                  >
                    <TrendingUp size={12} />
                    {analyzing === resume.id ? 'Analyzing…' : 'Analyze'}
                  </motion.button>
                  <motion.button
                    whileTap={{ scale: 0.96 }}
                    onClick={() => handleDelete(resume.id)}
                    aria-label={`Delete ${resume.file_name}`}
                    className="w-9 h-9 border border-line hover:border-red-500/50 text-mistDim hover:text-red-400 flex items-center justify-center transition"
                  >
                    <Trash2 size={13} />
                  </motion.button>
                </div>
              </div>

              <div className="meter mt-5">
                <div className="meter-fill" style={{ width: `${resume.ats_score}%` }} />
              </div>
            </motion.div>
          ))}
        </div>
      )}

      <VersionChart history={history} />

      <VersionCompare
        history={history}
        comparison={comparison}
        onCompare={handleCompare}
        loading={comparing}
        error={compareError}
      />

      {/* Analysis panel */}
      <AnimatePresence>
      {analysis && (
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -12 }}
          transition={{ duration: 0.3 }}
          className="panel ticked p-8"
        >
          <div className="flex items-center justify-between mb-8">
            <div>
              <span className="label">AI Analysis</span>
              <h2 className="text-lg font-light text-white mt-2">{analysis.file_name}</h2>
            </div>
            <button onClick={() => setAnalysis(null)} aria-label="Close analysis" className="text-mistDim hover:text-white transition">
              <X size={16} />
            </button>
          </div>

          <div className="grid grid-cols-2 lg:grid-cols-4 gap-px bg-line mb-8">
            {[
              { label: 'ATS Score', value: analysis.ats_score },
              { label: 'Skills found', value: analysis.skill_count },
              { label: 'Word count', value: analysis.word_count },
              { label: 'Experience', value: `${analysis.years_of_experience}y` },
            ].map(({ label, value }) => (
              <div key={label} className="bg-ink2 p-6 text-center">
                <div className="display text-3xl text-white mb-2">{value}</div>
                <span className="label">{label}</span>
              </div>
            ))}
          </div>

          {analysis.ats_breakdown && (
            <div className="mb-10 pb-10 border-b border-line">
              <AtsBreakdown breakdown={analysis.ats_breakdown} />
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 gap-10">
            <div>
              <span className="label">Detected skills</span>
              <div className="flex flex-wrap gap-2 mt-4">
                {analysis.skills?.map(skill => (
                  <span
                    key={skill}
                    className="text-[11px] border border-line2 text-accent px-3 py-1.5 capitalize font-light"
                  >
                    {skill}
                  </span>
                ))}
              </div>
            </div>
            <div>
              <span className="label">Education detected</span>
              {analysis.education?.length > 0 ? (
                <div className="flex flex-col gap-2 mt-4">
                  {analysis.education.map((edu, i) => (
                    <p key={i} className="text-xs text-mist font-light border border-line px-4 py-2.5">{edu}</p>
                  ))}
                </div>
              ) : (
                <p className="text-xs text-mistDim font-light mt-4">No education detected</p>
              )}
              {analysis.email && (
                <div className="mt-6">
                  <span className="label">Contact info</span>
                  <p className="text-xs text-mist font-light mt-3">{analysis.email}</p>
                  {analysis.phone && <p className="text-xs text-mist font-light mt-1.5">{analysis.phone}</p>}
                </div>
              )}
            </div>
          </div>
        </motion.div>
      )}
      </AnimatePresence>
    </div>
  )
}
