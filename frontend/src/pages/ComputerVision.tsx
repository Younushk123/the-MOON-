import { useEffect, useState, type FormEvent, type ChangeEvent } from 'react'
import { Film, Image as ImageIcon, ScanEye, Upload } from 'lucide-react'
import CvResultCard from '../components/ui/CvResultCard'
import Tag from '../components/ui/Tag'
import { analyzeFlexImage, getFlexVideoJob, startFlexVideoAnalysis } from '../services/api'
import type { CvAnalysisJobStatus, CvResult } from '../types/schemas'
import '../styles/ComputerVision.css'

const MAX_VIDEO_BYTES = 25 * 1024 * 1024
const MAX_IMAGE_BYTES = 25 * 1024 * 1024
const JOB_POLL_INTERVAL_MS = 2000
const MAX_JOB_POLLS = 420

type AnalysisState = 'idle' | 'loading' | 'error' | 'success'

const delay = (milliseconds: number) =>
  new Promise<void>((resolve) => setTimeout(resolve, milliseconds))

export default function ComputerVision() {
  const [video, setVideo] = useState<File | null>(null)
  const [previewUrl, setPreviewUrl] = useState('')
  const [mediaId, setMediaId] = useState('MEDIA-001')
  const [status, setStatus] = useState<AnalysisState>('idle')
  const [jobId, setJobId] = useState<string | null>(null)
  const [jobStatus, setJobStatus] = useState<CvAnalysisJobStatus | null>(null)
  const [result, setResult] = useState<CvResult | null>(null)
  const [error, setError] = useState('')
  const [image, setImage] = useState<File | null>(null)
  const [imagePreviewUrl, setImagePreviewUrl] = useState('')
  const [imageMediaId, setImageMediaId] = useState('MEDIA-002')
  const [imageStatus, setImageStatus] = useState<AnalysisState>('idle')
  const [imageResult, setImageResult] = useState<CvResult | null>(null)
  const [imageError, setImageError] = useState('')

  useEffect(() => {
    if (!video) {
      setPreviewUrl('')
      return
    }

    const url = URL.createObjectURL(video)
    setPreviewUrl(url)
    return () => URL.revokeObjectURL(url)
  }, [video])

  useEffect(() => {
    if (!image) {
      setImagePreviewUrl('')
      return
    }

    const url = URL.createObjectURL(image)
    setImagePreviewUrl(url)
    return () => URL.revokeObjectURL(url)
  }, [image])

  function selectVideo(event: ChangeEvent<HTMLInputElement>) {
    const selected = event.target.files?.[0] ?? null
    setJobId(null)
    setJobStatus(null)
    setResult(null)
    setError('')

    if (!selected) {
      setVideo(null)
      setStatus('idle')
      return
    }

    if (!selected.name.toLowerCase().endsWith('.mp4')) {
      setVideo(null)
      setStatus('error')
      setError('Please select an MP4 video.')
      return
    }

    if (selected.size > MAX_VIDEO_BYTES) {
      setVideo(null)
      setStatus('error')
      setError('The video exceeds the 25 MB upload limit.')
      return
    }

    setVideo(selected)
    setStatus('idle')
  }

  function selectImage(event: ChangeEvent<HTMLInputElement>) {
    const selected = event.target.files?.[0] ?? null
    setImageResult(null)
    setImageError('')

    if (!selected) {
      setImage(null)
      setImageStatus('idle')
      return
    }

    if (!/\.(jpe?g|png|webp)$/i.test(selected.name)) {
      setImage(null)
      setImageStatus('error')
      setImageError('Please select a JPEG, PNG, or WebP image.')
      return
    }

    if (selected.size > MAX_IMAGE_BYTES) {
      setImage(null)
      setImageStatus('error')
      setImageError('The image exceeds the 25 MB upload limit.')
      return
    }

    setImage(selected)
    setImageStatus('idle')
  }

  async function waitForJob(id: string) {
    for (let attempt = 0; attempt < MAX_JOB_POLLS; attempt += 1) {
      const job = await getFlexVideoJob(id)
      setJobStatus(job.status)

      if (job.status === 'completed') {
        if (!job.result) {
          throw new Error('The analysis job completed without returning a result.')
        }
        setResult(job.result)
        setStatus('success')
        setError('')
        return
      }

      if (job.status === 'failed') {
        setError(job.error || 'FLEX video analysis failed.')
        setStatus('error')
        return
      }

      await delay(JOB_POLL_INTERVAL_MS)
    }

    throw new Error('Analysis is still running. Check its status again shortly.')
  }

  async function submitImage(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!image || !imageMediaId.trim()) return

    setImageStatus('loading')
    setImageResult(null)
    setImageError('')
    try {
      const analysis = await analyzeFlexImage(image, imageMediaId.trim())
      setImageResult(analysis)
      setImageStatus('success')
    } catch (requestError: unknown) {
      setImageError(
        requestError instanceof Error
          ? requestError.message
          : 'Image analysis failed.',
      )
      setImageStatus('error')
    }
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!video || !mediaId.trim()) return

    setStatus('loading')
    setJobId(null)
    setJobStatus(null)
    setResult(null)
    setError('')
    try {
      const job = await startFlexVideoAnalysis(video, mediaId.trim())
      setJobId(job.job_id)
      setJobStatus(job.status)
      await waitForJob(job.job_id)
    } catch (requestError: unknown) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : 'Video analysis failed.',
      )
      setStatus('error')
    }
  }

  async function checkJobStatus() {
    if (!jobId) return
    setStatus('loading')
    setError('')
    try {
      await waitForJob(jobId)
    } catch (requestError: unknown) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : 'Could not retrieve the analysis status.',
      )
      setStatus('error')
    }
  }

  return (
    <div className="page cv-page">
      <div className="page-heading">
        <div>
          <p className="eyebrow">COMPUTER VISION · NASA FLEX PSI-69</p>
          <h1>Microgravity Flame Explorer</h1>
          <p>Analyze FLEX videos and still images to inspect candidate luminous regions.</p>
        </div>
        <Tag tone="info">FLEX profile</Tag>
      </div>

      <div className="cv-page-grid">
        <section className="panel cv-upload-panel">
          <div className="panel-title">
            <Film size={17} />
            <h3>Analyze a FLEX video</h3>
          </div>

          <div className="cv-profile">
            <strong>Supported recording</strong>
            <span>960 × 540 · 30 FPS · 693 frames · MP4</span>
          </div>

          <form onSubmit={submit}>
            <label className="cv-field-label" htmlFor="cv-media-id">Media ID</label>
            <input
              className="cv-text-input"
              id="cv-media-id"
              value={mediaId}
              onChange={(event) => {
                setMediaId(event.target.value)
                setJobId(null)
                setJobStatus(null)
                setResult(null)
                setError('')
                setStatus('idle')
              }}
              maxLength={64}
              disabled={status === 'loading'}
              required
            />
            <small className="cv-field-hint">
              Defaults to MEDIA-001 for the bundled FLEX video. Change it if your media registry uses another ID.
            </small>

            <label className="cv-field-label" htmlFor="cv-video-file">Video file</label>
            <input
              className="cv-file-input"
              id="cv-video-file"
              type="file"
              accept=".mp4,video/mp4"
              onChange={selectVideo}
              disabled={status === 'loading'}
            />
            <label className="cv-file-picker" htmlFor="cv-video-file">
              <Upload size={17} />
              <span>{video ? video.name : 'Choose an MP4 video (maximum 25 MB)'}</span>
            </label>

            {previewUrl && (
              <video
                className="cv-video-preview"
                src={previewUrl}
                controls
                preload="metadata"
                aria-label="Selected FLEX video preview"
              />
            )}

            <p className="cv-upload-note">
              The FLEX analyzer is recording-specific, not a general video detector. Annotated exports and other
              recordings are not supported. The upload is temporary and deleted after analysis.
            </p>

            <button
              className="primary-button cv-submit"
              type="submit"
              disabled={!video || !mediaId.trim() || status === 'loading'}
            >
              <ScanEye size={16} />
              {status === 'loading' ? 'Analyzing 693 frames…' : 'Upload & analyze video'}
            </button>
          </form>
        </section>

        <section className="panel cv-result-panel" aria-live="polite">
          <div className="panel-title">
            <ScanEye size={17} />
            <h3>Analysis result</h3>
          </div>

          {status === 'loading' && (
            <div className="cv-result-state">
              <strong>
                {jobStatus === 'queued'
                  ? 'Video analysis queued…'
                  : jobStatus === 'processing'
                    ? 'Analyzing 693 frames…'
                    : 'Uploading video…'}
              </strong>
              <p>The analysis runs in the background; this page checks its status automatically.</p>
              {jobId && <small>Job ID: {jobId}</small>}
            </div>
          )}
          {status === 'error' && (
            <div className="cv-result-error" role="alert">
              <p>{error}</p>
              {jobId && (jobStatus === 'queued' || jobStatus === 'processing') && (
                <button
                  className="secondary-button"
                  type="button"
                  onClick={() => void checkJobStatus()}
                >
                  Check analysis status
                </button>
              )}
            </div>
          )}
          {status === 'success' && result && <CvResultCard result={result} />}
          {status === 'idle' && (
            <div className="cv-result-state">
              <strong>No video analyzed yet</strong>
              <p>Select the supported FLEX MP4 to preview it and start analysis.</p>
            </div>
          )}
        </section>
      </div>

      <div className="cv-page-grid cv-image-grid">
        <section className="panel cv-upload-panel">
          <div className="panel-title">
            <ImageIcon size={17} />
            <h3>Analyze a FLEX image</h3>
          </div>

          <div className="cv-profile">
            <strong>Supported images</strong>
            <span>JPEG · PNG · WebP · up to 25 MB and 12 megapixels</span>
          </div>

          <form onSubmit={submitImage}>
            <label className="cv-field-label" htmlFor="cv-image-media-id">Media ID</label>
            <input
              className="cv-text-input"
              id="cv-image-media-id"
              value={imageMediaId}
              onChange={(event) => {
                setImageMediaId(event.target.value)
                setImageResult(null)
                setImageError('')
                setImageStatus('idle')
              }}
              maxLength={64}
              disabled={imageStatus === 'loading'}
              required
            />
            <small className="cv-field-hint">
              Defaults to MEDIA-002 for the bundled FLEX companion image. Change it if your media registry uses another ID.
            </small>

            <label className="cv-field-label" htmlFor="cv-image-file">Image file</label>
            <input
              className="cv-file-input"
              id="cv-image-file"
              type="file"
              accept=".jpg,.jpeg,.png,.webp,image/jpeg,image/png,image/webp"
              onChange={selectImage}
              disabled={imageStatus === 'loading'}
            />
            <label className="cv-file-picker" htmlFor="cv-image-file">
              <Upload size={17} />
              <span>{image ? image.name : 'Choose a JPEG, PNG, or WebP image'}</span>
            </label>

            {imagePreviewUrl && (
              <img
                className="cv-image-preview"
                src={imagePreviewUrl}
                alt="Selected FLEX still-image preview"
              />
            )}

            <p className="cv-upload-note">
              Analysis measures the largest red-excess luminous region; it does not confirm that the region is a flame.
              Pixel measurements are not physical dimensions.
            </p>

            <button
              className="primary-button cv-submit"
              type="submit"
              disabled={!image || !imageMediaId.trim() || imageStatus === 'loading'}
            >
              <ScanEye size={16} />
              {imageStatus === 'loading' ? 'Analyzing image…' : 'Upload & analyze image'}
            </button>
          </form>
        </section>

        <section className="panel cv-result-panel" aria-live="polite">
          <div className="panel-title">
            <ScanEye size={17} />
            <h3>Image analysis result</h3>
          </div>

          {imageStatus === 'loading' && (
            <div className="cv-result-state">
              <strong>Analyzing image…</strong>
              <p>The still-image pipeline is measuring candidate luminous regions.</p>
            </div>
          )}
          {imageStatus === 'error' && (
            <div className="cv-result-error" role="alert">
              <p>{imageError}</p>
            </div>
          )}
          {imageStatus === 'success' && imageResult && <CvResultCard result={imageResult} />}
          {imageStatus === 'idle' && (
            <div className="cv-result-state">
              <strong>No image analyzed yet</strong>
              <p>Select a still image to preview it and start analysis.</p>
            </div>
          )}
        </section>
      </div>
    </div>
  )
}
