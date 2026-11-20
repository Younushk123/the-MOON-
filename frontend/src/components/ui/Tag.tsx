import type { ReactNode } from 'react'

export type TagTone = 'good' | 'warn' | 'bad' | 'info' | 'mock'

export default function Tag({ tone = 'info', children, title }: { tone?: TagTone; children: ReactNode; title?: string }) {
  return (
    <span className={`schema-tag tone-${tone}`} title={title}>
      {children}
    </span>
  )
}
