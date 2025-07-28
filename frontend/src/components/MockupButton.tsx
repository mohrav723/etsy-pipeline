import React, { useState } from 'react';
import { Button, message, Modal, Radio, Space, Typography } from 'antd';
import { FileImageOutlined, LoadingOutlined, RobotOutlined, WarningOutlined } from '@ant-design/icons';
import { db } from '../firebase';
import { collection, addDoc, serverTimestamp, query, getDocs, doc, updateDoc } from 'firebase/firestore';
import { ErrorService } from '../services/errorService';
import { MOCKUP_STATUS, JOB_STATUS, INTELLIGENT_MOCKUP_STATUS } from '../constants';
import { MockupType } from '../types';

const { Text } = Typography;

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
  block = false
}) => {
  const [isGeneratingMockups, setIsGeneratingMockups] = useState(false);
  const [showTypeSelection, setShowTypeSelection] = useState(false);
  const [mockupType, setMockupType] = useState<MockupType>('simple');

  const handleButtonClick = () => {
    setShowTypeSelection(true);
  };

  const handleGenerateMockups = async () => {
    setShowTypeSelection(false);
    setIsGeneratingMockups(true);
    
    try {
      // Validate image URL
      if (!imageUrl || imageUrl === 'undefined' || imageUrl === 'null') {
        message.error({
          content: 'No image URL available. Please ensure the artwork has been generated.',
          duration: 5,
          icon: <WarningOutlined style={{ color: '#ff4d4f' }} />
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
          icon: <WarningOutlined style={{ color: '#faad14' }} />
        });
        setIsGeneratingMockups(false);
        return;
      }
      
      // Validate intelligent mockup requirements
      if (mockupType === 'intelligent' && mockupsSnapshot.size === 1) {
        message.warning('Only one template available. For best results with intelligent mockups, upload templates with clear placement areas (frames, t-shirts, mugs).');
      }

      // Create appropriate job based on type
      if (mockupType === 'intelligent') {
        // Debug logging
        console.log('Creating intelligent mockup job with:', {
          jobId,
          imageUrl,
          prompt,
          templateId: mockupsSnapshot.docs[0]?.id
        });
        
        // Create intelligent mockup job
        const intelligentJobData = {
          status: INTELLIGENT_MOCKUP_STATUS.PENDING,
          artwork_url: imageUrl,  // Backend expects artwork_url, not sourceImageUrl
          mockup_template: mockupsSnapshot.docs[0]?.id || 'default',  // Backend expects mockup_template
          original_job_id: jobId,  // Backend expects original_job_id, not sourceJobId
          sourcePrompt: prompt,
          createdAt: serverTimestamp(),
          processingStartTime: null,
          completionTime: null,
          error: null,
          resultUrl: null,
          detectedRegions: null
        };
        
        const docRef = await addDoc(collection(db, 'intelligent_mockup_jobs'), intelligentJobData);
        message.success({
          content: 'AI-powered mockup generation started! This typically takes 3-7 minutes. Check the Drafts tab for progress.',
          duration: 8,
          icon: <RobotOutlined style={{ color: '#52c41a' }} />
        });
      } else {
        // Create simple mockup job
        const mockupJobData = {
          status: MOCKUP_STATUS.PENDING,
          sourceJobId: jobId,
          sourceImageUrl: imageUrl,
          sourcePrompt: prompt,
          createdAt: serverTimestamp(),
        };

        const docRef = await addDoc(collection(db, 'mockup_jobs'), mockupJobData);
        message.success(`Generating mockups with ${mockupsSnapshot.docs.length} template(s)...`);
      }
      
      // Auto-approve the image when generating mockups
      try {
        const jobRef = doc(db, 'jobs', jobId);
        await updateDoc(jobRef, { status: JOB_STATUS.APPROVED });
      } catch (approveError) {
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
    <>
      <Button
        icon={isGeneratingMockups ? <LoadingOutlined /> : <FileImageOutlined />}
        loading={isGeneratingMockups}
        disabled={disabled || isGeneratingMockups}
        onClick={handleButtonClick}
        size={size}
        type={type}
        style={style}
        block={block}
      >
        {isGeneratingMockups ? 'Generating...' : 'Generate Mockups'}
      </Button>
      
      <Modal
        title="Select Mockup Type"
        open={showTypeSelection}
        onOk={handleGenerateMockups}
        onCancel={() => setShowTypeSelection(false)}
        okText="Generate"
        cancelText="Cancel"
        width={500}
      >
        <Radio.Group 
          value={mockupType} 
          onChange={(e) => setMockupType(e.target.value)}
          style={{ width: '100%' }}
        >
          <Space direction="vertical" style={{ width: '100%' }}>
            <Radio value="simple" style={{ padding: '12px 0' }}>
              <Space align="start">
                <FileImageOutlined style={{ fontSize: 24, color: '#1890ff' }} />
                <div>
                  <div style={{ fontWeight: 500 }}>Simple Mockup</div>
                  <Text type="secondary" style={{ fontSize: 12 }}>
                    Quick overlay of your artwork on templates. Ready in seconds.
                    <br />
                    <Text type="secondary" style={{ fontSize: 11, fontStyle: 'italic' }}>
                      Best for: Simple product mockups, fast results
                    </Text>
                  </Text>
                </div>
              </Space>
            </Radio>
            <Radio value="intelligent" style={{ padding: '12px 0' }}>
              <Space align="start">
                <RobotOutlined style={{ fontSize: 24, color: '#52c41a' }} />
                <div>
                  <div style={{ fontWeight: 500 }}>Intelligent Mockup (AI-Powered)</div>
                  <Text type="secondary" style={{ fontSize: 12 }}>
                    AI detects suitable regions and applies perspective correction for realistic placement.
                    Takes 2-5 minutes.
                    <br />
                    <Text type="secondary" style={{ fontSize: 11, fontStyle: 'italic' }}>
                      Best for: Professional mockups, complex templates, realistic placement
                    </Text>
                  </Text>
                </div>
              </Space>
            </Radio>
          </Space>
        </Radio.Group>
        
        <div style={{ 
          marginTop: 16, 
          padding: 12, 
          background: '#f0f5ff', 
          borderRadius: 6,
          border: '1px solid #d6e4ff'
        }}>
          <Text type="secondary" style={{ fontSize: 12 }}>
            <strong>Tip:</strong> Use Simple for quick results, or Intelligent for professional-quality mockups with automatic placement.
          </Text>
        </div>
      </Modal>
    </>
  );
};

export default MockupButton;