import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Landing from './pages/Landing.jsx'
import Login from './pages/Login'
import Register from './pages/Register'
import Dashboard from './pages/Dashboard'
import Overview from './pages/Overview'
import Resumes from './pages/Resumes'
import SkillGap from './pages/Skillgap'
import Roadmap from './pages/Roadmap'
import Interview from './pages/Interview'
import GitHub from './pages/Github'
import Settings from './pages/Settings'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />

        {/* Dashboard is a layout; each section owns a real URL so refresh,
            back/forward, deep links and bookmarks all work. */}
        <Route path="/dashboard" element={<Dashboard />}>
          <Route index element={<Overview />} />
          <Route path="resumes" element={<Resumes />} />
          <Route path="skill-gap" element={<SkillGap />} />
          <Route path="roadmap" element={<Roadmap />} />
          <Route path="interview" element={<Interview />} />
          <Route path="github" element={<GitHub />} />
          <Route path="settings" element={<Settings />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App
