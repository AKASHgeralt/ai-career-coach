/**
 * Single source of truth mapping a dashboard section's label to its URL.
 *
 * Labels are what the sidebar and every "go here next" call-to-action use;
 * paths are what the router needs. Keeping both in one place means adding a
 * section touches one file.
 */
export const PATH_FOR = {
  'Dashboard': '/dashboard',
  'Resumes': '/dashboard/resumes',
  'Skill Gap': '/dashboard/skill-gap',
  'Roadmap': '/dashboard/roadmap',
  'Interview': '/dashboard/interview',
  'GitHub': '/dashboard/github',
  'Settings': '/dashboard/settings',
}

export const LABEL_FOR = Object.fromEntries(
  Object.entries(PATH_FOR).map(([label, path]) => [path, label])
)
