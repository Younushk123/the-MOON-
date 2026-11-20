
import {
  API_BASE_URL,
  MOCK_LATENCY_MS,
  RAG_REQUEST_TIMEOUT_MS,
  REQUEST_TIMEOUT_MS,
  USE_MOCK,
} from '../config/env'

import { mockRoute } from '../data/mock/mockBackend'

import type {
  ApiEnvelope,
} from '../types/schemas'
// --------------------------------------------------
// API ERROR
// --------------------------------------------------

export class ApiError extends Error {
  errorCode?: string
  status?: number

  constructor(
    message: string,
    options: {
      errorCode?: string
      status?: number
    } = {},
  ) {
    super(message)

    this.name = 'ApiError'
    this.errorCode = options.errorCode
    this.status = options.status

    Object.setPrototypeOf(this, ApiError.prototype)
  }
}

// --------------------------------------------------
// HELPERS
// --------------------------------------------------

const sleep = (ms: number) =>
  new Promise<void>((resolve) => setTimeout(resolve, ms))

function createAbortError(): DOMException {
  return new DOMException(
    'Request was aborted.',
    'AbortError',
  )
}

function isEnvelope(
  value: unknown,
): value is ApiEnvelope<unknown> {
  if (!value || typeof value !== 'object') {
    return false
  }

  const envelope = value as Record<string, unknown>

  return (
    typeof envelope.success === 'boolean' &&
    'data' in envelope
  )
}

// --------------------------------------------------
// REAL API REQUEST
// --------------------------------------------------

async function realRequest(
  method: 'GET' | 'POST',
  path: string,
  body?: unknown,
  signal?: AbortSignal,
  timeoutMs = REQUEST_TIMEOUT_MS,
): Promise<{
  envelope: ApiEnvelope<unknown>
  status: number
}> {
  const isFormData =
    typeof FormData !== 'undefined' && body instanceof FormData

  if (signal?.aborted) {
    throw createAbortError()
  }

  const controller = new AbortController()

  const abortRequest = () => controller.abort()

  signal?.addEventListener('abort', abortRequest, {
    once: true,
  })

  const timeout = setTimeout(() => {
    controller.abort()
  }, timeoutMs)

  try {
    const response = await fetch(
      `${API_BASE_URL}${path}`,
      {
        method,

        headers: {
          Accept: 'application/json',

          ...(body !== undefined && !isFormData
            ? {
                'Content-Type': 'application/json',
              }
            : {}),
        },

        body: body === undefined
          ? undefined
          : isFormData
            ? body
            : JSON.stringify(body),

        signal: controller.signal,
      },
    )

    let json: unknown

    try {
      json = await response.json()
    } catch {
      json = null
    }

    if (!isEnvelope(json)) {
      if (!response.ok) {
        throw new ApiError(
          `API request failed (${response.status}).`,
          {
            status: response.status,
          },
        )
      }

      throw new ApiError(
        'Invalid API response. Expected a standard response envelope.',
        {
          status: response.status,
        },
      )
    }

    return {
      envelope: json,
      status: response.status,
    }
  } catch (error: unknown) {
    if (error instanceof ApiError) {
      throw error
    }

    if (
      error instanceof Error &&
      error.name === 'AbortError'
    ) {
      if (signal?.aborted) {
        throw error
      }

      throw new ApiError(
        'API request timed out. Please try again.',
      )
    }

    throw new ApiError(
      'Could not connect to the backend. Check that the server is running and the API URL is correct.',
    )
  } finally {
    clearTimeout(timeout)

    signal?.removeEventListener(
      'abort',
      abortRequest,
    )
  }
}

// --------------------------------------------------
// MOCK REQUEST
// --------------------------------------------------

async function mockRequest(
  method: 'GET' | 'POST',
  path: string,
  body?: unknown,
  signal?: AbortSignal,
): Promise<ApiEnvelope<unknown>> {
  if (signal?.aborted) {
    throw createAbortError()
  }

  await sleep(MOCK_LATENCY_MS)

  if (signal?.aborted) {
    throw createAbortError()
  }

  try {
    return mockRoute(method, path, body)
  } catch {
    throw new ApiError(
      'Mock API request failed. Check mockBackend configuration.',
    )
  }
}

// --------------------------------------------------
// MAIN API FUNCTION
// --------------------------------------------------

export async function callApi<T>(
  method: 'GET' | 'POST',
  path: string,
  body?: unknown,
  signal?: AbortSignal,
  timeoutMs = REQUEST_TIMEOUT_MS,
): Promise<T> {
  if (signal?.aborted) {
    throw createAbortError()
  }

  let envelope: ApiEnvelope<unknown>
  let status: number | undefined

  // MOCK MODE

  if (USE_MOCK) {
    envelope = await mockRequest(
      method,
      path,
      body,
      signal,
      timeoutMs,
    )
  }

  // REAL BACKEND MODE

  else {
    const result = await realRequest(
      method,
      path,
      body,
      signal,
      timeoutMs,
    )

    envelope = result.envelope
    status = result.status
  }

  // ERROR HANDLING
  // Supports both:
  // Full API: error.message / error.code
  // RAG API: message / error_code

  if (!envelope.success) {
    const message =
      envelope.error?.message ||
      envelope.message ||
      'The API reported an error.'

    const errorCode =
      envelope.error?.code ||
      envelope.error_code

    throw new ApiError(message, {
      errorCode,
      status,
    })
  }

  // SUCCESS RESPONSE

  if (envelope.data === null) {
    return null as T
  }

  return envelope.data as T
}
