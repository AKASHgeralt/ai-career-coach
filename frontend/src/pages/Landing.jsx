import { useNavigate } from 'react-router-dom'
import { BrainCircuit, FileSearch, Target, MessageSquare, GitBranch, BarChart3, ArrowRight, Sparkles, Shield, Zap } from 'lucide-react'

const features = [
  { icon: FileSearch, title: 'Resume Intelligence', desc: 'AI-powered ATS scoring, skill extraction and deep resume analysis in seconds.', color: 'from-indigo-500 to-purple-500' },
  { icon: Target, title: 'Skill Gap Engine', desc: 'Compare your profile against any job description with vector similarity matching.', color: 'from-purple-500 to-pink-500' },
  { icon: MessageSquare, title: 'Interview Simulator', desc: 'Practice with AI-generated questions, get scored answers and real-time feedback.', color: 'from-pink-500 to-rose-500' },
  { icon: GitBranch, title: 'GitHub Analyzer', desc: 'Deep dive into your repositories to generate a comprehensive developer score.', color: 'from-cyan-500 to-blue-500' },
  { icon: BarChart3, title: 'Learning Roadmap', desc: 'Personalized week-by-week plan to close your skill gaps and land your dream role.', color: 'from-blue-500 to-indigo-500' },
  { icon: BrainCircuit, title: 'AI Recommendations', desc: 'Curated courses, projects and practice questions tailored to your career goals.', color: 'from-violet-500 to-purple-500' },
]

const stats = [
  { value: '50K+', label: 'Job descriptions analyzed' },
  { value: '1000+', label: 'Skills tracked' },
  { value: '10K+', label: 'Interview questions' },
  { value: '98%', label: 'Accuracy rate' },
]

export default function Landing() {
  const navigate = useNavigate()

  return (
    <div className="min-h-screen bg-[#0a0a0f] text-white animated-bg">
      {/* Navbar */}
      <nav className="fixed top-0 left-0 right-0 z-50 glass border-b border-white/5">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center">
              <BrainCircuit size={16} className="text-white" />
            </div>
            <span className="font-semibold text-white">CareerAI</span>
          </div>
          <div className="hidden md:flex items-center gap-8 text-sm text-gray-400">
            <span className="hover:text-white cursor-pointer transition">Features</span>
            <span className="hover:text-white cursor-pointer transition">How it works</span>
            <span className="hover:text-white cursor-pointer transition">Pricing</span>
          </div>
          <div className="flex items-center gap-3">
            <button onClick={() => navigate('/login')} className="text-sm text-gray-400 hover:text-white px-4 py-2 rounded-lg transition">
              Sign in
            </button>
            <button onClick={() => navigate('/register')} className="text-sm bg-indigo-600 hover:bg-indigo-500 text-white px-4 py-2 rounded-lg transition flex items-center gap-1.5">
              Get started <ArrowRight size={14} />
            </button>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="pt-40 pb-24 px-6 text-center max-w-5xl mx-auto">
        <div className="inline-flex items-center gap-2 bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 text-xs px-3 py-1.5 rounded-full mb-6">
          <Sparkles size={12} />
          Powered by advanced NLP and LLM technology
        </div>
        <h1 className="text-6xl md:text-7xl font-bold mb-6 leading-tight tracking-tight">
          Land your dream job<br />
          <span className="gradient-text">with AI precision</span>
        </h1>
        <p className="text-gray-400 text-xl mb-10 max-w-2xl mx-auto leading-relaxed">
          The most advanced AI career platform. Analyze resumes, close skill gaps, simulate interviews and track your growth — all in one place.
        </p>
        <div className="flex items-center justify-center gap-4 flex-wrap">
          <button onClick={() => navigate('/register')} className="bg-indigo-600 hover:bg-indigo-500 text-white px-8 py-4 rounded-xl font-medium transition text-base flex items-center gap-2 glow">
            Start for free <ArrowRight size={16} />
          </button>
          <button onClick={() => navigate('/login')} className="glass text-gray-300 hover:text-white px-8 py-4 rounded-xl font-medium transition text-base">
            View demo
          </button>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-20">
          {stats.map(({ value, label }) => (
            <div key={label} className="glass rounded-2xl p-5 card-hover">
              <div className="text-3xl font-bold gradient-text mb-1">{value}</div>
              <div className="text-gray-500 text-sm">{label}</div>
            </div>
          ))}
        </div>
      </section>

      {/* Features */}
      <section className="py-24 px-6 max-w-7xl mx-auto">
        <div className="text-center mb-16">
          <h2 className="text-4xl font-bold mb-4">Everything you need to<br /><span className="gradient-text">accelerate your career</span></h2>
          <p className="text-gray-400 max-w-xl mx-auto">Built with cutting-edge ML, NLP and LLM technology to give you an unfair advantage in the job market.</p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {features.map(({ icon: Icon, title, desc, color }) => (
            <div key={title} className="glass rounded-2xl p-6 card-hover cursor-pointer group">
              <div className={`w-10 h-10 rounded-xl bg-gradient-to-br ${color} flex items-center justify-center mb-4 group-hover:scale-110 transition`}>
                <Icon size={18} className="text-white" />
              </div>
              <h3 className="font-semibold text-white mb-2">{title}</h3>
              <p className="text-gray-500 text-sm leading-relaxed">{desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* CTA */}
      <section className="py-24 px-6 text-center">
        <div className="glass rounded-3xl max-w-3xl mx-auto p-16 glow">
          <div className="flex justify-center gap-4 mb-6">
            <div className="w-10 h-10 rounded-xl bg-indigo-500/20 flex items-center justify-center"><Shield size={18} className="text-indigo-400" /></div>
            <div className="w-10 h-10 rounded-xl bg-purple-500/20 flex items-center justify-center"><Zap size={18} className="text-purple-400" /></div>
            <div className="w-10 h-10 rounded-xl bg-pink-500/20 flex items-center justify-center"><Sparkles size={18} className="text-pink-400" /></div>
          </div>
          <h2 className="text-4xl font-bold mb-4">Ready to transform<br /><span className="gradient-text">your career?</span></h2>
          <p className="text-gray-400 mb-8">Join thousands of professionals using AI to land better jobs faster.</p>
          <button onClick={() => navigate('/register')} className="bg-indigo-600 hover:bg-indigo-500 text-white px-8 py-4 rounded-xl font-medium transition text-base flex items-center gap-2 mx-auto">
            Get started free <ArrowRight size={16} />
          </button>
        </div>
      </section>

      <footer className="border-t border-white/5 py-8 text-center text-gray-600 text-sm">
        © 2026 CareerAI. Built with React, FastAPI and a lot of ML.
      </footer>
    </div>
  )
}