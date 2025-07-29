import { Timestamp } from 'firebase/firestore';
import {
  IntelligentMockupJob,
  IntelligentMockupJobStatus,
  IntelligentMockupErrorType,
} from '../types';

// Helper to create timestamp
const createTimestamp = (date: Date = new Date()): Timestamp => {
  return Timestamp.fromDate(date);
};

// Test data for different intelligent mockup job states
export const mockIntelligentMockupJobs: Record<
  IntelligentMockupJobStatus | 'various',
  IntelligentMockupJob[]
> = {
  pending: [
    {
      id: 'intel-mock-1',
      status: 'pending',
      sourceJobId: 'job-123',
      sourceImageUrl: 'https://example.com/artwork1.png',
      sourcePrompt: 'A beautiful sunset over mountains',
      createdAt: createTimestamp(),
      processingStartTime: null,
      completionTime: null,
      error: null,
      resultUrl: null,
      detectedRegions: null,
      templateUsed: 'template-001',
    },
  ],

  processing: [
    {
      id: 'intel-mock-2',
      status: 'processing',
      sourceJobId: 'job-456',
      sourceImageUrl: 'https://example.com/artwork2.png',
      sourcePrompt: 'Abstract geometric pattern',
      createdAt: createTimestamp(new Date(Date.now() - 60000)), // 1 minute ago
      processingStartTime: createTimestamp(new Date(Date.now() - 30000)), // 30 seconds ago
      completionTime: null,
      error: null,
      resultUrl: null,
      detectedRegions: null,
      templateUsed: 'template-002',
    },
  ],

  completed: [
    {
      id: 'intel-mock-3',
      status: 'completed',
      sourceJobId: 'job-789',
      sourceImageUrl: 'https://example.com/artwork3.png',
      sourcePrompt: 'Vintage botanical illustration',
      createdAt: createTimestamp(new Date(Date.now() - 300000)), // 5 minutes ago
      processingStartTime: createTimestamp(new Date(Date.now() - 280000)),
      completionTime: createTimestamp(new Date(Date.now() - 180000)), // 3 minutes ago
      error: null,
      resultUrl: 'https://example.com/intelligent-mockup-result.png',
      detectedRegions: [
        {
          label: 'picture_frame',
          confidence: 0.95,
          bbox: [100, 150, 400, 450],
        },
        {
          label: 'wall',
          confidence: 0.87,
          bbox: [0, 0, 800, 600],
        },
      ],
      templateUsed: 'template-003',
    },
  ],

  failed: [
    {
      id: 'intel-mock-4',
      status: 'failed',
      sourceJobId: 'job-101',
      sourceImageUrl: 'https://example.com/artwork4.png',
      sourcePrompt: 'Modern minimalist design',
      createdAt: createTimestamp(new Date(Date.now() - 600000)), // 10 minutes ago
      processingStartTime: createTimestamp(new Date(Date.now() - 580000)),
      completionTime: createTimestamp(new Date(Date.now() - 300000)),
      error: {
        message: 'Processing took too long. This can happen with complex images.',
        type: 'timeout' as IntelligentMockupErrorType,
        details: { processingTime: 300000 },
      },
      resultUrl: null,
      detectedRegions: null,
      templateUsed: 'template-004',
    },
    {
      id: 'intel-mock-5',
      status: 'failed',
      sourceJobId: 'job-102',
      sourceImageUrl: 'https://example.com/artwork5.png',
      sourcePrompt: 'Watercolor landscape',
      createdAt: createTimestamp(new Date(Date.now() - 900000)), // 15 minutes ago
      processingStartTime: createTimestamp(new Date(Date.now() - 880000)),
      completionTime: createTimestamp(new Date(Date.now() - 800000)),
      error: {
        message: "AI couldn't find suitable regions in the mockup template.",
        type: 'detection_failed' as IntelligentMockupErrorType,
        details: { detectedRegions: 0 },
      },
      resultUrl: null,
      detectedRegions: [],
      templateUsed: 'template-005',
    },
  ],

  retried: [
    {
      id: 'intel-mock-6',
      status: 'retried',
      sourceJobId: 'job-103',
      sourceImageUrl: 'https://example.com/artwork6.png',
      sourcePrompt: 'Digital art composition',
      createdAt: createTimestamp(new Date(Date.now() - 1200000)), // 20 minutes ago
      processingStartTime: createTimestamp(new Date(Date.now() - 1180000)),
      completionTime: createTimestamp(new Date(Date.now() - 900000)),
      error: {
        message: 'gRPC message size exceeded limit',
        type: 'grpc_error' as IntelligentMockupErrorType,
        details: { messageSize: 8388608, limit: 4194304 },
      },
      resultUrl: null,
      detectedRegions: null,
      templateUsed: 'template-006',
      retriedAt: createTimestamp(new Date(Date.now() - 600000)),
    },
  ],

  various: [
    // Mix of different statuses for testing lists
    {
      id: 'intel-mock-7',
      status: 'completed',
      sourceJobId: 'job-201',
      sourceImageUrl: 'https://example.com/artwork7.png',
      sourcePrompt: 'Cat in space',
      createdAt: createTimestamp(new Date(Date.now() - 7200000)), // 2 hours ago
      processingStartTime: createTimestamp(new Date(Date.now() - 7180000)),
      completionTime: createTimestamp(new Date(Date.now() - 7000000)),
      error: null,
      resultUrl: 'https://example.com/mockup-cat-space.png',
      detectedRegions: [
        {
          label: 't_shirt',
          confidence: 0.92,
          bbox: [50, 100, 350, 500],
        },
      ],
      templateUsed: 'template-tshirt-001',
    },
    {
      id: 'intel-mock-8',
      status: 'processing',
      sourceJobId: 'job-202',
      sourceImageUrl: 'https://example.com/artwork8.png',
      sourcePrompt: 'Retro gaming pixel art',
      createdAt: createTimestamp(new Date(Date.now() - 45000)), // 45 seconds ago
      processingStartTime: createTimestamp(new Date(Date.now() - 20000)),
      completionTime: null,
      error: null,
      resultUrl: null,
      detectedRegions: null,
      templateUsed: 'template-poster-001',
    },
    {
      id: 'intel-mock-9',
      status: 'pending',
      sourceJobId: 'job-203',
      sourceImageUrl: 'https://example.com/artwork9.png',
      sourcePrompt: 'Japanese cherry blossoms',
      createdAt: createTimestamp(new Date(Date.now() - 5000)), // 5 seconds ago
      processingStartTime: null,
      completionTime: null,
      error: null,
      resultUrl: null,
      detectedRegions: null,
      templateUsed: 'template-mug-001',
    },
  ],
};

// Helper functions for testing
export const getRandomIntelligentMockupJob = (): IntelligentMockupJob => {
  const allJobs = Object.values(mockIntelligentMockupJobs).flat();
  return allJobs[Math.floor(Math.random() * allJobs.length)];
};

export const createMockIntelligentJob = (
  overrides: Partial<IntelligentMockupJob> = {}
): IntelligentMockupJob => {
  return {
    id: `intel-mock-${Date.now()}`,
    status: 'pending',
    sourceJobId: `job-${Date.now()}`,
    sourceImageUrl: 'https://example.com/test-artwork.png',
    sourcePrompt: 'Test artwork prompt',
    createdAt: createTimestamp(),
    processingStartTime: null,
    completionTime: null,
    error: null,
    resultUrl: null,
    detectedRegions: null,
    templateUsed: 'template-test',
    ...overrides,
  };
};

// Simulate status progression for testing
export const simulateJobProgression = (job: IntelligentMockupJob): IntelligentMockupJob => {
  const now = new Date();

  switch (job.status) {
    case 'pending':
      return {
        ...job,
        status: 'processing',
        processingStartTime: createTimestamp(now),
      };

    case 'processing': {
      // 80% chance of success, 20% chance of failure
      const success = Math.random() > 0.2;
      if (success) {
        return {
          ...job,
          status: 'completed',
          completionTime: createTimestamp(now),
          resultUrl: `https://example.com/result-${job.id}.png`,
          detectedRegions: [
            {
              label: 'detected_object',
              confidence: 0.85 + Math.random() * 0.15,
              bbox: [
                Math.floor(Math.random() * 100),
                Math.floor(Math.random() * 100),
                Math.floor(Math.random() * 100) + 200,
                Math.floor(Math.random() * 100) + 200,
              ],
            },
          ],
        };
      } else {
        const errorTypes: IntelligentMockupErrorType[] = [
          'timeout',
          'detection_failed',
          'grpc_error',
        ];
        const errorType = errorTypes[Math.floor(Math.random() * errorTypes.length)];
        return {
          ...job,
          status: 'failed',
          completionTime: createTimestamp(now),
          error: {
            message: `Test error: ${errorType}`,
            type: errorType,
            details: { test: true },
          },
        };
      }
    }

    default:
      return job;
  }
};
