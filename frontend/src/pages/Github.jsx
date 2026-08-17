import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { GitBranch, Star, BookOpen, Users, Code, Loader, X, RefreshCw } from 'lucide-react'
import { connectGithub, getGithubProfile } from '../api/github'
import GithubInsights, { SyncStatus } from '../components/GithubInsights'

export default function GitHub() {
  const [username, setUsername] = useState('')
  const [profile, setProfile] = useState(null)
  const [loading, setLoading] = useState(false)
  const [fetching, setFetching] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    getGithubProfile()
      .then(setProfile)
      .catch(() => {})
      .finally(() => setFetching(false))
  }, [])

  const handleConnect = async () => {
    if (!username.trim()) {
      setError('Please enter a GitHub username')
      return
    }
    setLoading(true)
    setError('')
    try {
      const data = await connectGithub(username, Boolean(profile))
      setProfile(data)
      setUsername('')
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to connect GitHub profile')
    } finally {
      setLoading(false)
    }
  }

  const getScoreColor = (score) => {
    if (score >= 70) return 'text-emerald-400'
    if (score >= 40) return 'text-amber-400'
    return 'text-red-400'
  }

  if (fetching) {
    return (
      <div className="p-10 flex items-center justify-center min-h-96">
        <Loader size={18} className="animate-spin text-accent" />
      </div>
    )
  }

  return (
    <div className="p-5 sm:p-8 lg:p-10">
      <div className="mb-10">
        <span className="label">Integration</span>
        <h1 className="display text-4xl text-white mt-3 mb-2">GitHub Analyzer</h1>
        <p className="text-mistDim text-sm font-light">
          Connect your GitHub to analyze repositories and get a developer score.
        </p>
      </div>

      {error && (
        <div role="alert"
          className="border border-red-500/30 bg-red-500/[0.07] text-red-300 text-sm font-light px-4 py-3 mb-8 flex items-center justify-between">
          {error}
          <button onClick={() => setError('')} aria-label="Dismiss error"><X size={14} /></button>
        </div>
      )}

      {/* Connect form */}
      <div className="panel ticked p-8 mb-8">
        <span className="label">
          {profile ? 'Update GitHub Profile' : 'Connect GitHub Profile'}
        </span>
        <div className="flex flex-col sm:flex-row gap-3 mt-6">
          <input
            type="text"
            placeholder="Enter GitHub username (e.g. torvalds)"
            value={username}
            onChange={e => setUsername(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleConnect()}
            className="field flex-1 px-4 py-3.5 text-sm font-light"
          />
          <motion.button
            whileTap={{ scale: 0.97 }}
            onClick={handleConnect}
            disabled={loading}
            className="btn-primary text-xs uppercase tracking-[0.18em] px-7 py-3.5 flex items-center gap-2.5 whitespace-nowrap"
          >
            {loading
              ? <><Loader size={13} className="animate-spin" /> Analyzing…</>
              : profile
                ? <><RefreshCw size={13} /> Refresh</>
                : <><GitBranch size={13} /> Connect</>}
          </motion.button>
        </div>
      </div>

      {/* Profile */}
      <AnimatePresence>
      {profile && (
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.35 }}
        >
          {/* Score card */}
          <div className="panel ticked p-8 mb-8">
            <div className="flex items-start justify-between mb-6">
              <div>
                <span className="label">Profile</span>
                <h2 className="display text-3xl text-white mt-2">@{profile.github_username}</h2>
                <p className="text-[11px] text-mistDim mt-2">
                  Last synced {new Date(profile.synced_at).toLocaleDateString()}
                </p>
              </div>
              <div className="text-right">
                <p className={`display text-6xl ${getScoreColor(profile.developer_score)}`}>
                  {profile.developer_score}
                </p>
                <span className="label mt-2 block">Developer score</span>
              </div>
            </div>

            <div className="meter mb-8">
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${profile.developer_score}%` }}
                transition={{ duration: 0.8, ease: 'easeOut' }}
                className="meter-fill"
              />
            </div>

            <div className="grid grid-cols-2 lg:grid-cols-4 gap-px bg-line">
              {[
                { label: 'Repositories', value: profile.repo_count, icon: BookOpen },
                { label: 'Total stars', value: profile.total_stars?.toLocaleString(), icon: Star },
                { label: 'Followers', value: profile.followers, icon: Users },
                { label: 'Following', value: profile.following, icon: Users },
              ].map(({ label, value, icon: Icon }, i) => (
                <motion.div
                  key={label}
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.3, delay: i * 0.05 }}
                  className="bg-ink2 p-6"
                >
                  <Icon size={14} className="text-accent mb-4" />
                  <p className="display text-3xl text-white">{value}</p>
                  <span className="label mt-2 block">{label}</span>
                </motion.div>
              ))}
            </div>
          </div>

          <SyncStatus profile={profile} />

          <GithubInsights insights={profile.insights} />

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {/* Top languages */}
            <div className="panel p-8">
              <span className="label">Top Languages</span>
              {profile.top_languages?.length > 0 ? (
                <div className="flex flex-col mt-6">
                  {profile.top_languages.map(({ language, count }, i) => (
                    <motion.div
                      key={language}
                      initial={{ opacity: 0, x: -8 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ duration: 0.3, delay: i * 0.06 }}
                      className="flex items-center gap-4 py-3.5 border-b border-line last:border-b-0"
                    >
                      <Code size={13} className="text-accent flex-shrink-0" />
                      <div className="flex-1">
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-sm text-mist font-light">{language}</span>
                          <span className="text-[11px] text-mistDim">{count} repos</span>
                        </div>
                        <div className="meter">
                          <div className="meter-fill" style={{ width: `${Math.min(count * 15, 100)}%` }} />
                        </div>
                      </div>
                    </motion.div>
                  ))}
                </div>
              ) : (
                <p className="text-mistDim text-sm font-light mt-6">No language data available</p>
              )}
            </div>

            {/* Top repos */}
            <div className="panel p-8">
              <span className="label">Top Repositories</span>
              <div className="flex flex-col mt-6">
                {profile.repos?.slice(0, 5).map((repo, i) => (
                  <motion.a
                    key={repo.name}
                    initial={{ opacity: 0, x: 8 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ duration: 0.3, delay: i * 0.06 }}
                    href={repo.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-4 py-3.5 border-b border-line last:border-b-0 hover:bg-accent/[0.03] transition px-2 -mx-2"
                  >
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-light text-white truncate">{repo.name}</p>
                      {repo.description && (
                        <p className="text-[11px] text-mistDim truncate mt-1">{repo.description}</p>
                      )}
                    </div>
                    <div className="flex items-center gap-1.5 flex-shrink-0">
                      <Star size={11} className="text-accent" />
                      <span className="text-[11px] text-mist">{repo.stars?.toLocaleString()}</span>
                    </div>
                  </motion.a>
                ))}
              </div>
            </div>
          </div>
        </motion.div>
      )}
      </AnimatePresence>

      {!profile && !loading && (
        <div className="panel ticked p-16 text-center">
          <div className="relative z-10">
            <GitBranch size={28} className="text-mistDim mx-auto mb-4" />
            <p className="text-mistDim text-sm font-light">
              Enter your GitHub username above to analyze your profile and get a developer score.
            </p>
          </div>
        </div>
      )}
    </div>
  )
}
