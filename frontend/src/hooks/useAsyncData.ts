import { useCallback, useEffect, useState } from 'react'

export type AsyncStatus = 'idle' | 'loading' | 'success' | 'error'


export function useAsyncData<T>(
  fetcher: (signal: AbortSignal) => Promise<T>,
  deps: unknown[],
  enabled = true,
) {
  const [state, setState] = useState<{ status: AsyncStatus; data: T | null; error: string }>({
    status: enabled ? 'loading' : 'idle',
    data: null,
    error: '',
  })
  const [tick, setTick] = useState(0)

  useEffect(() => {
    if (!enabled) {
      setState({ status: 'idle', data: null, error: '' })
      return undefined
    }
    const controller = new AbortController()
    setState({ status: 'loading', data: null, error: '' })

    fetcher(controller.signal)
      .then((data) => {
        if (!controller.signal.aborted) setState({ status: 'success', data, error: '' })
      })
      .catch((error: any) => {
        if (controller.signal.aborted || error?.name === 'AbortError') return
        setState({ status: 'error', data: null, error: error?.message || 'Request failed.' })
      })

    return () => controller.abort()
    
  }, [...deps, tick, enabled])

  const reload = useCallback(() => setTick((value) => value + 1), [])
  return { ...state, reload }
}
