import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { BrainCircuit, Mail, Lock, ArrowRight, Eye, EyeOff } from 'lucide-react'

export default function Login() {
  const navigate = useNavigate()
  const [form, setForm] = useState({ email: '', password: '' })
  const [showPass, setShowPass] = useState(false)

  const handleSubmit = (e) => {
    e.preventDefault()
    navigate('/dashboard')
  }

  return (
    <div className="min-h-screen bg-[#0a0a0f] flex animated-bg">
      {/* Left panel */}
      <div className="hidden md:flex flex-col justify-between w-1/2 p-12 border-r border-white/5">
        <div className="flex items-center gap-2 cursor-pointer" onClick={() => navigate('/')}>
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center">
            <BrainCircuit size={16} className="text-white" />
          </div>
          <span className="font-semibold text-white">CareerAI</span>
        </div>
        <div>
          <div className="glass rounded-2xl p-6 mb-6">
            <div className="flex items-center gap-3 mb-3">
              <div className="w-10 h-10 rounded-full bg-gradient-to-br from-indigo-500 to-purple-500 flex items-center justify-center text-sm font-semibold text-white">AK</div>
              <div>
                <div className="text-sm font-medium text-white">Akash Kumar</div>
                <div className="text-xs text-gray-500">Software Engineer</div>
              </div>
            </div>
            <p className="text-gray-400 text-sm leading-relaxed">"CareerAI helped me identify exactly what skills I was missing. Got my dream job in 6 weeks."</p>
            <div className="flex gap-1 mt-3">
              {[1,2,3,4,5].map(i => (
                <div key={i} className="w-3 h-3 rounded-full bg-yellow-400" />
              ))}
            </div>
          </div>
          <h2 className="text-4xl font-bold text-white leading-tight">
            Your AI-powered<br />
            <span className="gradient-text">career co-pilot</span>
          </h2>
          <p className="text-gray-600 text-sm mt-3">Join thousands of professionals landing better jobs with AI.</p>
        </div>
      </div>

      {/* Right panel */}
      <div className="flex-1 flex items-center justify-center px-6">
        <div className="w-full max-w-sm">
          {/* Mobile logo */}
          <div className="flex md:hidden items-center gap-2 mb-8 cursor-pointer" onClick={() => navigate('/')}>
            <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center">
              <BrainCircuit size={14} className="text-white" />
            </div>
            <span className="font-semibold text-white text-sm">CareerAI</span>
          </div>

          <div className="mb-8">
            <h2 className="text-2xl font-bold text-white mb-1">Welcome back</h2>
            <p className="text-gray-500 text-sm">Sign in to continue your career journey</p>
          </div>

          <form onSubmit={handleSubmit} className="flex flex-col gap-4">
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
              <div className="flex items-center justify-between mb-1.5">
                <label className="text-xs text-gray-500 uppercase tracking-wider">Password</label>
                <span className="text-xs text-indigo-400 hover:text-indigo-300 cursor-pointer transition">Forgot password?</span>
              </div>
              <div className="relative">
                <Lock size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-600" />
                <input
                  type={showPass ? 'text' : 'password'}
                  placeholder="••••••••"
                  value={form.password}
                  onChange={e => setForm({...form, password: e.target.value})}
                  className="w-full bg-white/5 border border-white/10 rounded-xl pl-9 pr-10 py-3 text-white text-sm focus:outline-none focus:border-indigo-500 focus:bg-indigo-500/5 transition placeholder-gray-700"
                />
                <button
                  type="button"
                  onClick={() => setShowPass(!showPass)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-600 hover:text-gray-400 transition"
                >
                  {showPass ? <EyeOff size={15} /> : <Eye size={15} />}
                </button>
              </div>
            </div>
            <button
              type="submit"
              className="bg-indigo-600 hover:bg-indigo-500 text-white py-3 rounded-xl font-medium transition flex items-center justify-center gap-2 mt-1 glow"
            >
              Sign in <ArrowRight size={15} />
            </button>
          </form>

          <div className="mt-6 pt-6 border-t border-white/5 text-center">
            <p className="text-gray-600 text-sm">
              Don't have an account?{' '}
              <Link to="/register" className="text-indigo-400 hover:text-indigo-300 transition">Create one free</Link>
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