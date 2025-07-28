import { IntelligentMockupJob, IntelligentMockupErrorType } from '../types';
import { INTELLIGENT_MOCKUP_ERRORS, INTELLIGENT_MOCKUP_TIMEOUTS } from '../constants';

/**
 * Get user-friendly error message based on error type
 */
export const getIntelligentMockupErrorMessage = (error?: IntelligentMockupJob['error']): string => {
  if (!error) return 'An unknown error occurred. Please try again.';
  
  const errorMessages: Record<IntelligentMockupErrorType, string> = {
    [INTELLIGENT_MOCKUP_ERRORS.TIMEOUT]: 
      'Processing took too long. This can happen with complex images or high server load. Please try again or use a simpler template.',
    [INTELLIGENT_MOCKUP_ERRORS.DETECTION_FAILED]: 
      'AI couldn\'t find suitable regions in the mockup template. Try using a template with clearer placement areas (like frames, t-shirts, or mugs).',
    [INTELLIGENT_MOCKUP_ERRORS.GRPC_ERROR]: 
      'Communication error with the AI service. This is usually temporary. Please wait a moment and try again.',
    [INTELLIGENT_MOCKUP_ERRORS.UNKNOWN]: 
      'An unexpected error occurred. Our team has been notified. Please try again later.'
  };
  
  return errorMessages[error.type] || error.message || errorMessages[INTELLIGENT_MOCKUP_ERRORS.UNKNOWN];
};

/**
 * Get suggested actions based on error type
 */
export const getErrorSuggestedActions = (error?: IntelligentMockupJob['error']): string[] => {
  if (!error) return ['Try again with a different template'];
  
  const suggestions: Record<IntelligentMockupErrorType, string[]> = {
    [INTELLIGENT_MOCKUP_ERRORS.TIMEOUT]: [
      'Try using a smaller image',
      'Use a simpler mockup template',
      'Try again during off-peak hours'
    ],
    [INTELLIGENT_MOCKUP_ERRORS.DETECTION_FAILED]: [
      'Use a mockup template with clear placement areas',
      'Try templates with frames, t-shirts, or product mockups',
      'Use the simple mockup option instead'
    ],
    [INTELLIGENT_MOCKUP_ERRORS.GRPC_ERROR]: [
      'Wait a few moments and retry',
      'Check your internet connection',
      'Try using the simple mockup option'
    ],
    [INTELLIGENT_MOCKUP_ERRORS.UNKNOWN]: [
      'Try again in a few minutes',
      'Use a different mockup template',
      'Contact support if the issue persists'
    ]
  };
  
  return suggestions[error.type] || suggestions[INTELLIGENT_MOCKUP_ERRORS.UNKNOWN];
};

/**
 * Check if a job has timed out
 */
export const hasJobTimedOut = (job: IntelligentMockupJob): boolean => {
  if (job.status !== 'processing' || !job.processingStartTime) return false;
  
  const startTime = job.processingStartTime.toMillis ? job.processingStartTime.toMillis() : job.processingStartTime;
  const processingTime = Date.now() - startTime;
  return processingTime > INTELLIGENT_MOCKUP_TIMEOUTS.MAX_PROCESSING_TIME;
};

/**
 * Format processing time for display
 */
export const formatProcessingTime = (startTime?: any, endTime?: any): string => {
  if (!startTime) return '0s';
  
  const start = startTime.toMillis ? startTime.toMillis() : startTime;
  const end = endTime ? (endTime.toMillis ? endTime.toMillis() : endTime) : Date.now();
  
  const duration = end - start;
  const seconds = Math.floor(duration / 1000);
  const minutes = Math.floor(seconds / 60);
  
  if (minutes > 0) {
    return `${minutes}m ${seconds % 60}s`;
  }
  return `${seconds}s`;
};

/**
 * Get progress percentage for processing jobs
 */
export const getProcessingProgress = (job: IntelligentMockupJob): number => {
  if (job.status !== 'processing' || !job.processingStartTime) return 0;
  
  const startTime = job.processingStartTime.toMillis ? job.processingStartTime.toMillis() : job.processingStartTime;
  const elapsed = Date.now() - startTime;
  const expectedDuration = 120000; // 2 minutes expected
  
  // Cap at 95% to avoid showing 100% while still processing
  return Math.min(95, Math.floor((elapsed / expectedDuration) * 100));
};

/**
 * Validate mockup template availability
 */
export const validateMockupTemplates = async (db: any): Promise<{ 
  hasTemplates: boolean; 
  templateCount: number;
  error?: string;
}> => {
  try {
    const { collection, getDocs, query } = await import('firebase/firestore');
    const mockupsQuery = query(collection(db, 'mockups'));
    const snapshot = await getDocs(mockupsQuery);
    
    return {
      hasTemplates: !snapshot.empty,
      templateCount: snapshot.size
    };
  } catch (error) {
    return {
      hasTemplates: false,
      templateCount: 0,
      error: 'Failed to check mockup templates'
    };
  }
};

/**
 * Get error analytics data
 */
export const getErrorAnalytics = (error: IntelligentMockupJob['error']) => {
  return {
    error_type: error?.type || 'unknown',
    error_message: error?.message || 'No message',
    has_details: !!error?.details,
    timestamp: new Date().toISOString()
  };
};