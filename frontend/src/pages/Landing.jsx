import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { BrainCircuit, FileSearch, Target, MessageSquare, GitBranch, BarChart3, ArrowRight, Sparkles, Shield, Zap, Upload, Wand2, Rocket, ChevronDown } from 'lucide-react'
import { WireTerrain, WireTube, Hotspot } from '../components/Wire'

const features = [
  { icon: FileSearch, title: 'Resume Intelligence', desc: 'AI-powered ATS scoring, skill extraction and deep resume analysis in seconds.' },
  { icon: Target, title: 'Skill Gap Engine', desc: 'Compare your profile against any job description with vector similarity matching.' },
  { icon: MessageSquare, title: 'Interview Simulator', desc: 'Practice with AI-generated questions, get scored answers and real-time feedback.' },
  { icon: GitBranch, title: 'GitHub Analyzer', desc: 'Deep dive into your repositories to generate a comprehensive developer score.' },
  { icon: BarChart3, title: 'Learning Roadmap', desc: 'Personalized week-by-week plan to close your skill gaps and land your dream role.' },
  { icon: BrainCircuit, title: 'AI Recommendations', desc: 'Curated courses, projects and practice questions tailored to your career goals.' },
]

const stats = [
  { value: '50K+', label: 'Job descriptions analyzed' },
  { value: '1000+', label: 'Skills tracked' },
  { value: '10K+', label: 'Interview questions' },
  { value: '98%', label: 'Accuracy rate' },
]

const steps = [
  { icon: Upload, step: '01', title: 'Upload your resume', desc: 'Drop in a PDF and get an instant ATS score with extracted skills, education and experience.' },
  { icon: Wand2, step: '02', title: 'Find your gaps', desc: 'Paste any job description to see exactly which skills match and which are missing, powered by vector embeddings.' },
  { icon: Rocket, step: '03', title: 'Close them fast', desc: 'Get an AI-generated roadmap of courses, projects and books, then practice in the interview simulator.' },
]

const scrollTo = (id) => {
  document.getElementById(id)?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

export default function Landing() {
  const navigate = useNavigate()

  return (
    <div className="min-h-screen bg-ink text-white overflow-hidden">
      {/* Navbar */}
      <nav className="fixed top-0 left-0 right-0 z-50 border-b border-line bg-ink/70 backdrop-blur-xl">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 border border-line2 flex items-center justify-center">
              <BrainCircuit size={15} className="text-accent" />
            </div>
            <span className="text-sm tracking-[0.28em] uppercase text-white/90">CareerAI</span>
          </div>
          <div className="hidden md:flex items-center gap-10">
            <button onClick={() => scrollTo('features')} className="label hover:text-accent transition">Features</button>
            <button onClick={() => scrollTo('how-it-works')} className="label hover:text-accent transition">How it works</button>
          </div>
          <div className="flex items-center gap-3">
            <button onClick={() => navigate('/login')} className="label hover:text-white transition px-3 py-2">
              Sign in
            </button>
            <button onClick={() => navigate('/register')} className="btn-primary text-xs uppercase tracking-[0.18em] px-5 py-2.5 flex items-center gap-2">
              Get started <ArrowRight size={13} />
            </button>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="relative min-h-screen flex flex-col items-center justify-center px-6 aurora dot-grid">
        <div className="relative z-10 text-center max-w-4xl">
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="inline-flex items-center gap-2.5 border border-line px-4 py-2 mb-10"
          >
            <Sparkles size={11} className="text-accent" />
            <span className="label !text-accent">Powered by NLP &amp; LLM technology</span>
          </motion.div>

          <motion.h1
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, delay: 0.1 }}
            className="display text-6xl md:text-8xl mb-8"
          >
            Land your dream job<br />
            <span className="accent-text">with AI precision</span>
          </motion.h1>

          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, delay: 0.2 }}
            className="text-mist text-lg font-light mb-12 max-w-2xl mx-auto leading-relaxed"
          >
            The most advanced AI career platform. Analyze resumes, close skill gaps,
            simulate interviews and track your growth — all in one place.
          </motion.p>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, delay: 0.3 }}
            className="flex items-center justify-center gap-4 flex-wrap"
          >
            <motion.button
              whileTap={{ scale: 0.97 }}
              onClick={() => navigate('/register')}
              className="btn-primary px-9 py-4 text-xs uppercase tracking-[0.2em] flex items-center gap-2.5"
            >
              Start for free <ArrowRight size={14} />
            </motion.button>
            <motion.button
              whileTap={{ scale: 0.97 }}
              onClick={() => navigate('/login')}
              className="btn-ghost px-9 py-4 text-xs uppercase tracking-[0.2em]"
            >
              Sign in
            </motion.button>
          </motion.div>
        </div>

        {/* Terrain horizon */}
        <div className="absolute bottom-0 left-0 right-0 h-[46vh] pointer-events-none">
          <WireTerrain className="w-full h-full" />
          <div className="absolute inset-x-0 bottom-0 h-32 bg-gradient-to-t from-ink to-transparent" />
        </div>

        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1 }}
          className="absolute bottom-8 left-1/2 -translate-x-1/2 z-10 flex flex-col items-center gap-3"
        >
          <span className="label">Scroll down to discover</span>
          <ChevronDown size={16} className="text-accent animate-bounce" />
        </motion.div>
      </section>

      {/* Stats */}
      <section className="relative border-y border-line">
        <div className="max-w-7xl mx-auto grid grid-cols-2 md:grid-cols-4">
          {stats.map(({ value, label }, i) => (
            <motion.div
              key={label}
              initial={{ opacity: 0, y: 16 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: i * 0.08 }}
              className="px-8 py-10 border-r border-line last:border-r-0 text-center"
            >
              <div className="display text-4xl mb-2 accent-text">{value}</div>
              <div className="label">{label}</div>
            </motion.div>
          ))}
        </div>
      </section>

      {/* Features */}
      <section id="features" className="relative py-32 px-6 scroll-mt-16">
        <div className="max-w-7xl mx-auto">
          <div className="flex items-end justify-between mb-16 flex-wrap gap-6">
            <div>
              <span className="label">01 — Capabilities</span>
              <h2 className="display text-5xl md:text-6xl mt-5">
                Everything you need to<br />
                <span className="accent-text">accelerate your career</span>
              </h2>
            </div>
            <p className="text-mist text-sm font-light max-w-sm leading-relaxed">
              Built with cutting-edge ML, NLP and LLM technology to give you an
              unfair advantage in the job market.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3">
            {features.map(({ icon: Icon, title, desc }, i) => (
              <motion.div
                key={title}
                initial={{ opacity: 0, y: 16 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.45, delay: i * 0.06 }}
                className="group relative border border-line -ml-px -mt-px p-8 hover:bg-accent/[0.03] transition-colors duration-300"
              >
                <div className="flex items-start justify-between mb-8">
                  <div className="w-11 h-11 border border-line2 flex items-center justify-center group-hover:border-accent transition-colors">
                    <Icon size={17} className="text-accent" />
                  </div>
                  <span className="label opacity-40">{String(i + 1).padStart(2, '0')}</span>
                </div>
                <h3 className="text-lg font-light text-white mb-3 tracking-tight">{title}</h3>
                <p className="text-mistDim text-sm font-light leading-relaxed">{desc}</p>
                <div className="mt-6 h-px w-0 group-hover:w-full bg-gradient-to-r from-accent to-transparent transition-all duration-500" />
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* How it works */}
      <section id="how-it-works" className="relative py-32 px-6 scroll-mt-16 border-t border-line overflow-hidden">
        <div className="absolute -left-24 top-1/2 -translate-y-1/2 w-[420px] opacity-25 pointer-events-none drift">
          <WireTube className="w-full" />
        </div>
        <div className="absolute -right-32 bottom-10 w-[380px] opacity-15 pointer-events-none">
          <WireTube className="w-full" flip rings={12} />
        </div>

        <div className="relative max-w-6xl mx-auto">
          <div className="text-center mb-20">
            <span className="label">02 — Process</span>
            <h2 className="display text-5xl md:text-6xl mt-5 mb-5">
              Three steps to<br />
              <span className="accent-text">a stronger application</span>
            </h2>
            <p className="text-mist text-sm font-light max-w-md mx-auto">
              No fluff — upload, analyze, and start closing the gaps that matter.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-px bg-line">
            {steps.map(({ icon: Icon, step, title, desc }, i) => (
              <motion.div
                key={step}
                initial={{ opacity: 0, y: 16 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.45, delay: i * 0.1 }}
                className="relative bg-ink p-10"
              >
                <Hotspot className="absolute top-6 right-6" />
                <div className="display text-6xl text-white/[0.06] mb-6">{step}</div>
                <div className="w-11 h-11 border border-line2 flex items-center justify-center mb-6">
                  <Icon size={17} className="text-accent" />
                </div>
                <h3 className="text-lg font-light text-white mb-3">{title}</h3>
                <p className="text-mistDim text-sm font-light leading-relaxed">{desc}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="relative py-32 px-6 border-t border-line aurora dot-grid">
        <div className="relative z-10 max-w-3xl mx-auto text-center">
          <div className="flex justify-center gap-5 mb-10">
            {[Shield, Zap, Sparkles].map((Icon, i) => (
              <div key={i} className="w-12 h-12 border border-line2 flex items-center justify-center">
                <Icon size={17} className="text-accent" />
              </div>
            ))}
          </div>
          <h2 className="display text-5xl md:text-6xl mb-6">
            Ready to transform<br />
            <span className="accent-text">your career?</span>
          </h2>
          <p className="text-mist text-sm font-light mb-12">
            Join thousands of professionals using AI to land better jobs faster.
          </p>
          <motion.button
            whileTap={{ scale: 0.97 }}
            onClick={() => navigate('/register')}
            className="btn-primary px-10 py-4 text-xs uppercase tracking-[0.2em] flex items-center gap-2.5 mx-auto"
          >
            Get started free <ArrowRight size={14} />
          </motion.button>
        </div>
      </section>

      <footer className="border-t border-line py-10 px-6">
        <div className="max-w-7xl mx-auto flex items-center justify-between flex-wrap gap-4">
          <div className="flex items-center gap-3">
            <div className="w-6 h-6 border border-line flex items-center justify-center">
              <BrainCircuit size={11} className="text-accent" />
            </div>
            <span className="label">CareerAI</span>
          </div>
          <span className="label">© 2026 — Built with React, FastAPI and a lot of ML</span>
        </div>
      </footer>
    </div>
  )
}
