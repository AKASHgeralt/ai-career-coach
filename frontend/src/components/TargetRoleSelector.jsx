import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Target, Check, Loader } from 'lucide-react'
import { getTargetRoles, setTargetRole } from '../api/auth'

/**
 * Target role picker. The role list is fetched from the backend catalogue so
 * adding a role server-side needs no frontend change.
 *
 * onChange(updatedUser) fires after a successful save so parents can refresh
 * anything the role influences.
 */
export default function TargetRoleSelector({ current, onChange, compact = false }) {
  const [roles, setRoles] = useState([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    getTargetRoles()
      .then(setRoles)
      .catch(() => setError('Could not load the role list'))
      .finally(() => setLoading(false))
  }, [])

  const handlePick = async (slug) => {
    if (slug === current || saving) return
    setSaving(slug)
    setError('')
    try {
      const updated = await setTargetRole(slug)
      onChange?.(updated)
    } catch (err) {
      setError(err.response?.data?.detail || 'Could not save your target role')
    } finally {
      setSaving(null)
    }
  }

  if (loading) {
    return (
      <div className={`grid ${compact ? 'grid-cols-1 sm:grid-cols-2' : 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-3'} gap-px bg-line`}>
        {Array.from({ length: compact ? 4 : 6 }).map((_, i) => (
          <div key={i} className="bg-ink p-4 animate-pulse">
            <div className="h-3 w-28 bg-white/[0.06]" />
          </div>
        ))}
      </div>
    )
  }

  if (error && roles.length === 0) {
    return <p className="text-red-300 text-sm font-light">{error}</p>
  }

  return (
    <div>
      {error && <p className="text-red-300 text-xs font-light mb-3">{error}</p>}
      <div className={`grid ${compact ? 'grid-cols-1 sm:grid-cols-2' : 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-3'} gap-px bg-line`}>
        {roles.map(({ slug, label }) => {
          const active = slug === current
          return (
            <motion.button
              key={slug}
              whileTap={{ scale: 0.98 }}
              onClick={() => handlePick(slug)}
              disabled={!!saving}
              aria-pressed={active}
              className={`relative flex items-center gap-3 p-4 text-left transition disabled:opacity-60
                ${active
                  ? 'bg-accent/[0.10] text-white'
                  : 'bg-ink text-mist hover:bg-accent/[0.04] hover:text-white'}`}
            >
              <span
                className={`w-5 h-5 border flex items-center justify-center flex-shrink-0
                  ${active ? 'border-accent text-accent' : 'border-line2 text-transparent'}`}
              >
                {saving === slug
                  ? <Loader size={10} className="animate-spin text-accent" />
                  : <Check size={11} />}
              </span>
              <span className="text-sm font-light">{label}</span>
              {active && <Target size={12} className="text-accent ml-auto flex-shrink-0" />}
            </motion.button>
          )
        })}
      </div>
    </div>
  )
}
