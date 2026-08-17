import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { User, Mail, Calendar, LogOut, Shield, Camera, Loader, X, Trash2, Target } from 'lucide-react'
import { getMe, uploadAvatar, removeAvatar } from '../api/auth'
import { avatarSrc } from '../api/client'
import TargetRoleSelector from '../components/TargetRoleSelector'

const MAX_AVATAR_MB = 3
const ACCEPTED_TYPES = ['image/png', 'image/jpeg', 'image/gif', 'image/webp']

export default function Settings() {
  const navigate = useNavigate()
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState('')
  const fileInputRef = useRef(null)

  useEffect(() => {
    getMe()
      .then(setUser)
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  const handleLogout = () => {
    localStorage.removeItem('token')
    navigate('/')
  }

  const handleAvatarPick = async (file) => {
    if (!file) return
    if (!ACCEPTED_TYPES.includes(file.type)) {
      setError('Please choose a PNG, JPEG, GIF or WEBP image')
      return
    }
    if (file.size > MAX_AVATAR_MB * 1024 * 1024) {
      setError(`Image must be under ${MAX_AVATAR_MB}MB`)
      return
    }
    setUploading(true)
    setError('')
    try {
      const updated = await uploadAvatar(file)
      setUser(updated)
    } catch {
      setError('Failed to upload photo. Please try again.')
    } finally {
      setUploading(false)
      if (fileInputRef.current) fileInputRef.current.value = ''
    }
  }

  const handleRemoveAvatar = async () => {
    setUploading(true)
    setError('')
    try {
      const updated = await removeAvatar()
      setUser(updated)
    } catch {
      setError('Failed to remove photo. Please try again.')
    } finally {
      setUploading(false)
    }
  }

  return (
    <motion.div
      className="p-5 sm:p-8 lg:p-10 max-w-2xl"
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, ease: 'easeOut' }}
    >
      <div className="mb-10">
        <span className="label">Account</span>
        <h1 className="display text-4xl text-white mt-3 mb-2">Settings</h1>
        <p className="text-mistDim text-sm font-light">Manage your account details.</p>
      </div>

      {error && (
        <motion.div
          initial={{ opacity: 0, y: -6 }}
          animate={{ opacity: 1, y: 0 }}
          className="border border-red-500/30 bg-red-500/[0.07] text-red-300 text-sm font-light px-4 py-3 mb-8 flex items-center justify-between"
        >
          {error}
          <button onClick={() => setError('')} aria-label="Dismiss error"><X size={14} /></button>
        </motion.div>
      )}

      {loading ? (
        <div className="panel p-8 animate-pulse">
          <div className="h-4 w-32 bg-white/[0.06] mb-4" />
          <div className="h-3 w-48 bg-white/[0.04]" />
        </div>
      ) : (
        <>
          <div className="panel ticked p-8 mb-8">
            <div className="flex items-center gap-6 mb-8">
              <input
                ref={fileInputRef}
                type="file"
                accept="image/png,image/jpeg,image/gif,image/webp"
                className="hidden"
                onChange={e => handleAvatarPick(e.target.files[0])}
              />
              <button
                onClick={() => fileInputRef.current?.click()}
                disabled={uploading}
                className="relative w-16 h-16 border border-line2 overflow-hidden flex-shrink-0 group disabled:cursor-wait"
                title="Change photo"
              >
                {avatarSrc(user?.avatar_url) ? (
                  <img src={avatarSrc(user.avatar_url)} alt="Your avatar" className="w-full h-full object-cover" />
                ) : (
                  <div className="w-full h-full flex items-center justify-center display text-2xl text-accent">
                    {user?.full_name?.charAt(0) || 'U'}
                  </div>
                )}
                <div className="absolute inset-0 bg-ink/80 flex items-center justify-center opacity-0 group-hover:opacity-100 transition">
                  {uploading
                    ? <Loader size={15} className="text-accent animate-spin" />
                    : <Camera size={15} className="text-accent" />}
                </div>
              </button>

              {/* min-w-0 lets this shrink below its content: without it a long
                  email address widens the row past the viewport. */}
              <div className="flex-1 min-w-0">
                <p className="text-white text-lg font-light truncate">{user?.full_name}</p>
                <p className="text-mistDim text-sm font-light mt-0.5 truncate">{user?.email}</p>
                <div className="flex items-center gap-5 mt-3">
                  <button
                    onClick={() => fileInputRef.current?.click()}
                    disabled={uploading}
                    className="label hover:text-accent transition disabled:opacity-50"
                  >
                    Upload photo
                  </button>
                  {user?.avatar_url && (
                    <button
                      onClick={handleRemoveAvatar}
                      disabled={uploading}
                      className="label hover:text-red-400 transition disabled:opacity-50 flex items-center gap-1.5"
                    >
                      <Trash2 size={10} /> Remove
                    </button>
                  )}
                </div>
              </div>
            </div>

            <div className="flex flex-col">
              {[
                { icon: User, label: 'Full name', value: user?.full_name },
                { icon: Mail, label: 'Email', value: user?.email },
                {
                  icon: Calendar,
                  label: 'Member since',
                  value: user?.created_at
                    ? new Date(user.created_at).toLocaleDateString(undefined, { year: 'numeric', month: 'long', day: 'numeric' })
                    : '—',
                },
              ].map(({ icon: Icon, label, value }) => (
                <div key={label} className="flex items-center gap-4 py-4 border-b border-line last:border-b-0">
                  <Icon size={14} className="text-accent flex-shrink-0" />
                  <div>
                    <span className="label">{label}</span>
                    <p className="text-sm text-mist font-light mt-1">{value}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="panel ticked p-8 mb-8">
            <div className="flex items-start justify-between mb-2">
              <div className="flex items-center gap-2.5">
                <Target size={14} className="text-accent" />
                <span className="label">Target role</span>
              </div>
              {user?.target_role_label && (
                <span className="text-[11px] text-accent uppercase tracking-[0.15em]">
                  {user.target_role_label}
                </span>
              )}
            </div>
            <p className="text-mistDim text-xs font-light mb-6">
              Drives your skill-gap baseline, roadmap, interview questions and
              career readiness score. You can change it at any time.
            </p>
            <TargetRoleSelector
              current={user?.target_role}
              onChange={setUser}
            />
            {user?.target_role_updated_at && (
              <p className="text-[11px] text-mistDim mt-5">
                Last changed {new Date(user.target_role_updated_at).toLocaleDateString()}
              </p>
            )}
          </div>

          <div className="panel p-8">
            <div className="flex items-center gap-2.5 mb-6">
              <Shield size={14} className="text-accent" />
              <span className="label">Session</span>
            </div>
            <button
              onClick={handleLogout}
              className="btn-ghost flex items-center gap-2.5 text-[11px] uppercase tracking-[0.15em] px-5 py-3 hover:!text-red-400 hover:!border-red-500/40"
            >
              <LogOut size={13} /> Sign out of this device
            </button>
          </div>
        </>
      )}
    </motion.div>
  )
}
