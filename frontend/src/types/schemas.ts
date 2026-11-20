
export type SourceType =
  | 'dataset'
  | 'research_paper'
  | 'technical_report'
  | 'webpage'

export type AccessStatus =
  | 'accessible'
  | 'restricted'
  | 'unavailable'
  | 'unknown'

export type VerificationStatus =
  | 'metadata_verified'
  | 'content_verified'
  | 'unverified'

export type IngestionStatus =
  | 'not_ingested'
  | 'ingested'
  | 'partially_ingested'
  | 'failed'

export type ComparisonStatus =
  | 'success'
  | 'partial'
  | 'not_comparable'

export type EvidenceStatus =
  | 'supported'
  | 'partially_supported'
  | 'insufficient_evidence'

export type ExperimentDataStatus = string
export type MeasurementStatus = string
export type AnalysisStatus = string
export type AnalysisType = string
export type InsightConfidence = string
export type CvProcessingStatus = string
export type CvCalibrationStatus = string

// Experiments

export interface Experiment {
  experiment_id: string
  name: string
  investigation: string
  program: string
  description: string
  platform: string
  source_ids: string[]
  data_status: ExperimentDataStatus
  available_measurements: string[]
  limitations: string[]
  last_updated: string
}

// Measurements

export interface MeasurementConditions {
  fuel: string | null
  pressure: number | null
  temperature: number | null
  flow_velocity: number | null
}

export interface Measurement {
  measurement_id: string
  experiment_id: string
  variable: string
  value: number | null
  unit: string
  timestamp: string | number | null
  conditions: MeasurementConditions
  source_id: string
  measurement_status: MeasurementStatus
  notes: string[]
}

// Sources

export interface Source {
  source_id: string
  title: string
  url: string | null
  publisher: string
  source_type: SourceType
  experiment_id: string
  access_status: AccessStatus
  verification_status: VerificationStatus
  ingestion_status: IngestionStatus
  publication_date: string | null
}

// Analysis

export interface AnalysisMetric {
  metric: string
  variable: string
  value: number | null
  unit: string
}

export interface AnalysisDataQuality {
  missing_values: number
  validation_passed: boolean
  warnings: string[]
}

export interface AnalysisResult {
  analysis_id: string
  experiment_id: string
  analysis_type: AnalysisType
  status: AnalysisStatus
  results: AnalysisMetric[]
  data_quality: AnalysisDataQuality
  source_ids: string[]
  limitations: string[]
}

// Comparison

export interface ComparedVariable {
  variable: string
  unit: string
  comparable: boolean
  reason: string
}

export interface Comparison {
  comparison_id: string
  experiment_ids: string[]
  status: ComparisonStatus
  compared_variables: ComparedVariable[]
  findings: string[]
  warnings: string[]
  source_ids: string[]
}

// Insights

export interface SupportingEvidence {
  source_id: string
  experiment_id: string | null
  evidence_text: string
  url: string | null
}

export interface Insight {
  insight_id: string
  question: string
  claim: string
  supporting_evidence: SupportingEvidence[]
  fire_safety_relevance: string
  limitations: string[]
  confidence: InsightConfidence
  evidence_status: EvidenceStatus
}

// Computer Vision

export interface CvFeatures {
  area_pixels: number | null
  width_pixels: number | null
  height_pixels: number | null
  brightness_mean: number | null
}

export interface CvResult {
  cv_result_id: string
  experiment_id: string
  media_id: string
  processing_status: CvProcessingStatus
  detected: boolean | null
  features: CvFeatures
  method: string | null
  calibration_status: CvCalibrationStatus
  limitations: string[]
  source_ids: string[]
}

export type CvAnalysisJobStatus =
  | 'queued'
  | 'processing'
  | 'completed'
  | 'failed'

export interface CvAnalysisJob {
  job_id: string
  status: CvAnalysisJobStatus
  result: CvResult | null
  error: string | null
}

// API Response Envelope

export interface ApiFailure {
  code?: string
  message: string
  details?: Record<string, unknown>[] | null
}

export interface ApiMeta {
  schema_version?: string
  data_mode?: 'mock' | 'psi' | null
}

export interface ApiEnvelope<T> {
  success: boolean
  data: T | null

  // Full backend response
  error?: ApiFailure | null
  meta?: ApiMeta

  // Legacy FastAPI RAG response
  message?: string
  error_code?: string
}

// API Requests

export interface ComparisonRequest {
  experiment_ids: string[]
  variables?: string[]
}

export interface AskRequest {
  question: string
  experiment_ids?: string[]
  validated_findings?: Record<string, unknown>[]
  top_k?: number
}

export interface InsightRequest {
  question: string
  experiment_ids?: string[]
  experiment_id?: string
  analysis_id?: string
}

export interface AnalysisRequest {
  experiment_id: string
  analysis_type?: AnalysisType
}

export interface VisionRequest {
  experiment_id: string
  media_id: string
}

// Health

export type HealthData = Record<string, unknown> | null
