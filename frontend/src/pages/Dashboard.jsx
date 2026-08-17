import { useState, useEffect, useMemo } from 'react'
import { useNavigate, useLocation, Outlet } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  Home, FileText, BarChart2, BookOpen, MessageSquare,
  GitBranch, Settings as SettingsIcon, LogOut, BrainCircuit,
  Menu, X
} from 'lucide-react'
import { avatarSrc } from '../api/client'
import { getMe } from '../api/auth'
import { PATH_FOR } from './dashboardSections'

const navItems = [
  { icon: Home, label: 'Dashboard' },
  { icon: FileText, label: 'Resumes' },
  { icon: BarChart2, label: 'Skill Gap' },
  { icon: BookOpen, label: 'Roadmap' },
  { icon: MessageSquare, label: 'Interview' },
  { icon: GitBranch, label: 'GitHub' },
  { icon: SettingsIcon, label: 'Settings' },
]

function NavButton({ icon: Icon, label, active, onSelect }) {
  const isActive = active === label
  return (
    <motion.button
      whileTap={{ scale: 0.98 }}
      onClick={() => onSelect(label)}
      aria-current={isActive ? 'page' : undefined}
      className={`relative flex items-center gap-3.5 px-6 py-3 text-sm font-light transition w-full text-left
        ${isActive
          ? 'text-white bg-accent/[0.06]'
          : 'text-mistDim hover:text-mist hover:bg-white/[0.02]'}`}
    >
      {isActive && (
        <span
          className="absolute left-0 top-0 bottom-0 w-px bg-accent"
          style={{ boxShadow: '0 0 12px #4da6ff' }}
        />
      )}
      <Icon size={15} className={isActive ? 'text-accent' : ''} />
      {label}
    </motion.button>
  )
}

// Declared at module scope on purpose. Defining this inside Dashboard gave it a
// fresh component identity on every render, so React tore down and rebuilt the
// whole sidebar each time — which also wedged the AnimatePresence swap in main.
function Sidebar({ active, onSelect, user, onLogout, open, onClose, pinned }) {
  return (
    <aside
      // Off-canvas drawer below lg; a permanent column from lg up. Kept mounted
      // so nav state survives opening and closing on mobile.
      className="w-60 flex flex-col py-7 border-r border-line fixed left-0 top-0 h-full bg-ink z-40"
      style={{
        transform: (open || pinned) ? 'translateX(0)' : 'translateX(-100%)',
        transition: 'transform .3s cubic-bezier(.4,0,.2,1)',
      }}
    >
      <button
        onClick={onClose}
        aria-label="Close navigation"
        className="lg:hidden absolute top-6 right-4 text-mistDim hover:text-white transition p-1"
      >
        <X size={16} />
      </button>
      <div className="flex items-center gap-3 px-6 mb-10">
        <div className="w-8 h-8 border border-line2 flex items-center justify-center">
          <BrainCircuit size={14} className="text-accent" />
        </div>
        <span className="text-xs tracking-[0.28em] uppercase text-white/90">CareerAI</span>
      </div>

      <div className="flex flex-col flex-1">
        <p className="label px-6 mb-3">Main</p>
        {navItems.slice(0, 5).map(item => (
          <NavButton key={item.label} {...item} active={active} onSelect={onSelect} />
        ))}

        <p className="label px-6 mt-8 mb-3">Tools</p>
        {navItems.slice(5).map(item => (
          <NavButton key={item.label} {...item} active={active} onSelect={onSelect} />
        ))}
      </div>

      <div className="border-t border-line pt-5 mt-5">
        <div className="flex items-center gap-3 px-6 mb-4">
          <div className="w-9 h-9 border border-line2 overflow-hidden flex-shrink-0 flex items-center justify-center text-xs text-accent">
            {avatarSrc(user?.avatar_url) ? (
              <img src={avatarSrc(user.avatar_url)} alt="" className="w-full h-full object-cover" />
            ) : (
              user?.full_name?.charAt(0) || 'U'
            )}
          </div>
          <div className="flex-1 min-w-0">
            <div className="text-sm font-light text-white truncate">{user?.full_name}</div>
            <div className="text-[11px] text-mistDim truncate">{user?.email}</div>
          </div>
        </div>
        <button
          onClick={onLogout}
          className="flex items-center gap-3.5 px-6 py-3 text-sm font-light text-mistDim hover:text-red-400 transition w-full text-left"
        >
          <LogOut size={15} />
          Logout
        </button>
      </div>
    </aside>
  )
}

export default function Dashboard() {
  const location = useLocation()
  // Active section comes from the URL, so refresh, back/forward and deep links
  // all behave correctly. Longest-prefix match keeps /dashboard from matching
  // every child route.
  const active = useMemo(() => {
    const match = Object.entries(PATH_FOR)
      .filter(([, path]) => location.pathname === path || location.pathname.startsWith(path + '/'))
      .sort((a, b) => b[1].length - a[1].length)[0]
    return match ? match[0] : 'Dashboard'
  }, [location.pathname])
  const navigate = useNavigate()
  const [user, setUser] = useState(null)
  const [navOpen, setNavOpen] = useState(false)
  // The sidebar is a permanent column from lg up and a drawer below it.
  const [isDesktop, setIsDesktop] = useState(
    () => typeof window !== 'undefined' && window.matchMedia('(min-width: 1024px)').matches
  )

  useEffect(() => {
    const mq = window.matchMedia('(min-width: 1024px)')
    const onChange = (e) => {
      setIsDesktop(e.matches)
      if (e.matches) setNavOpen(false)
    }
    mq.addEventListener('change', onChange)
    return () => mq.removeEventListener('change', onChange)
  }, [])

  useEffect(() => {
    // The layout guards the route and loads only what the sidebar shows.
    // Each section fetches its own data, so switching sections no longer
    // re-requests the dashboard payload.
    if (!localStorage.getItem('token')) {
      navigate('/login')
      return
    }
    let cancelled = false
    getMe()
      .then(u => { if (!cancelled) setUser(u) })
      .catch(() => { if (!cancelled) navigate('/login') })
    return () => { cancelled = true }
  }, [navigate])

  const handleLogout = () => {
    localStorage.removeItem('token')
    navigate('/')
  }

  const selectSection = (label) => {
    navigate(PATH_FOR[label] || '/dashboard')
    setNavOpen(false)
  }

  return (
    <div className="min-h-screen bg-ink text-white flex">
      {/* Mobile top bar — the only way to reach navigation below lg */}
      <div className="lg:hidden fixed top-0 left-0 right-0 z-30 h-14 border-b border-line bg-ink/95 backdrop-blur flex items-center gap-3 px-4">
        <button
          onClick={() => setNavOpen(true)}
          aria-label="Open navigation"
          aria-expanded={navOpen}
          className="w-9 h-9 border border-line2 flex items-center justify-center text-accent"
        >
          <Menu size={15} />
        </button>
        <span className="text-xs tracking-[0.28em] uppercase text-white/90">CareerAI</span>
        <span className="label ml-auto truncate max-w-[45%]">{active}</span>
      </div>

      {/* Scrim closes the drawer on tap. Always rendered rather than mounted
          conditionally: a sibling appearing before <Sidebar/> shifts its
          position in the tree, which makes React remount the whole aside and
          lose its transition. Visibility is toggled instead. */}
      <div
        onClick={() => setNavOpen(false)}
        className={`lg:hidden fixed inset-0 bg-ink/80 z-30 transition-opacity duration-300
          ${navOpen ? 'opacity-100' : 'opacity-0 pointer-events-none'}`}
        aria-hidden="true"
      />

      <Sidebar
        active={active}
        onSelect={selectSection}
        user={user}
        onLogout={handleLogout}
        open={navOpen}
        pinned={isDesktop}
        onClose={() => setNavOpen(false)}
      />

      <main className="flex-1 min-w-0 lg:ml-60 min-h-screen pt-14 lg:pt-0">
        <Outlet />
      </main>
    </div>
  )
}
