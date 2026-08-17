import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { MessageSquare, Play, Send, Trophy, Loader, X } from 'lucide-react'
import { startInterview, submitAnswer, getSessions } from '../api/interview'
import InterviewAnalytics from '../components/InterviewAnalytics'

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
    } catch {
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
      setError(err.response?.data?.detail || 'Failed to submit answer')
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
    if (score >= 7) return 'text-emerald-400'
    if (score >= 4) return 'text-amber-400'
    return 'text-red-400'
  }

  return (
    <div className="p-5 sm:p-8 lg:p-10">
      <div className="mb-10">
        <span className="label">Practice</span>
        <h1 className="display text-4xl text-white mt-3 mb-2">AI Interview Simulator</h1>
        <p className="text-mistDim text-sm font-light">
          Practice with AI-generated questions and get real-time feedback.
        </p>
      </div>

      {error && (
        <div role="alert"
          className="border border-red-500/30 bg-red-500/[0.07] text-red-300 text-sm font-light px-4 py-3 mb-8 flex items-center justify-between">
          {error}
          <button onClick={() => setError('')} aria-label="Dismiss error"><X size={14} /></button>
        </div>
      )}

      {/* Setup phase */}
      {phase === 'setup' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <div className="lg:col-span-2">
            <div className="panel ticked p-8">
              <span className="label">Start New Interview</span>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 mt-6 mb-6">
                <div>
                  <label className="label block mb-2.5">Job Role</label>
                  <input
                    type="text"
                    placeholder="e.g. Backend Engineer"
                    value={jobRole}
                    onChange={e => setJobRole(e.target.value)}
                    className="field w-full px-4 py-3.5 text-sm font-light"
                  />
                </div>
                <div>
                  <label className="label block mb-2.5">Difficulty</label>
                  <select
                    value={difficulty}
                    onChange={e => setDifficulty(e.target.value)}
                    className="field w-full px-4 py-3.5 text-sm font-light"
                  >
                    <option value="easy" className="bg-ink2">Easy</option>
                    <option value="medium" className="bg-ink2">Medium</option>
                    <option value="hard" className="bg-ink2">Hard</option>
                  </select>
                </div>
              </div>
              <motion.button
                whileTap={{ scale: 0.97 }}
                onClick={handleStart}
                disabled={loading}
                className="btn-primary text-xs uppercase tracking-[0.18em] px-7 py-3.5 flex items-center gap-2.5"
              >
                {loading
                  ? <><Loader size={13} className="animate-spin" /> Starting…</>
                  : <><Play size={13} /> Start Interview</>}
              </motion.button>
            </div>
          </div>

          <div className="panel p-8">
            <span className="label">How it works</span>
            <div className="flex flex-col mt-6">
              {[
                { step: '1', text: 'Choose your job role and difficulty' },
                { step: '2', text: 'AI generates 5 technical questions' },
                { step: '3', text: 'Answer each question in your own words' },
                { step: '4', text: 'Get instant AI scoring and feedback' },
                { step: '5', text: 'Review your strengths and improvements' },
              ].map(({ step, text }) => (
                <div key={step} className="flex items-center gap-4 py-3 border-b border-line last:border-b-0">
                  <div className="w-6 h-6 border border-line2 flex items-center justify-center text-[10px] text-accent flex-shrink-0">
                    {step}
                  </div>
                  <p className="text-mist text-xs font-light">{text}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Past sessions */}
          {pastSessions.length > 0 && (
            <div className="lg:col-span-3 panel p-8">
              <span className="label">Past Sessions</span>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-px bg-line mt-6">
                {pastSessions.map((s, i) => (
                  <motion.div
                    key={s.id}
                    initial={{ opacity: 0, y: 8 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.3, delay: i * 0.05 }}
                    className="bg-ink p-5"
                  >
                    <div className="flex items-center justify-between mb-3">
                      <p className="text-sm font-light text-white truncate">{s.job_role}</p>
                      <span className={`text-[10px] uppercase tracking-[0.15em] px-2 py-1 border
                        ${s.status === 'completed'
                          ? 'border-emerald-500/30 text-emerald-400'
                          : 'border-amber-500/30 text-amber-400'}`}>
                        {s.status}
                      </span>
                    </div>
                    <p className="text-[11px] text-mistDim">
                      {s.difficulty} · {new Date(s.created_at).toLocaleDateString()}
                    </p>
                    <p className="display text-2xl text-white mt-3">{s.total_score} pts</p>
                  </motion.div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Active interview */}
      {phase === 'active' && (
        <div className="max-w-3xl">
          <div className="flex items-center justify-between mb-8">
            <div className="flex items-center gap-5">
              <span className="label">Question {questionNumber} of {totalQuestions}</span>
              <div className="flex gap-1.5">
                {Array.from({ length: totalQuestions }).map((_, i) => (
                  <div
                    key={i}
                    className={`h-px w-10 ${i < questionNumber ? 'bg-accent' : 'bg-line'}`}
                    style={i < questionNumber ? { boxShadow: '0 0 8px #4da6ff' } : undefined}
                  />
                ))}
              </div>
            </div>
            <button onClick={handleReset} className="label hover:text-red-400 transition">Exit</button>
          </div>

          <motion.div
            key={questionNumber}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.35 }}
            className="panel ticked p-8"
          >
            <div className="flex items-start gap-5 mb-8">
              <div className="w-10 h-10 border border-line2 flex items-center justify-center flex-shrink-0">
                <MessageSquare size={15} className="text-accent" />
              </div>
              <div>
                <span className="label">
                  AI Interviewer · {session?.job_role} · {session?.difficulty}
                </span>
                <p className="text-white text-lg font-light leading-relaxed mt-3">{currentQuestion}</p>
              </div>
            </div>

            {feedback && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                className="border border-line bg-accent/[0.03] p-5 mb-6"
              >
                <div className="flex items-center justify-between mb-3">
                  <span className="label">Previous answer feedback</span>
                  <span className={`display text-2xl ${getScoreColor(feedback.score)}`}>
                    {feedback.score}/10
                  </span>
                </div>
                <p className="text-mist text-sm font-light mb-4">{feedback.feedback}</p>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
                  <div>
                    <span className="label !text-emerald-400">Strengths</span>
                    <p className="text-xs text-mistDim font-light mt-2">{feedback.strengths}</p>
                  </div>
                  <div>
                    <span className="label !text-amber-400">Improvements</span>
                    <p className="text-xs text-mistDim font-light mt-2">{feedback.improvements}</p>
                  </div>
                </div>
              </motion.div>
            )}

            <textarea
              rows={5}
              placeholder="Type your answer here…"
              value={answer}
              onChange={e => setAnswer(e.target.value)}
              className="field w-full px-4 py-3.5 text-sm font-light resize-none mb-6"
            />
            <motion.button
              whileTap={{ scale: 0.97 }}
              onClick={handleSubmit}
              disabled={loading}
              className="btn-primary text-xs uppercase tracking-[0.18em] px-7 py-3.5 flex items-center gap-2.5"
            >
              {loading
                ? <><Loader size={13} className="animate-spin" /> Evaluating…</>
                : <><Send size={13} /> Submit Answer</>}
            </motion.button>
          </motion.div>
        </div>
      )}

      {/* Complete phase */}
      {phase === 'complete' && finalResult && (
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.45 }}
          className="max-w-2xl"
        >
          <div className="panel ticked p-12 text-center">
            <div className="relative z-10">
              <motion.div
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                transition={{ type: 'spring', stiffness: 200, damping: 13, delay: 0.1 }}
                className="w-16 h-16 border border-line2 flex items-center justify-center mx-auto mb-6"
              >
                <Trophy size={24} className="text-accent" />
              </motion.div>
              <h2 className="display text-4xl text-white mb-3">Interview Complete</h2>
              <p className="text-mistDim text-sm font-light mb-10">Here's how you performed</p>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-px bg-line mb-10">
                <div className="bg-ink p-6">
                  <p className="display text-4xl text-white">{finalResult.total_score}</p>
                  <span className="label mt-2 block">Total score</span>
                </div>
                <div className="bg-ink p-6">
                  <p className="display text-4xl accent-text">{finalResult.average_score}</p>
                  <span className="label mt-2 block">Avg per question</span>
                </div>
                <div className="bg-ink p-6">
                  <p className="display text-4xl text-white">{finalResult.questions_asked}</p>
                  <span className="label mt-2 block">Questions answered</span>
                </div>
              </div>

              <div className="text-left mb-10">
                <span className="label">Final feedback</span>
                <p className="text-mist text-sm font-light mt-3">{finalResult.feedback}</p>
              </div>

              <div className="mb-10">
                <InterviewAnalytics analytics={finalResult.analytics} />
              </div>

              <motion.button
                whileTap={{ scale: 0.97 }}
                onClick={handleReset}
                className="btn-primary text-xs uppercase tracking-[0.18em] px-7 py-3.5 mx-auto"
              >
                Start New Interview
              </motion.button>
            </div>
          </div>
        </motion.div>
      )}
    </div>
  )
}
