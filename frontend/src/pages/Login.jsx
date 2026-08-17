import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { BrainCircuit, Mail, Lock, ArrowRight, Eye, EyeOff } from 'lucide-react'
import { login } from '../api/auth'
import { WireTerrain } from '../components/Wire'

export default function Login() {
  const navigate = useNavigate()
  const [form, setForm] = useState({ email: '', password: '' })
  const [showPass, setShowPass] = useState(false)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const data = await login(form.email, form.password)
      localStorage.setItem('token', data.access_token)
      navigate('/dashboard')
    } catch (err) {
      // Don't report every failure as bad credentials — a blocked or
      // unreachable API looks identical to the user otherwise, and sends
      // them retyping a password that was never the problem.
      if (!err.response) {
        setError("Can't reach the API. Is the backend running on port 8000, and is this page on http://localhost:5173?")
      } else if (err.response.status === 401) {
        setError('Invalid email or password')
      } else {
        setError(err.response.data?.detail || `Login failed (${err.response.status})`)
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
          <div className="panel ticked p-7 mb-10 max-w-sm">
            <div className="flex items-center gap-4 mb-4">
              <div className="w-10 h-10 border border-line2 flex items-center justify-center text-xs tracking-widest text-accent">
                AK
              </div>
              <div>
                <div className="text-sm font-light text-white">Akash Kumar</div>
                <div className="label mt-0.5">Software Engineer</div>
              </div>
            </div>
            <p className="text-mist text-sm font-light leading-relaxed">
              "CareerAI helped me identify exactly what skills I was missing.
              Got my dream job in 6 weeks."
            </p>
            <div className="flex gap-1.5 mt-4">
              {[1, 2, 3, 4, 5].map(i => (
                <div key={i} className="w-1.5 h-1.5 rounded-full bg-accent" style={{ boxShadow: '0 0 8px #4da6ff' }} />
              ))}
            </div>
          </div>

          <h2 className="display text-5xl text-white">
            Your AI-powered<br />
            <span className="accent-text">career co-pilot</span>
          </h2>
        </div>

        <div className="absolute bottom-0 left-0 right-0 h-56 pointer-events-none opacity-60">
          <WireTerrain className="w-full h-full" lines={18} />
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
            <span className="label">Account access</span>
            <h2 className="display text-4xl text-white mt-4 mb-2">Welcome back</h2>
            <p className="text-mistDim text-sm font-light">Sign in to continue your career journey</p>
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
              {loading ? 'Signing in…' : <>Sign in <ArrowRight size={14} /></>}
            </motion.button>
          </form>

          <div className="hairline my-8" />

          <p className="text-mistDim text-sm font-light text-center">
            Don't have an account?{' '}
            <Link to="/register" className="text-accent hover:text-accent2 transition">Create one free</Link>
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
