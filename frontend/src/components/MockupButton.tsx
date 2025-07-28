import React, { useState } from 'react';
import { Button, message } from 'antd';
import { FileImageOutlined, LoadingOutlined } from '@ant-design/icons';
import { db } from '../firebase';
import { collection, addDoc, serverTimestamp, query, getDocs, doc, updateDoc } from 'firebase/firestore';

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

  const handleGenerateMockups = async () => {
    setIsGeneratingMockups(true);
    
    try {
      // First, check if there are available mockup templates
      const mockupsQuery = query(collection(db, 'mockups'));
      const mockupsSnapshot = await getDocs(mockupsQuery);
      
      if (mockupsSnapshot.empty) {
        message.warning('No mockup templates available. Please upload mockups first.');
        setIsGeneratingMockups(false);
        return;
      }

      // Create a mockup generation job that will trigger the Temporal workflow
      const mockupJobData = {
        status: 'pending_mockup_generation',
        sourceJobId: jobId,
        sourceImageUrl: imageUrl,
        sourcePrompt: prompt,
        createdAt: serverTimestamp(),
      };

      const docRef = await addDoc(collection(db, 'mockup_jobs'), mockupJobData);
      
      // Auto-approve the image when generating mockups
      try {
        const jobRef = doc(db, 'jobs', jobId);
        await updateDoc(jobRef, { status: 'approved' });
      } catch (approveError) {
        // Don't fail the whole operation if approval fails
      }
      
      message.success(`Generating mockups with ${mockupsSnapshot.docs.length} template(s)...`);
      
      // Show progress message
      setTimeout(() => {
        message.info('Check the Drafts tab to see your mockup progress!');
      }, 2000);
      
    } catch (error) {
      message.error(`Failed to generate mockups: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setIsGeneratingMockups(false);
    }
  };

  return (
    <Button
      icon={isGeneratingMockups ? <LoadingOutlined /> : <FileImageOutlined />}
      loading={isGeneratingMockups}
      disabled={disabled || isGeneratingMockups}
      onClick={handleGenerateMockups}
      size={size}
      type={type}
      style={style}
      block={block}
    >
      {isGeneratingMockups ? 'Generating...' : 'Generate Mockups'}
    </Button>
  );
};

export default MockupButton;