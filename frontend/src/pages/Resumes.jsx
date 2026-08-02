import { useState, useEffect } from 'react'
import { Upload, FileText, Trash2, Eye, TrendingUp, X } from 'lucide-react'
import { uploadResume, getResumes, deleteResume, analyzeResume } from '../api/resumes'

export default function Resumes() {
  const [resumes, setResumes] = useState([])
  const [loading, setLoading] = useState(true)
  const [uploading, setUploading] = useState(false)
  const [analyzing, setAnalyzing] = useState(null)
  const [analysis, setAnalysis] = useState(null)
  const [dragOver, setDragOver] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    fetchResumes()
  }, [])

  const fetchResumes = async () => {
    try {
      const data = await getResumes()
      setResumes(data)
    } catch (err) {
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
    } catch (err) {
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
    } catch (err) {
      setError('Failed to delete resume')
    }
  }

  const handleAnalyze = async (id) => {
    setAnalyzing(id)
    try {
      const data = await analyzeResume(id)
      setAnalysis(data)
    } catch (err) {
      setError('Analysis failed')
    } finally {
      setAnalyzing(null)
    }
  }

  const getScoreColor = (score) => {
    if (score >= 75) return 'text-green-400'
    if (score >= 50) return 'text-yellow-400'
    return 'text-red-400'
  }

  const getScoreBg = (score) => {
    if (score >= 75) return 'from-green-500 to-emerald-500'
    if (score >= 50) return 'from-yellow-500 to-orange-500'
    return 'from-red-500 to-rose-500'
  }

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white mb-1">Resumes</h1>
        <p className="text-gray-600 text-sm">Upload and analyze your resumes with AI-powered ATS scoring.</p>
      </div>

      {error && (
        <div className="bg-red-500/10 border border-red-500/20 text-red-400 text-sm px-4 py-3 rounded-xl mb-6 flex items-center justify-between">
          {error}
          <button onClick={() => setError('')}><X size={14} /></button>
        </div>
      )}

      {/* Upload zone */}
      <div
        className={`border-2 border-dashed rounded-2xl p-10 text-center mb-8 transition cursor-pointer
          ${dragOver ? 'border-indigo-500 bg-indigo-500/5' : 'border-white/10 hover:border-indigo-500/50'}`}
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
        <div className="w-14 h-14 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center mx-auto mb-4">
          <Upload size={24} className="text-indigo-400" />
        </div>
        {uploading ? (
          <div>
            <p className="text-white font-medium mb-1">Uploading and analyzing...</p>
            <p className="text-gray-600 text-sm">This may take a few seconds</p>
          </div>
        ) : (
          <div>
            <p className="text-white font-medium mb-1">Drop your PDF here or click to browse</p>
            <p className="text-gray-600 text-sm">PDF only · Max 5MB · AI-powered ATS scoring</p>
          </div>
        )}
      </div>

      {/* Resume list */}
      {loading ? (
        <div className="text-gray-600 text-sm">Loading resumes...</div>
      ) : resumes.length === 0 ? (
        <div className="glass rounded-2xl p-10 text-center">
          <FileText size={32} className="text-gray-700 mx-auto mb-3" />
          <p className="text-gray-500 text-sm">No resumes uploaded yet. Upload your first resume above!</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4 mb-8">
          {resumes.map((resume) => (
            <div key={resume.id} className="glass rounded-2xl p-5 card-hover">
              <div className="flex items-center gap-4">
                <div className="w-10 h-10 rounded-xl bg-indigo-500/10 flex items-center justify-center flex-shrink-0">
                  <FileText size={18} className="text-indigo-400" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-white font-medium text-sm truncate">{resume.file_name}</p>
                  <p className="text-gray-600 text-xs mt-0.5">
                    Uploaded {new Date(resume.uploaded_at).toLocaleDateString()}
                  </p>
                </div>
                <div className="text-right mr-4">
                  <p className={`text-2xl font-bold ${getScoreColor(resume.ats_score)}`}>{resume.ats_score}</p>
                  <p className="text-xs text-gray-600">ATS Score</p>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => handleAnalyze(resume.id)}
                    disabled={analyzing === resume.id}
                    className="flex items-center gap-1.5 bg-indigo-600/20 hover:bg-indigo-600/30 text-indigo-300 text-xs px-3 py-2 rounded-lg transition disabled:opacity-50"
                  >
                    <TrendingUp size={13} />
                    {analyzing === resume.id ? 'Analyzing...' : 'Analyze'}
                  </button>
                  <button
                    onClick={() => handleDelete(resume.id)}
                    className="w-8 h-8 rounded-lg bg-red-500/10 hover:bg-red-500/20 text-red-400 flex items-center justify-center transition"
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
              </div>

              {/* Score bar */}
              <div className="mt-4">
                <div className="h-1.5 bg-white/5 rounded-full overflow-hidden">
                  <div
                    className={`h-full bg-gradient-to-r ${getScoreBg(resume.ats_score)} rounded-full transition-all`}
                    style={{ width: `${resume.ats_score}%` }}
                  />
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Analysis panel */}
      {analysis && (
        <div className="glass rounded-2xl p-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-base font-semibold text-white">AI Analysis — {analysis.file_name}</h2>
            <button onClick={() => setAnalysis(null)} className="text-gray-600 hover:text-white transition">
              <X size={16} />
            </button>
          </div>

          <div className="grid grid-cols-4 gap-4 mb-6">
            {[
              { label: 'ATS Score', value: analysis.ats_score },
              { label: 'Skills found', value: analysis.skill_count },
              { label: 'Word count', value: analysis.word_count },
              { label: 'Experience', value: `${analysis.years_of_experience}y` },
            ].map(({ label, value }) => (
              <div key={label} className="bg-white/5 rounded-xl p-4 text-center">
                <div className="text-2xl font-bold text-white mb-1">{value}</div>
                <div className="text-xs text-gray-600">{label}</div>
              </div>
            ))}
          </div>

          <div className="grid grid-cols-2 gap-6">
            <div>
              <h3 className="text-sm font-medium text-white mb-3">Detected skills</h3>
              <div className="flex flex-wrap gap-2">
                {analysis.skills?.map(skill => (
                  <span key={skill} className="text-xs bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 px-2.5 py-1 rounded-lg capitalize">
                    {skill}
                  </span>
                ))}
              </div>
            </div>
            <div>
              <h3 className="text-sm font-medium text-white mb-3">Education detected</h3>
              {analysis.education?.length > 0 ? (
                <div className="flex flex-col gap-2">
                  {analysis.education.map((edu, i) => (
                    <p key={i} className="text-xs text-gray-400 bg-white/5 px-3 py-2 rounded-lg">{edu}</p>
                  ))}
                </div>
              ) : (
                <p className="text-xs text-gray-600">No education detected</p>
              )}
              {analysis.email && (
                <div className="mt-3">
                  <h3 className="text-sm font-medium text-white mb-2">Contact info</h3>
                  <p className="text-xs text-gray-400">{analysis.email}</p>
                  {analysis.phone && <p className="text-xs text-gray-400 mt-1">{analysis.phone}</p>}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}