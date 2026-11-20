import { AlertTriangle, Inbox, LoaderCircle } from 'lucide-react'

type Props = {
  kind: 'loading' | 'empty' | 'error'
  title?: string
  message?: string
  onRetry?: () => void
}

/** Shared loading / empty / error block for panels. Uses the existing dark theme. */
export default function StateNotice({ kind, title, message, onRetry }: Props) {
  const Icon = kind === 'loading' ? LoaderCircle : kind === 'error' ? AlertTriangle : Inbox
  const defaults = {
    loading: 'Loading…',
    empty: 'Nothing to show yet',
    error: 'Something went wrong',
  }

  return (
    <div className={`state-notice is-${kind}`} role={kind === 'error' ? 'alert' : 'status'}>
      <Icon size={22} className={kind === 'loading' ? 'state-spin' : undefined} />
      <strong>{title ?? defaults[kind]}</strong>
      {message && <p>{message}</p>}
      {kind === 'error' && onRetry && (
        <button type="button" className="secondary-button" onClick={onRetry}>
          Try again
        </button>
      )}
    </div>
  )
}
