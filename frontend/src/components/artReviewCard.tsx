import React, { useState } from 'react';
import { 
  Card, 
  Button, 
  Typography, 
  Space, 
  Image, 
  Collapse, 
  Form, 
  Input, 
  Select, 
  Slider, 
  InputNumber, 
  Checkbox,
  message,
  Spin
} from 'antd';
import { 
  CheckOutlined, 
  ReloadOutlined, 
  SettingOutlined,
  LoadingOutlined
} from '@ant-design/icons';
import { db } from '../firebase';
import { doc, updateDoc, deleteDoc, collection, addDoc, serverTimestamp } from 'firebase/firestore';
import MockupButton from './MockupButton';

const { Text } = Typography;
const { TextArea } = Input;

// Export the Job type so other components can use it
export type Job = {
  id: string;
  generatedImageUrl: string;
  prompt: string;
  model: string;
  aspectRatio: string;
  steps: number;
  guidance: number;
  safetyTolerance: number;
  seed: number;
  promptUpsampling: boolean;
  originalJobId?: string; // Optional reference to the job this was regenerated from
};

type ArtReviewCardProps = {
  job: Job;
};

const ArtReviewCard = ({ job }: ArtReviewCardProps) => {
  const [isRegenerating, setIsRegenerating] = useState(false);
  const [isApproving, setIsApproving] = useState(false);
  const [form] = Form.useForm();
  
  // Initialize form with current job values
  React.useEffect(() => {
    form.setFieldsValue({
      prompt: job.prompt,
      aspectRatio: job.aspectRatio,
      steps: job.steps,
      guidance: job.guidance,
      safetyTolerance: job.safetyTolerance,
      seed: job.seed,
      promptUpsampling: job.promptUpsampling
    });
  }, [job, form]);
  
  // Clear regenerating state when the job changes (new image loaded)
  React.useEffect(() => {
    if (isRegenerating) {
      setIsRegenerating(false);
    }
  }, [job.generatedImageUrl]);

  const handleRegenerate = async () => {
    try {
      const values = await form.validateFields();
      setIsRegenerating(true);
      
      console.log(`Creating new generation from job ${job.id} with parameters:`, values);

      // Create a new job entry instead of updating the existing one
      const newJobData = {
        status: 'pending_art_generation',
        prompt: values.prompt,
        aspectRatio: values.aspectRatio,
        steps: values.steps,
        guidance: values.guidance,
        safetyTolerance: values.safetyTolerance,
        seed: values.seed,
        promptUpsampling: values.promptUpsampling,
        createdAt: serverTimestamp(),
        originalJobId: job.id, // Reference to the job this was regenerated from
      };
      
      const docRef = await addDoc(collection(db, 'jobs'), newJobData);
      console.log(`New regeneration job created with ID: ${docRef.id}`);
      
      message.success('Regeneration job submitted successfully!');
      
      // Set a timeout to clear loading state if no new image appears
      setTimeout(() => {
        setIsRegenerating(false);
      }, 30000); // 30 second timeout
      
    } catch (error: any) {
      console.error("Error creating regeneration job:", error);
      message.error(`Failed to regenerate: ${error.message || 'Unknown error'}`);
      setIsRegenerating(false);
    }
  };
  
  const handleApprove = async () => {
    setIsApproving(true);
    
    console.log(`Approving job ${job.id}...`);
    const jobRef = doc(db, 'jobs', job.id);
    
    try {
      await updateDoc(jobRef, { status: 'approved' });
      message.success('Image approved successfully!');
    } catch (error: any) {
      console.error("Error approving job:", error);
      message.error(`Failed to approve: ${error.message || 'Unknown error'}`);
    } finally {
      setIsApproving(false);
    }
  };


  const parameterEditorItems = [
    {
      key: 'parameters',
      label: (
        <Space>
          <SettingOutlined />
          Edit Parameters
        </Space>
      ),
      children: (
        <Form
          form={form}
          layout="vertical"
          size="small"
        >
          <Form.Item
            label="Prompt"
            name="prompt"
            rules={[{ required: true, message: 'Prompt is required' }]}
          >
            <TextArea rows={3} />
          </Form.Item>

          <Form.Item label="Aspect Ratio" name="aspectRatio">
            <Select>
              <Select.Option value="16:9">16:9 (Landscape)</Select.Option>
              <Select.Option value="1:1">1:1 (Square)</Select.Option>
              <Select.Option value="9:16">9:16 (Portrait)</Select.Option>
            </Select>
          </Form.Item>

          <Form.Item label="Steps" name="steps">
            <Slider
              min={1}
              max={50}
              tooltip={{ formatter: (value) => `${value} steps` }}
            />
          </Form.Item>

          <Form.Item label="Guidance" name="guidance">
            <Slider
              min={1.5}
              max={5}
              step={0.1}
              tooltip={{ formatter: (value) => `${value}` }}
            />
          </Form.Item>

          <Form.Item label="Safety Tolerance" name="safetyTolerance">
            <Slider
              min={1}
              max={6}
              step={1}
              tooltip={{ formatter: (value) => `Level ${value}` }}
            />
          </Form.Item>

          <Form.Item label="Seed" name="seed">
            <InputNumber style={{ width: '100%' }} />
          </Form.Item>

          <Form.Item name="promptUpsampling" valuePropName="checked">
            <Checkbox>Prompt Upsampling</Checkbox>
          </Form.Item>
        </Form>
      ),
    },
  ];

  return (
    <Card
      style={{ width: '100%' }}
      styles={{ body: { padding: '20px' } }}
      cover={
        <div style={{ 
          display: 'flex', 
          justifyContent: 'center', 
          alignItems: 'center',
          padding: '20px', 
          backgroundColor: '#2f3136',
          minHeight: '300px'
        }}>
          {isRegenerating ? (
            <div style={{ 
              display: 'flex', 
              flexDirection: 'column', 
              alignItems: 'center', 
              gap: '16px',
              color: '#ffffff'
            }}>
              <Spin size="large" />
              <Typography.Text style={{ color: '#b9bbbe', fontSize: '16px' }}>
                Generating new image...
              </Typography.Text>
            </div>
          ) : (
            <Image
              src={job.generatedImageUrl}
              alt="AI generated art"
              style={{ 
                maxWidth: '100%', 
                maxHeight: '500px',
                borderRadius: '8px',
                objectFit: 'contain'
              }}
              onError={() => {
                console.error('Failed to load image:', job.generatedImageUrl);
                message.error('Failed to load image');
              }}
            />
          )}
        </div>
      }
      actions={[
        <Button
          key="regenerate"
          type="default"
          icon={isRegenerating ? <LoadingOutlined /> : <ReloadOutlined />}
          loading={isRegenerating}
          disabled={isApproving}
          onClick={handleRegenerate}
          size="large"
        >
          {isRegenerating ? 'Regenerating...' : 'Regenerate'}
        </Button>,
        <Button
          key="approve"
          type="primary"
          icon={isApproving ? <LoadingOutlined /> : <CheckOutlined />}
          loading={isApproving}
          disabled={isRegenerating}
          onClick={handleApprove}
          size="large"
        >
          {isApproving ? 'Approving...' : 'Approve'}
        </Button>,
        <MockupButton
          key="mockups"
          jobId={job.id}
          imageUrl={job.generatedImageUrl}
          prompt={job.prompt}
          disabled={isRegenerating || isApproving}
        />,
      ]}
    >
      <Card.Meta
        description={
          <Space direction="vertical" size={16} style={{ width: '100%' }}>
            <div style={{ padding: '8px 0', textAlign: 'center' }}>
              <Text style={{ fontSize: '15px', fontStyle: 'italic', color: '#b9bbbe' }}>
                "{job.prompt}"
              </Text>
            </div>
            
            <Collapse 
              items={parameterEditorItems}
              size="small"
              ghost
              style={{ marginTop: '8px' }}
            />
          </Space>
        }
      />
    </Card>
  );
};

export default ArtReviewCard;