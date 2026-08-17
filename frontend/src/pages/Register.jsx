import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { BrainCircuit, Mail, Lock, User, ArrowRight, Eye, EyeOff, Check } from 'lucide-react'
import { register } from '../api/auth'
import { WireTerrain } from '../components/Wire'

const perks = [
  'AI-powered resume analysis and ATS scoring',
  'Skill gap detection against any job description',
  'Interview simulator with real-time AI feedback',
  'Personalized week-by-week learning roadmap',
  'GitHub profile analyzer and developer score',
]

export default function Register() {
  const navigate = useNavigate()
  const [form, setForm] = useState({ name: '', email: '', password: '' })
  const [showPass, setShowPass] = useState(false)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await register(form.name, form.email, form.password)
      navigate('/login')
    } catch (err) {
      if (!err.response) {
        setError("Can't reach the API. Is the backend running on port 8000, and is this page on http://localhost:5173?")
      } else {
        setError(err.response.data?.detail || 'Registration failed')
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-ink flex">
      {/* Left — atmosphere */}
      <div className="hidden md:flex flex-col justify-between w-1/2 p-14 border-r border-line relative overflow-hidden aurora dot-grid">
        <div
          className="flex items-center gap-3 cursor-pointer relative z-10 w-fit"
          onClick={() => navigate('/')}
        >
          <div className="w-8 h-8 border border-line2 flex items-center justify-center">
            <BrainCircuit size={15} className="text-accent" />
          </div>
          <span className="text-sm tracking-[0.28em] uppercase text-white/90">CareerAI</span>
        </div>

        <div className="relative z-10">
          <span className="label">What you get</span>
          <h2 className="display text-5xl text-white mt-5 mb-4">
            Everything you need<br />
            <span className="accent-text">to land the job</span>
          </h2>
          <p className="text-mistDim text-sm font-light mb-10">
            Built with cutting-edge ML, NLP and LLM technology.
          </p>

          <div className="flex flex-col">
            {perks.map(p => (
              <div key={p} className="flex items-center gap-4 py-3.5 border-b border-line last:border-b-0">
                <div className="w-5 h-5 border border-line2 flex items-center justify-center flex-shrink-0">
                  <Check size={10} className="text-accent" />
                </div>
                <span className="text-mist text-sm font-light">{p}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="absolute bottom-0 left-0 right-0 h-48 pointer-events-none opacity-45">
          <WireTerrain className="w-full h-full" lines={16} />
        </div>
      </div>

      {/* Right — form */}
      <div className="flex-1 flex items-center justify-center px-6 py-12">
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, ease: 'easeOut' }}
          className="w-full max-w-sm"
        >
          <div
            className="flex md:hidden items-center gap-3 mb-10 cursor-pointer"
            onClick={() => navigate('/')}
          >
            <div className="w-7 h-7 border border-line2 flex items-center justify-center">
              <BrainCircuit size={13} className="text-accent" />
            </div>
            <span className="text-xs tracking-[0.28em] uppercase text-white/90">CareerAI</span>
          </div>

          <div className="mb-10">
            <span className="label">New account</span>
            <h2 className="display text-4xl text-white mt-4 mb-2">Create your account</h2>
            <p className="text-mistDim text-sm font-light">Start your AI-powered career journey today</p>
          </div>

          {error && (
            <motion.div
              initial={{ opacity: 0, y: -6 }}
              animate={{ opacity: 1, y: 0 }}
              className="border border-red-500/30 bg-red-500/[0.07] text-red-300 text-sm px-4 py-3 mb-6 font-light"
            >
              {error}
            </motion.div>
          )}

          <form onSubmit={handleSubmit} className="flex flex-col gap-5">
            <div>
              <label className="label block mb-2.5">Full name</label>
              <div className="relative">
                <User size={14} className="absolute left-4 top-1/2 -translate-y-1/2 text-mistDim" />
                <input
                  type="text"
                  placeholder="Akash Veer"
                  value={form.name}
                  onChange={e => setForm({ ...form, name: e.target.value })}
                  className="field w-full pl-11 pr-4 py-3.5 text-sm font-light"
                />
              </div>
            </div>

            <div>
              <label className="label block mb-2.5">Email</label>
              <div className="relative">
                <Mail size={14} className="absolute left-4 top-1/2 -translate-y-1/2 text-mistDim" />
                <input
                  type="email"
                  placeholder="you@example.com"
                  value={form.email}
                  onChange={e => setForm({ ...form, email: e.target.value })}
                  className="field w-full pl-11 pr-4 py-3.5 text-sm font-light"
                />
              </div>
            </div>

            <div>
              <label className="label block mb-2.5">Password</label>
              <div className="relative">
                <Lock size={14} className="absolute left-4 top-1/2 -translate-y-1/2 text-mistDim" />
                <input
                  type={showPass ? 'text' : 'password'}
                  placeholder="••••••••"
                  value={form.password}
                  onChange={e => setForm({ ...form, password: e.target.value })}
                  className="field w-full pl-11 pr-11 py-3.5 text-sm font-light"
                />
                <button
                  type="button"
                  onClick={() => setShowPass(!showPass)}
                  aria-label={showPass ? 'Hide password' : 'Show password'}
                  className="absolute right-4 top-1/2 -translate-y-1/2 text-mistDim hover:text-accent transition"
                >
                  {showPass ? <EyeOff size={14} /> : <Eye size={14} />}
                </button>
              </div>
            </div>

            <motion.button
              whileTap={{ scale: 0.98 }}
              type="submit"
              disabled={loading}
              className="btn-primary py-4 text-xs uppercase tracking-[0.2em] flex items-center justify-center gap-2.5 mt-2"
            >
              {loading ? 'Creating account…' : <>Create account <ArrowRight size={14} /></>}
            </motion.button>
          </form>

          <div className="hairline my-8" />

          <p className="text-mistDim text-sm font-light text-center">
            Already have an account?{' '}
            <Link to="/login" className="text-accent hover:text-accent2 transition">Sign in</Link>
          </p>
          <p
            className="text-center label mt-6 cursor-pointer hover:text-accent transition"
            onClick={() => navigate('/')}
          >
            ← Back to home
          </p>
        </motion.div>
      </div>
    </div>
  )
}
