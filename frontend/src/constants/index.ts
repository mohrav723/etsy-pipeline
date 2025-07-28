// File size limits
export const FILE_SIZE_LIMIT_MB = 10;
export const FILE_SIZE_LIMIT_BYTES = FILE_SIZE_LIMIT_MB * 1024 * 1024;

// Pagination
export const JOBS_PER_PAGE = 20;

// File types
export const ALLOWED_FILE_TYPES = ['image/jpeg', 'image/png', 'image/webp'];

// Job status constants
export const JOB_STATUS = {
  PENDING_ART: 'pending_art_generation',
  PROCESSING: 'processing',
  COMPLETED: 'completed',
  FAILED: 'failed',
  APPROVED: 'approved',
  PENDING_REVIEW: 'pending_review'
} as const;

// Mockup job status
export const MOCKUP_STATUS = {
  PENDING: 'pending_mockup_generation',
  PROCESSING: 'processing',
  COMPLETED: 'completed',
  FAILED: 'failed'
} as const;

// API limits
export const MAX_PROMPT_LENGTH = 1000;
export const MIN_PROMPT_LENGTH = 3;

// Generation parameters
export const GENERATION_DEFAULTS = {
  aspectRatio: '16:9',
  steps: 28,
  guidance: 3,
  safetyTolerance: 2,
  seed: 42,
  promptUpsampling: false
} as const;

// Timeouts
export const REGENERATION_TIMEOUT_MS = 30000; // 30 seconds
export const COST_REFRESH_INTERVAL_MS = 60000; // 1 minute

// Slider ranges
export const SLIDER_RANGES = {
  steps: { min: 1, max: 50 },
  guidance: { min: 1.5, max: 5, step: 0.1 },
  safetyTolerance: { min: 0, max: 6, step: 1 }
} as const;

// Aspect ratios
export const ASPECT_RATIOS = [
  { value: '16:9', label: '16:9 (Landscape)' },
  { value: '1:1', label: '1:1 (Square)' },
  { value: '9:16', label: '9:16 (Portrait)' }
] as const;

// Style constants
export const CARD_HEIGHT_FIT = 'fit-content';
export const IMAGE_PREVIEW_HEIGHT = '200px';
export const MODAL_IMAGE_MAX_HEIGHT = '500px';