import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Home, FileText, BarChart2, BookOpen, MessageSquare,
  GitBranch, Settings, LogOut, BrainCircuit, TrendingUp,
  Upload, Bell, ChevronRight, Zap, Target, Award
} from 'lucide-react'
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'
import { getSummary } from '../api/analytics'

const navItems = [
  { icon: Home, label: 'Dashboard' },
  { icon: FileText, label: 'Resumes' },
  { icon: BarChart2, label: 'Skill Gap' },
  { icon: BookOpen, label: 'Roadmap' },
  { icon: MessageSquare, label: 'Interview' },
  { icon: GitBranch, label: 'GitHub' },
  { icon: Settings, label: 'Settings' },
]

const chartData = [
  { week: 'W1', score: 45 },
  { week: 'W2', score: 52 },
  { week: 'W3', score: 58 },
  { week: 'W4', score: 61 },
  { week: 'W5', score: 70 },
  { week: 'W6', score: 74 },
]

export default function Dashboard() {
  const [active, setActive] = useState('Dashboard')
  const navigate = useNavigate()
  const [summary, setSummary] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const token = localStorage.getItem('token')
    if (!token) {
      navigate('/login')
      return
    }
    getSummary()
      .then(data => setSummary(data))
      .catch(() => navigate('/login'))
      .finally(() => setLoading(false))
  }, [])

  const handleLogout = () => {
    localStorage.removeItem('token')
    navigate('/')
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-[#0a0a0f] flex items-center justify-center">
        <div className="text-gray-400 text-sm">Loading your dashboard...</div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-[#0a0a0f] text-white flex">
      <aside className="w-60 flex flex-col py-6 px-3 border-r border-white/5 sidebar-glow fixed h-full">
        <div className="flex items-center gap-2 px-3 mb-8">
          <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center">
            <BrainCircuit size={14} className="text-white" />
          </div>
          <span className="font-semibold text-white text-sm">CareerAI</span>
        </div>

        <div className="flex flex-col gap-0.5 flex-1">
          <p className="text-xs text-gray-600 uppercase tracking-wider px-3 mb-2">Main</p>
          {navItems.slice(0, 5).map(({ icon: Icon, label }) => (
            <button
              key={label}
              onClick={() => setActive(label)}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition w-full text-left group
                ${active === label
                  ? 'bg-indigo-600/20 text-indigo-300 border border-indigo-500/20'
                  : 'text-gray-500 hover:text-gray-300 hover:bg-white/5'}`}
            >
              <Icon size={16} />
              {label}
              {active === label && <ChevronRight size={12} className="ml-auto" />}
            </button>
          ))}

          <p className="text-xs text-gray-600 uppercase tracking-wider px-3 mt-4 mb-2">Tools</p>
          {navItems.slice(5).map(({ icon: Icon, label }) => (
            <button
              key={label}
              onClick={() => setActive(label)}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition w-full text-left
                ${active === label
                  ? 'bg-indigo-600/20 text-indigo-300 border border-indigo-500/20'
                  : 'text-gray-500 hover:text-gray-300 hover:bg-white/5'}`}
            >
              <Icon size={16} />
              {label}
            </button>
          ))}
        </div>

        <div className="border-t border-white/5 pt-4 mt-4">
          <div className="flex items-center gap-3 px-3 mb-3">
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-indigo-500 to-purple-500 flex items-center justify-center text-xs font-semibold">
              {summary?.user?.full_name?.charAt(0) || 'U'}
            </div>
            <div className="flex-1 min-w-0">
              <div className="text-sm font-medium text-white truncate">{summary?.user?.full_name}</div>
              <div className="text-xs text-gray-600 truncate">{summary?.user?.email}</div>
            </div>
          </div>
          <button
            onClick={handleLogout}
            className="flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm text-gray-600 hover:text-red-400 hover:bg-red-500/5 transition w-full text-left"
          >
            <LogOut size={15} />
            Logout
          </button>
        </div>
      </aside>

      <main className="flex-1 ml-60 p-8 min-h-screen">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold text-white">Good morning, {summary?.user?.full_name?.split(' ')[0]} 👋</h1>
            <p className="text-gray-600 text-sm mt-0.5">Here's what's happening with your career today.</p>
          </div>
          <div className="flex items-center gap-3">
            <button className="w-9 h-9 glass rounded-xl flex items-center justify-center text-gray-500 hover:text-white transition">
              <Bell size={16} />
            </button>
            <button className="bg-indigo-600 hover:bg-indigo-500 text-white text-sm px-4 py-2 rounded-xl transition flex items-center gap-2">
              <Upload size={14} /> Upload resume
            </button>
          </div>
        </div>

        <div className="grid grid-cols-4 gap-4 mb-6">
          {[
            { label: 'ATS Score', value: summary?.resumes?.avg_ats_score || 0, change: '+13', icon: TrendingUp, color: 'text-green-400', bg: 'bg-green-500/10' },
            { label: 'Resumes', value: summary?.resumes?.count || 0, change: 'uploaded', icon: FileText, color: 'text-indigo-400', bg: 'bg-indigo-500/10' },
            { label: 'Interviews', value: summary?.interviews?.total_sessions || 0, change: 'sessions', icon: MessageSquare, color: 'text-purple-400', bg: 'bg-purple-500/10' },
            { label: 'Match score', value: `${summary?.skill_gaps?.avg_match_score || 0}%`, change: 'avg gap score', icon: Zap, color: 'text-yellow-400', bg: 'bg-yellow-500/10' },
          ].map(({ label, value, change, icon: Icon, color, bg }) => (
            <div key={label} className="glass rounded-2xl p-5 card-hover">
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs text-gray-600 uppercase tracking-wider">{label}</span>
                <div className={`w-8 h-8 ${bg} rounded-lg flex items-center justify-center`}>
                  <Icon size={14} className={color} />
                </div>
              </div>
              <div className="text-3xl font-bold text-white mb-1">{value}</div>
              <div className="text-xs text-green-400">{change}</div>
            </div>
          ))}
        </div>

        <div className="grid grid-cols-3 gap-4">
          <div className="col-span-2 glass rounded-2xl p-6">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h2 className="text-sm font-semibold text-white">ATS Score Progress</h2>
                <p className="text-xs text-gray-600 mt-0.5">Last 6 weeks</p>
              </div>
            </div>
            <ResponsiveContainer width="100%" height={180}>
              <AreaChart data={chartData}>
                <defs>
                  <linearGradient id="scoreGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#6366f1" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <XAxis dataKey="week" tick={{ fill: '#4b5563', fontSize: 11 }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fill: '#4b5563', fontSize: 11 }} axisLine={false} tickLine={false} domain={[30, 100]} />
                <Tooltip contentStyle={{ background: '#13131a', border: '1px solid rgba(255,255,255,0.08)', borderRadius: '12px', color: '#fff', fontSize: 12 }} />
                <Area type="monotone" dataKey="score" stroke="#6366f1" strokeWidth={2} fill="url(#scoreGrad)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>

          <div className="glass rounded-2xl p-6">
            <h2 className="text-sm font-semibold text-white mb-4">Recent activity</h2>
            <div className="flex flex-col gap-4">
              {summary?.resumes?.recent?.map((r) => (
                <div key={r.id} className="flex gap-3">
                  <div className="w-7 h-7 rounded-lg bg-white/5 flex items-center justify-center flex-shrink-0 mt-0.5">
                    <FileText size={13} className="text-indigo-400" />
                  </div>
                  <div>
                    <p className="text-xs text-gray-300 leading-relaxed">{r.file_name} uploaded</p>
                    <p className="text-xs text-gray-600 mt-0.5">ATS: {r.ats_score}</p>
                  </div>
                </div>
              ))}
              {summary?.interviews?.recent?.map((s) => (
                <div key={s.id} className="flex gap-3">
                  <div className="w-7 h-7 rounded-lg bg-white/5 flex items-center justify-center flex-shrink-0 mt-0.5">
                    <MessageSquare size={13} className="text-purple-400" />
                  </div>
                  <div>
                    <p className="text-xs text-gray-300 leading-relaxed">{s.job_role} interview</p>
                    <p className="text-xs text-gray-600 mt-0.5">Score: {s.total_score} · {s.status}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="col-span-3 glass rounded-2xl p-6">
            <div className="flex items-center justify-between mb-5">
              <div>
                <h2 className="text-sm font-semibold text-white">Top missing skills</h2>
                <p className="text-xs text-gray-600 mt-0.5">Based on your skill gap analyses</p>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              {summary?.skill_gaps?.top_missing_skills?.length > 0
                ? summary.skill_gaps.top_missing_skills.map(({ skill, count }) => (
                  <div key={skill} className="flex items-center gap-4">
                    <div className="flex-1">
                      <div className="flex items-center justify-between mb-1.5">
                        <span className="text-sm text-gray-300 font-medium capitalize">{skill}</span>
                        <span className="text-xs text-gray-600">{count}x missing</span>
                      </div>
                      <div className="h-1.5 bg-white/5 rounded-full overflow-hidden">
                        <div className="h-full bg-gradient-to-r from-red-500 to-rose-500 rounded-full" style={{ width: `${Math.min(count * 20, 100)}%` }} />
                      </div>
                    </div>
                  </div>
                ))
                : <p className="text-gray-600 text-sm col-span-2">No skill gap analyses yet. Upload a resume and analyze it!</p>
              }
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}