import { useState, useEffect } from 'react'
import { GitBranch, Star, BookOpen, Users, Code, Loader, X, RefreshCw } from 'lucide-react'
import { connectGithub, getGithubProfile } from '../api/github'

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
      const data = await connectGithub(username)
      setProfile(data)
      setUsername('')
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to connect GitHub profile')
    } finally {
      setLoading(false)
    }
  }

  const getScoreColor = (score) => {
    if (score >= 70) return 'text-green-400'
    if (score >= 40) return 'text-yellow-400'
    return 'text-red-400'
  }

  const getScoreGradient = (score) => {
    if (score >= 70) return 'from-green-500 to-emerald-500'
    if (score >= 40) return 'from-yellow-500 to-orange-500'
    return 'from-red-500 to-rose-500'
  }

  if (fetching) {
    return (
      <div className="p-8 flex items-center justify-center min-h-96">
        <Loader size={20} className="animate-spin text-gray-600" />
      </div>
    )
  }

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white mb-1">GitHub Analyzer</h1>
        <p className="text-gray-600 text-sm">Connect your GitHub to analyze repositories and get a developer score.</p>
      </div>

      {error && (
        <div className="bg-red-500/10 border border-red-500/20 text-red-400 text-sm px-4 py-3 rounded-xl mb-6 flex items-center justify-between">
          {error}
          <button onClick={() => setError('')}><X size={14} /></button>
        </div>
      )}

      {/* Connect form */}
      <div className="glass rounded-2xl p-6 mb-6">
        <h2 className="text-sm font-semibold text-white mb-4">
          {profile ? 'Update GitHub Profile' : 'Connect GitHub Profile'}
        </h2>
        <div className="flex gap-3">
          <input
            type="text"
            placeholder="Enter GitHub username (e.g. torvalds)"
            value={username}
            onChange={e => setUsername(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleConnect()}
            className="flex-1 bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white text-sm focus:outline-none focus:border-indigo-500 transition placeholder-gray-700"
          />
          <button
            onClick={handleConnect}
            disabled={loading}
            className="bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white text-sm px-6 py-2.5 rounded-xl transition flex items-center gap-2 whitespace-nowrap"
          >
            {loading
              ? <><Loader size={14} className="animate-spin" /> Analyzing...</>
              : profile
                ? <><RefreshCw size={14} /> Refresh</>
                : <><GitBranch size={14} /> Connect</>
            }
          </button>
        </div>
      </div>

      {/* Profile */}
      {profile && (
        <>
          {/* Score card */}
          <div className="glass rounded-2xl p-6 mb-6">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h2 className="text-lg font-bold text-white">@{profile.github_username}</h2>
                <p className="text-gray-600 text-sm mt-0.5">Last synced {new Date(profile.synced_at).toLocaleDateString()}</p>
              </div>
              <div className="text-right">
                <p className={`text-4xl font-bold ${getScoreColor(profile.developer_score)}`}>
                  {profile.developer_score}
                </p>
                <p className="text-xs text-gray-600 mt-1">Developer score</p>
              </div>
            </div>
            <div className="h-2 bg-white/5 rounded-full overflow-hidden mb-6">
              <div
                className={`h-full bg-gradient-to-r ${getScoreGradient(profile.developer_score)} rounded-full`}
                style={{ width: `${profile.developer_score}%` }}
              />
            </div>
            <div className="grid grid-cols-4 gap-4">
              {[
                { label: 'Repositories', value: profile.repo_count, icon: BookOpen, color: 'text-indigo-400', bg: 'bg-indigo-500/10' },
                { label: 'Total stars', value: profile.total_stars?.toLocaleString(), icon: Star, color: 'text-yellow-400', bg: 'bg-yellow-500/10' },
                { label: 'Followers', value: profile.followers, icon: Users, color: 'text-purple-400', bg: 'bg-purple-500/10' },
                { label: 'Following', value: profile.following, icon: Users, color: 'text-cyan-400', bg: 'bg-cyan-500/10' },
              ].map(({ label, value, icon: Icon, color, bg }) => (
                <div key={label} className="bg-white/5 rounded-xl p-4">
                  <div className={`w-8 h-8 ${bg} rounded-lg flex items-center justify-center mb-3`}>
                    <Icon size={15} className={color} />
                  </div>
                  <p className="text-2xl font-bold text-white">{value}</p>
                  <p className="text-xs text-gray-600 mt-1">{label}</p>
                </div>
              ))}
            </div>
          </div>

          <div className="grid grid-cols-2 gap-6">
            {/* Top languages */}
            <div className="glass rounded-2xl p-6">
              <h2 className="text-sm font-semibold text-white mb-4">Top Languages</h2>
              {profile.top_languages?.length > 0 ? (
                <div className="flex flex-col gap-3">
                  {profile.top_languages.map(({ language, count }) => (
                    <div key={language} className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-lg bg-white/5 flex items-center justify-center flex-shrink-0">
                        <Code size={14} className="text-gray-400" />
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-sm text-gray-300">{language}</span>
                          <span className="text-xs text-gray-600">{count} repos</span>
                        </div>
                        <div className="h-1.5 bg-white/5 rounded-full overflow-hidden">
                          <div
                            className="h-full bg-gradient-to-r from-indigo-500 to-purple-500 rounded-full"
                            style={{ width: `${Math.min(count * 15, 100)}%` }}
                          />
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-gray-600 text-sm">No language data available</p>
              )}
            </div>

            {/* Top repos */}
            <div className="glass rounded-2xl p-6">
              <h2 className="text-sm font-semibold text-white mb-4">Top Repositories</h2>
              <div className="flex flex-col gap-3">
                {profile.repos?.slice(0, 5).map((repo) => (
  <a
    key={repo.name}
    href={repo.url}
    target="_blank"
    rel="noopener noreferrer"
    className="flex items-center gap-3 bg-white/5 rounded-xl p-3 hover:bg-white/10 transition"
  >
    <div className="flex-1 min-w-0">
      <p className="text-sm font-medium text-white truncate">
        {repo.name}
      </p>
      {repo.description && (
        <p className="text-xs text-gray-600 truncate mt-0.5">
          {repo.description}
        </p>
      )}
    </div>

    <div className="flex items-center gap-1 flex-shrink-0">
      <Star size={12} className="text-yellow-400" />
      <span className="text-xs text-gray-400">
        {repo.stars?.toLocaleString()}
      </span>
    </div>
  </a>
))}
              </div>
            </div>
          </div>
        </>
      )}

      {!profile && !loading && (
        <div className="glass rounded-2xl p-12 text-center">
          <GitBranch size={32} className="text-gray-700 mx-auto mb-3" />
          <p className="text-gray-500 text-sm">Enter your GitHub username above to analyze your profile and get a developer score.</p>
        </div>
      )}
    </div>
  )
}