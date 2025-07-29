import React, { useState } from 'react';
import { Button, message } from 'antd';
import { LoadingOutlined, RobotOutlined, WarningOutlined } from '@ant-design/icons';
import { db } from '../firebase';
import {
  collection,
  addDoc,
  serverTimestamp,
  query,
  getDocs,
  doc,
  updateDoc,
} from 'firebase/firestore';
import { ErrorService } from '../services/errorService';
import { JOB_STATUS, INTELLIGENT_MOCKUP_STATUS } from '../constants';

type MockupButtonProps = {
  jobId: string;
  imageUrl: string;
  prompt?: string;
  size?: 'small' | 'middle' | 'large';
  type?: 'default' | 'primary' | 'text' | 'link';
  disabled?: boolean;
  style?: React.CSSProperties;
  block?: boolean;
};

const MockupButton: React.FC<MockupButtonProps> = ({
  jobId,
  imageUrl,
  prompt = '',
  size = 'large',
  type = 'default',
  disabled = false,
  style = { backgroundColor: '#5865f2', borderColor: '#5865f2', color: 'white' },
  block = false,
}) => {
  const [isGeneratingMockups, setIsGeneratingMockups] = useState(false);

  const handleGenerateMockups = async () => {
    setIsGeneratingMockups(true);

    try {
      // Validate image URL
      if (!imageUrl || imageUrl === 'undefined' || imageUrl === 'null') {
        message.error({
          content: 'No image URL available. Please ensure the artwork has been generated.',
          duration: 5,
          icon: <WarningOutlined style={{ color: '#ff4d4f' }} />,
        });
        setIsGeneratingMockups(false);
        return;
      }
      // First, check if there are available mockup templates
      const mockupsQuery = query(collection(db, 'mockups'));
      const mockupsSnapshot = await getDocs(mockupsQuery);

      if (mockupsSnapshot.empty) {
        message.error({
          content: 'No mockup templates available. Please upload mockup templates first.',
          duration: 5,
          icon: <WarningOutlined style={{ color: '#faad14' }} />,
        });
        setIsGeneratingMockups(false);
        return;
      }

      // Validate intelligent mockup requirements
      if (mockupsSnapshot.size === 1) {
        message.warning(
          'Only one template available. For best results with AI mockups, upload templates with clear placement areas (frames, t-shirts, mugs).'
        );
      }

      // Debug logging
      // console.log('Creating intelligent mockup job with:', {
      //   jobId,
      //   imageUrl,
      //   prompt,
      //   templateId: mockupsSnapshot.docs[0]?.id,
      // });

      // Create intelligent mockup job
      const intelligentJobData = {
        status: INTELLIGENT_MOCKUP_STATUS.PENDING,
        artwork_url: imageUrl, // Backend expects artwork_url, not sourceImageUrl
        mockup_template: mockupsSnapshot.docs[0]?.id || 'default', // Backend expects mockup_template
        original_job_id: jobId, // Backend expects original_job_id, not sourceJobId
        sourcePrompt: prompt,
        createdAt: serverTimestamp(),
        processingStartTime: null,
        completionTime: null,
        error: null,
        resultUrl: null,
        detectedRegions: null,
      };

      await addDoc(collection(db, 'intelligent_mockup_jobs'), intelligentJobData);
      message.success({
        content:
          'AI-powered mockup generation started! This typically takes 3-7 minutes. Check the Drafts tab for progress.',
        duration: 8,
        icon: <RobotOutlined style={{ color: '#52c41a' }} />,
      });

      // Auto-approve the image when generating mockups
      try {
        const jobRef = doc(db, 'jobs', jobId);
        await updateDoc(jobRef, { status: JOB_STATUS.APPROVED });
      } catch (_approveError) {
        // Don't fail the whole operation if approval fails
      }

      // Show progress message
      setTimeout(() => {
        message.info('Check the Drafts tab to see your mockup progress!');
      }, 2000);
    } catch (error) {
      ErrorService.showError(error, 'Mockup generation');
    } finally {
      setIsGeneratingMockups(false);
    }
  };

  return (
    <Button
      icon={isGeneratingMockups ? <LoadingOutlined /> : <RobotOutlined />}
      loading={isGeneratingMockups}
      disabled={disabled || isGeneratingMockups}
      onClick={handleGenerateMockups}
      size={size}
      type={type}
      style={style}
      block={block}
    >
      {isGeneratingMockups ? 'Generating...' : 'Generate AI Mockups'}
    </Button>
  );
};

export default MockupButton;
