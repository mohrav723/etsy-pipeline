import { Timestamp } from 'firebase/firestore';

// Job-related types
export type JobStatus = 'pending_art_generation' | 'processing' | 'completed' | 'failed' | 'approved' | 'pending_review';
export type MockupJobStatus = 'pending_mockup_generation' | 'processing' | 'completed' | 'failed';
export type IntelligentMockupJobStatus = 'pending' | 'processing' | 'completed' | 'failed' | 'retried';

export interface Job {
  id: string;
  prompt: string;
  model?: string;
  guidance?: number;
  steps?: number;
  seed?: number;
  status: JobStatus;
  generatedImageUrl?: string;
  error?: string;
  createdAt: Timestamp;
  approved?: boolean;
  approvedAt?: Timestamp;
}

export interface MockupJob {
  id: string;
  jobId: string;
  mockupId: string;
  status: MockupJobStatus;
  mockupUrl?: string;
  error?: string;
  createdAt: Timestamp;
}

export interface Mockup {
  id: string;
  name: string;
  fileName: string;
  imageUrl: string;
  uploadedAt: Timestamp;
}

// Intelligent Mockup types
export type IntelligentMockupErrorType = 'timeout' | 'detection_failed' | 'grpc_error' | 'unknown';

export interface IntelligentMockupJob {
  id: string;
  status: IntelligentMockupJobStatus;
  original_job_id: string;  // Backend uses original_job_id
  artwork_url: string;  // Backend uses artwork_url
  mockup_template: string;  // Backend uses mockup_template
  sourcePrompt?: string;  // Keep for frontend display
  createdAt: Timestamp;
  processingStartTime?: Timestamp | null;
  processing_started_at?: Timestamp | null;  // Backend alternative field
  completionTime?: Timestamp | null;
  processing_completed_at?: Timestamp | null;  // Backend alternative field
  error?: {
    message: string;
    type: IntelligentMockupErrorType;
    details?: any;
  } | null;
  error_message?: string | null;  // Backend uses error_message
  result_url?: string | null;  // Backend uses result_url
  detected_regions?: number | null;  // Backend uses detected_regions as count
  selected_region?: string | null;  // Backend adds selected_region
  mockup_results?: Array<{  // New field for multiple results
    template_id: string;
    template_name: string;
    url: string;
    detected_regions: number;
    selected_region: string;
  }> | null;
  total_mockups_generated?: number | null;
  detected_regions_total?: number | null;
  detectedRegions?: Array<{  // Keep for compatibility
    label: string;
    confidence: number;
    bbox: [number, number, number, number];
  }> | null;
  templateUsed?: string;  // Keep for compatibility
  retriedAt?: Timestamp;
}

export interface DetectedRegion {
  label: string;
  confidence: number;
  bbox: [number, number, number, number]; // [x1, y1, x2, y2]
}

// Cost tracking types
export interface Cost {
  id: string;
  jobId: string;
  costType: 'bfl_generation' | 'storage_upload' | 'object_detection' | 'perspective_transform';
  amount: number;
  timestamp: Timestamp;
  details: {
    model?: string;
    steps?: number;
    success?: boolean;
    sizeBytes?: number;
    operation?: string;
  };
}

// Form types
export interface GenerationFormValues {
  prompt: string;
  model: string;
  guidance: number;
  steps: number;
  seed?: number;
}

export interface RegenerationFormValues extends GenerationFormValues {
  // Additional fields for regeneration if needed
}

// Error types
export interface AppError {
  message: string;
  code?: string;
  context?: string;
}

// Type guards
export const isIntelligentMockupJob = (job: any): job is IntelligentMockupJob => {
  return job && typeof job.status === 'string' && 
         ['pending', 'processing', 'completed', 'failed', 'retried'].includes(job.status) &&
         (job.original_job_id || job.sourceJobId) && (job.artwork_url || job.sourceImageUrl);
};

// Utility types
export type MockupType = 'simple' | 'intelligent';