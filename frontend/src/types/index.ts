import { Timestamp } from 'firebase/firestore';

// Job-related types
export type JobStatus = 'pending_art_generation' | 'processing' | 'completed' | 'failed' | 'approved' | 'pending_review';
export type MockupJobStatus = 'pending_mockup_generation' | 'processing' | 'completed' | 'failed';

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