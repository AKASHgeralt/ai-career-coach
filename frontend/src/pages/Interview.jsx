import { useState, useEffect } from 'react'
import { MessageSquare, Play, Send, Trophy, ChevronRight, Loader, X } from 'lucide-react'
import { startInterview, submitAnswer, getSessions } from '../api/interview'

export default function Interview() {
  const [phase, setPhase] = useState('setup') // setup | active | complete
  const [jobRole, setJobRole] = useState('')
  const [difficulty, setDifficulty] = useState('medium')
  const [session, setSession] = useState(null)
  const [currentQuestion, setCurrentQuestion] = useState('')
  const [questionNumber, setQuestionNumber] = useState(1)
  const [totalQuestions, setTotalQuestions] = useState(5)
  const [answer, setAnswer] = useState('')
  const [feedback, setFeedback] = useState(null)
  const [loading, setLoading] = useState(false)
  const [pastSessions, setPastSessions] = useState([])
  const [error, setError] = useState('')
  const [finalResult, setFinalResult] = useState(null)

  useEffect(() => {
    getSessions().then(setPastSessions).catch(() => {})
  }, [])

  const handleStart = async () => {
    if (!jobRole.trim()) {
      setError('Please enter a job role')
      return
    }
    setLoading(true)
    setError('')
    try {
      const data = await startInterview(jobRole, difficulty)
      setSession(data)
      setCurrentQuestion(data.question)
      setQuestionNumber(1)
      setTotalQuestions(data.total_questions)
      setPhase('active')
      setFeedback(null)
    } catch (err) {
      setError('Failed to start interview')
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = async () => {
    if (!answer.trim()) {
      setError('Please enter an answer')
      return
    }
    setLoading(true)
    setError('')
    try {
      const data = await submitAnswer(session.session_id, answer)
      setFeedback(data)
      setAnswer('')
      if (data.session_complete) {
        setFinalResult(data)
        setPhase('complete')
        const sessions = await getSessions()
        setPastSessions(sessions)
      } else {
        setCurrentQuestion(data.next_question)
        setQuestionNumber(data.question_number)
      }
    } catch (err) {
      setError('Failed to submit answer')
    } finally {
      setLoading(false)
    }
  }

  const handleReset = () => {
    setPhase('setup')
    setSession(null)
    setCurrentQuestion('')
    setAnswer('')
    setFeedback(null)
    setFinalResult(null)
    setError('')
  }

  const getScoreColor = (score) => {
    if (score >= 7) return 'text-green-400'
    if (score >= 4) return 'text-yellow-400'
    return 'text-red-400'
  }

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white mb-1">AI Interview Simulator</h1>
        <p className="text-gray-600 text-sm">Practice with AI-generated questions and get real-time feedback.</p>
      </div>

      {error && (
        <div className="bg-red-500/10 border border-red-500/20 text-red-400 text-sm px-4 py-3 rounded-xl mb-6 flex items-center justify-between">
          {error}
          <button onClick={() => setError('')}><X size={14} /></button>
        </div>
      )}

      {/* Setup phase */}
      {phase === 'setup' && (
        <div className="grid grid-cols-3 gap-6">
          <div className="col-span-2">
            <div className="glass rounded-2xl p-6 mb-6">
              <h2 className="text-sm font-semibold text-white mb-4">Start New Interview</h2>
              <div className="grid grid-cols-2 gap-4 mb-4">
                <div>
                  <label className="text-xs text-gray-500 uppercase tracking-wider mb-1.5 block">Job Role</label>
                  <input
                    type="text"
                    placeholder="e.g. Backend Engineer"
                    value={jobRole}
                    onChange={e => setJobRole(e.target.value)}
                    className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white text-sm focus:outline-none focus:border-indigo-500 transition placeholder-gray-700"
                  />
                </div>
                <div>
                  <label className="text-xs text-gray-500 uppercase tracking-wider mb-1.5 block">Difficulty</label>
                  <select
                    value={difficulty}
                    onChange={e => setDifficulty(e.target.value)}
                    className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white text-sm focus:outline-none focus:border-indigo-500 transition"
                  >
                    <option value="easy" className="bg-gray-900">Easy</option>
                    <option value="medium" className="bg-gray-900">Medium</option>
                    <option value="hard" className="bg-gray-900">Hard</option>
                  </select>
                </div>
              </div>
              <button
                onClick={handleStart}
                disabled={loading}
                className="bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white text-sm px-6 py-2.5 rounded-xl transition flex items-center gap-2"
              >
                {loading ? <><Loader size={14} className="animate-spin" /> Starting...</> : <><Play size={14} /> Start Interview</>}
              </button>
            </div>
          </div>

          <div className="glass rounded-2xl p-6">
            <h2 className="text-sm font-semibold text-white mb-4">How it works</h2>
            <div className="flex flex-col gap-4">
              {[
                { step: '1', text: 'Choose your job role and difficulty' },
                { step: '2', text: 'AI generates 5 technical questions' },
                { step: '3', text: 'Answer each question in your own words' },
                { step: '4', text: 'Get instant AI scoring and feedback' },
                { step: '5', text: 'Review your strengths and improvements' },
              ].map(({ step, text }) => (
                <div key={step} className="flex items-center gap-3">
                  <div className="w-6 h-6 rounded-full bg-indigo-500/20 border border-indigo-500/30 flex items-center justify-center text-xs text-indigo-400 flex-shrink-0 font-medium">
                    {step}
                  </div>
                  <p className="text-gray-400 text-sm">{text}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Past sessions */}
          {pastSessions.length > 0 && (
            <div className="col-span-3 glass rounded-2xl p-6">
              <h2 className="text-sm font-semibold text-white mb-4">Past Sessions</h2>
              <div className="grid grid-cols-3 gap-3">
                {pastSessions.map(s => (
                  <div key={s.id} className="bg-white/5 rounded-xl p-4">
                    <div className="flex items-center justify-between mb-2">
                      <p className="text-sm font-medium text-white truncate">{s.job_role}</p>
                      <span className={`text-xs px-2 py-0.5 rounded-full ${s.status === 'completed' ? 'bg-green-500/10 text-green-400' : 'bg-yellow-500/10 text-yellow-400'}`}>
                        {s.status}
                      </span>
                    </div>
                    <p className="text-xs text-gray-600">{s.difficulty} · {new Date(s.created_at).toLocaleDateString()}</p>
                    <p className="text-lg font-bold text-white mt-2">{s.total_score} pts</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Active interview */}
      {phase === 'active' && (
        <div className="max-w-3xl">
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-3">
              <span className="text-xs text-gray-600 uppercase tracking-wider">Question {questionNumber} of {totalQuestions}</span>
              <div className="flex gap-1">
                {Array.from({ length: totalQuestions }).map((_, i) => (
                  <div key={i} className={`h-1.5 w-8 rounded-full ${i < questionNumber ? 'bg-indigo-500' : 'bg-white/10'}`} />
                ))}
              </div>
            </div>
            <button onClick={handleReset} className="text-xs text-gray-600 hover:text-gray-400 transition">Exit</button>
          </div>

          <div className="glass rounded-2xl p-6 mb-4">
            <div className="flex items-start gap-3 mb-6">
              <div className="w-8 h-8 rounded-xl bg-indigo-500/20 flex items-center justify-center flex-shrink-0">
                <MessageSquare size={15} className="text-indigo-400" />
              </div>
              <div>
                <p className="text-xs text-gray-600 mb-2">AI Interviewer · {session?.job_role} · {session?.difficulty}</p>
                <p className="text-white text-base leading-relaxed">{currentQuestion}</p>
              </div>
            </div>

            {feedback && (
              <div className="bg-white/5 rounded-xl p-4 mb-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs text-gray-500 uppercase tracking-wider">Previous answer feedback</span>
                  <span className={`text-lg font-bold ${getScoreColor(feedback.score)}`}>{feedback.score}/10</span>
                </div>
                <p className="text-gray-400 text-sm mb-2">{feedback.feedback}</p>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <p className="text-xs text-green-400 mb-1">Strengths</p>
                    <p className="text-xs text-gray-500">{feedback.strengths}</p>
                  </div>
                  <div>
                    <p className="text-xs text-yellow-400 mb-1">Improvements</p>
                    <p className="text-xs text-gray-500">{feedback.improvements}</p>
                  </div>
                </div>
              </div>
            )}

            <textarea
              rows={5}
              placeholder="Type your answer here..."
              value={answer}
              onChange={e => setAnswer(e.target.value)}
              className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white text-sm focus:outline-none focus:border-indigo-500 transition placeholder-gray-700 resize-none mb-4"
            />
            <button
              onClick={handleSubmit}
              disabled={loading}
              className="bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white text-sm px-6 py-2.5 rounded-xl transition flex items-center gap-2"
            >
              {loading ? <><Loader size={14} className="animate-spin" /> Evaluating...</> : <><Send size={14} /> Submit Answer</>}
            </button>
          </div>
        </div>
      )}

      {/* Complete phase */}
      {phase === 'complete' && finalResult && (
        <div className="max-w-2xl">
          <div className="glass rounded-2xl p-8 text-center mb-6">
            <div className="w-16 h-16 rounded-2xl bg-indigo-500/20 flex items-center justify-center mx-auto mb-4">
              <Trophy size={28} className="text-indigo-400" />
            </div>
            <h2 className="text-2xl font-bold text-white mb-2">Interview Complete!</h2>
            <p className="text-gray-500 text-sm mb-6">Here's how you performed</p>
            <div className="grid grid-cols-3 gap-4 mb-6">
              <div className="bg-white/5 rounded-xl p-4">
                <p className="text-3xl font-bold text-white">{finalResult.total_score}</p>
                <p className="text-xs text-gray-600 mt-1">Total score</p>
              </div>
              <div className="bg-white/5 rounded-xl p-4">
                <p className="text-3xl font-bold text-white">{finalResult.average_score}</p>
                <p className="text-xs text-gray-600 mt-1">Avg per question</p>
              </div>
              <div className="bg-white/5 rounded-xl p-4">
                <p className="text-3xl font-bold text-white">{finalResult.questions_asked}</p>
                <p className="text-xs text-gray-600 mt-1">Questions answered</p>
              </div>
            </div>
            <div className="text-left mb-6">
              <p className="text-xs text-gray-500 uppercase tracking-wider mb-2">Final feedback</p>
              <p className="text-gray-300 text-sm">{finalResult.feedback}</p>
            </div>
            <button
              onClick={handleReset}
              className="bg-indigo-600 hover:bg-indigo-500 text-white text-sm px-6 py-2.5 rounded-xl transition"
            >
              Start New Interview
            </button>
          </div>
        </div>
      )}
    </div>
  )
}