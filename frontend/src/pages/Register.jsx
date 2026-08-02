import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { BrainCircuit, Mail, Lock, User, ArrowRight, Eye, EyeOff, Check } from 'lucide-react'
import { register } from '../api/auth'

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
      setError(err.response?.data?.detail || 'Registration failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-[#0a0a0f] flex animated-bg">
      <div className="hidden md:flex flex-col justify-between w-1/2 p-12 border-r border-white/5">
        <div className="flex items-center gap-2 cursor-pointer" onClick={() => navigate('/')}>
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center">
            <BrainCircuit size={16} className="text-white" />
          </div>
          <span className="font-semibold text-white">CareerAI</span>
        </div>
        <div>
          <h2 className="text-4xl font-bold text-white leading-tight mb-3">
            Everything you need<br />
            <span className="gradient-text">to land the job</span>
          </h2>
          <p className="text-gray-600 text-sm mb-8">Built with cutting-edge ML, NLP and LLM technology.</p>
          <div className="flex flex-col gap-3">
            {perks.map(p => (
              <div key={p} className="flex items-center gap-3">
                <div className="w-5 h-5 rounded-full bg-indigo-500/20 border border-indigo-500/30 flex items-center justify-center flex-shrink-0">
                  <Check size={11} className="text-indigo-400" />
                </div>
                <span className="text-gray-400 text-sm">{p}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="flex-1 flex items-center justify-center px-6">
        <div className="w-full max-w-sm">
          <div className="flex md:hidden items-center gap-2 mb-8 cursor-pointer" onClick={() => navigate('/')}>
            <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center">
              <BrainCircuit size={14} className="text-white" />
            </div>
            <span className="font-semibold text-white text-sm">CareerAI</span>
          </div>

          <div className="mb-8">
            <h2 className="text-2xl font-bold text-white mb-1">Create your account</h2>
            <p className="text-gray-500 text-sm">Start your AI-powered career journey today</p>
          </div>

          {error && (
            <div className="bg-red-500/10 border border-red-500/20 text-red-400 text-sm px-4 py-3 rounded-xl mb-4">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="flex flex-col gap-4">
            <div>
              <label className="text-xs text-gray-500 mb-1.5 block uppercase tracking-wider">Full name</label>
              <div className="relative">
                <User size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-600" />
                <input
                  type="text"
                  placeholder="Akash Veer"
                  value={form.name}
                  onChange={e => setForm({...form, name: e.target.value})}
                  className="w-full bg-white/5 border border-white/10 rounded-xl pl-9 pr-4 py-3 text-white text-sm focus:outline-none focus:border-indigo-500 focus:bg-indigo-500/5 transition placeholder-gray-700"
                />
              </div>
            </div>
            <div>
              <label className="text-xs text-gray-500 mb-1.5 block uppercase tracking-wider">Email</label>
              <div className="relative">
                <Mail size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-600" />
                <input
                  type="email"
                  placeholder="you@example.com"
                  value={form.email}
                  onChange={e => setForm({...form, email: e.target.value})}
                  className="w-full bg-white/5 border border-white/10 rounded-xl pl-9 pr-4 py-3 text-white text-sm focus:outline-none focus:border-indigo-500 focus:bg-indigo-500/5 transition placeholder-gray-700"
                />
              </div>
            </div>
            <div>
              <label className="text-xs text-gray-500 mb-1.5 block uppercase tracking-wider">Password</label>
              <div className="relative">
                <Lock size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-600" />
                <input
                  type={showPass ? 'text' : 'password'}
                  placeholder="••••••••"
                  value={form.password}
                  onChange={e => setForm({...form, password: e.target.value})}
                  className="w-full bg-white/5 border border-white/10 rounded-xl pl-9 pr-10 py-3 text-white text-sm focus:outline-none focus:border-indigo-500 focus:bg-indigo-500/5 transition placeholder-gray-700"
                />
                <button type="button" onClick={() => setShowPass(!showPass)} className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-600 hover:text-gray-400 transition">
                  {showPass ? <EyeOff size={15} /> : <Eye size={15} />}
                </button>
              </div>
            </div>
            <button
              type="submit"
              disabled={loading}
              className="bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white py-3 rounded-xl font-medium transition flex items-center justify-center gap-2 glow"
            >
              {loading ? 'Creating account...' : <> Create account <ArrowRight size={15} /> </>}
            </button>
          </form>

          <div className="mt-6 pt-6 border-t border-white/5 text-center">
            <p className="text-gray-600 text-sm">
              Already have an account?{' '}
              <Link to="/login" className="text-indigo-400 hover:text-indigo-300 transition">Sign in</Link>
            </p>
          </div>
          <p className="text-center text-xs text-gray-700 mt-4 cursor-pointer hover:text-gray-500 transition" onClick={() => navigate('/')}>
            ← Back to home
          </p>
        </div>
      </div>
    </div>
  )
}