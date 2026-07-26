import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Home, FileText, BarChart2, BookOpen, MessageSquare,
  GitBranch, Settings, LogOut, BrainCircuit, TrendingUp,
  Upload, Bell, ChevronRight, Zap, Target, Award
} from 'lucide-react'
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'

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

const missingSkills = [
  { skill: 'Docker', priority: 'Critical', pct: 85, color: 'from-red-500 to-rose-500' },
  { skill: 'Kubernetes', priority: 'High', pct: 65, color: 'from-orange-500 to-amber-500' },
  { skill: 'FastAPI', priority: 'Medium', pct: 45, color: 'from-yellow-500 to-orange-400' },
  { skill: 'Redis', priority: 'Low', pct: 25, color: 'from-green-500 to-emerald-500' },
]

const recentActivity = [
  { icon: Upload, text: 'Resume v3 uploaded', time: '2h ago', color: 'text-indigo-400' },
  { icon: Target, text: 'Skill gap analyzed for SWE role', time: '1d ago', color: 'text-purple-400' },
  { icon: MessageSquare, text: 'Interview session completed — 81%', time: '2d ago', color: 'text-green-400' },
  { icon: Award, text: 'ATS score improved by 13 points', time: '3d ago', color: 'text-yellow-400' },
]

export default function Dashboard() {
  const [active, setActive] = useState('Dashboard')
  const navigate = useNavigate()

  return (
    <div className="min-h-screen bg-[#0a0a0f] text-white flex">
      {/* Sidebar */}
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

        {/* User section */}
        <div className="border-t border-white/5 pt-4 mt-4">
          <div className="flex items-center gap-3 px-3 mb-3">
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-indigo-500 to-purple-500 flex items-center justify-center text-xs font-semibold">AK</div>
            <div className="flex-1 min-w-0">
              <div className="text-sm font-medium text-white truncate">Akash Veer</div>
              <div className="text-xs text-gray-600 truncate">akash@email.com</div>
            </div>
          </div>
          <button
            onClick={() => navigate('/')}
            className="flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm text-gray-600 hover:text-red-400 hover:bg-red-500/5 transition w-full text-left"
          >
            <LogOut size={15} />
            Logout
          </button>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 ml-60 p-8 min-h-screen">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold text-white">Good morning, Akash 👋</h1>
            <p className="text-gray-600 text-sm mt-0.5">Here's what's happening with your career today.</p>
          </div>
          <div className="flex items-center gap-3">
            <button className="w-9 h-9 glass rounded-xl flex items-center justify-center text-gray-500 hover:text-white transition relative">
              <Bell size={16} />
              <span className="absolute top-1.5 right-1.5 w-1.5 h-1.5 bg-indigo-500 rounded-full"></span>
            </button>
            <button className="bg-indigo-600 hover:bg-indigo-500 text-white text-sm px-4 py-2 rounded-xl transition flex items-center gap-2">
              <Upload size={14} /> Upload resume
            </button>
          </div>
        </div>

        {/* Stat cards */}
        <div className="grid grid-cols-4 gap-4 mb-6">
          {[
            { label: 'ATS Score', value: '74', change: '+13', icon: TrendingUp, color: 'text-green-400', bg: 'bg-green-500/10' },
            { label: 'Resumes', value: '3', change: '+1', icon: FileText, color: 'text-indigo-400', bg: 'bg-indigo-500/10' },
            { label: 'Interviews', value: '5', change: '+2', icon: MessageSquare, color: 'text-purple-400', bg: 'bg-purple-500/10' },
            { label: 'Match score', value: '68%', change: '+8%', icon: Zap, color: 'text-yellow-400', bg: 'bg-yellow-500/10' },
          ].map(({ label, value, change, icon: Icon, color, bg }) => (
            <div key={label} className="glass rounded-2xl p-5 card-hover">
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs text-gray-600 uppercase tracking-wider">{label}</span>
                <div className={`w-8 h-8 ${bg} rounded-lg flex items-center justify-center`}>
                  <Icon size={14} className={color} />
                </div>
              </div>
              <div className="text-3xl font-bold text-white mb-1">{value}</div>
              <div className="text-xs text-green-400">{change} this week</div>
            </div>
          ))}
        </div>

        <div className="grid grid-cols-3 gap-4">
          {/* Chart */}
          <div className="col-span-2 glass rounded-2xl p-6">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h2 className="text-sm font-semibold text-white">ATS Score Progress</h2>
                <p className="text-xs text-gray-600 mt-0.5">Last 6 weeks</p>
              </div>
              <span className="text-xs bg-green-500/10 text-green-400 border border-green-500/20 px-2.5 py-1 rounded-lg">↑ 29 pts</span>
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

          {/* Activity */}
          <div className="glass rounded-2xl p-6">
            <h2 className="text-sm font-semibold text-white mb-4">Recent activity</h2>
            <div className="flex flex-col gap-4">
              {recentActivity.map(({ icon: Icon, text, time, color }) => (
                <div key={text} className="flex gap-3">
                  <div className="w-7 h-7 rounded-lg bg-white/5 flex items-center justify-center flex-shrink-0 mt-0.5">
                    <Icon size={13} className={color} />
                  </div>
                  <div>
                    <p className="text-xs text-gray-300 leading-relaxed">{text}</p>
                    <p className="text-xs text-gray-600 mt-0.5">{time}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Missing skills */}
          <div className="col-span-3 glass rounded-2xl p-6">
            <div className="flex items-center justify-between mb-5">
              <div>
                <h2 className="text-sm font-semibold text-white">Top missing skills</h2>
                <p className="text-xs text-gray-600 mt-0.5">Based on your last skill gap analysis</p>
              </div>
              <button className="text-xs text-indigo-400 hover:text-indigo-300 transition flex items-center gap-1">
                View full report <ChevronRight size={12} />
              </button>
            </div>
            <div className="grid grid-cols-2 gap-4">
              {missingSkills.map(({ skill, priority, pct, color }) => (
                <div key={skill} className="flex items-center gap-4">
                  <div className="flex-1">
                    <div className="flex items-center justify-between mb-1.5">
                      <span className="text-sm text-gray-300 font-medium">{skill}</span>
                      <span className="text-xs text-gray-600">{priority}</span>
                    </div>
                    <div className="h-1.5 bg-white/5 rounded-full overflow-hidden">
                      <div className={`h-full bg-gradient-to-r ${color} rounded-full`} style={{ width: `${pct}%` }} />
                    </div>
                  </div>
                  <span className="text-xs text-gray-500 w-8 text-right">{pct}%</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}