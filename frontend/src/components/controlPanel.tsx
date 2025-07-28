import { useState } from 'react';
import { useGeneration } from '../context/GenerationContext';
import { 
  Card, 
  Form, 
  Input, 
  Select, 
  Slider, 
  InputNumber, 
  Checkbox, 
  Button, 
  Typography, 
  message,
  Space,
  Divider
} from 'antd';
import { ThunderboltOutlined, LoadingOutlined } from '@ant-design/icons';
import { db } from '../firebase';
import { collection, addDoc, serverTimestamp } from 'firebase/firestore';
import JobStatus from './JobStatus';
import { GenerationFormValues } from '../types';
import { ErrorService } from '../services/errorService';

const { Title, Text } = Typography;
const { TextArea } = Input;

const ControlPanel = () => {
  const [form] = Form.useForm();
  const [isLoading, setIsLoading] = useState(false);
  const { setIsGenerating } = useGeneration();

  const handleGenerateClick = async (values: GenerationFormValues & { aspectRatio?: string; safetyTolerance?: number; promptUpsampling?: boolean }) => {
    setIsLoading(true);
    setIsGenerating(true);
    
    try {
      const docRef = await addDoc(collection(db, "jobs"), {
        status: 'pending_art_generation',
        prompt: values.prompt.trim(),
        createdAt: serverTimestamp(),
        aspectRatio: values.aspectRatio,
        steps: values.steps,
        guidance: values.guidance,
        safetyTolerance: values.safetyTolerance,
        seed: values.seed === -1 ? Math.floor(Math.random() * 1000000) : values.seed,
        promptUpsampling: values.promptUpsampling || false,
      });
      
      message.success(`Art generation job submitted! ID: ${docRef.id.slice(0, 8)}...`);
      form.resetFields(['prompt']);
      
      // Keep showing loading state until image is generated
      // The loading state will be cleared when a new job appears in pending_review
      
    } catch (e) {
      ErrorService.showError(e, 'Job submission');
      setIsGenerating(false);
    } finally {
      setIsLoading(false);
    }
  };

  const handleFormFinish = (values: GenerationFormValues & { aspectRatio?: string; safetyTolerance?: number; promptUpsampling?: boolean }) => {
    handleGenerateClick(values);
  };

  const handleFormFinishFailed = () => {
    message.error('Please fill in all required fields correctly.');
  };

  return (
    <Card
      title={
        <Space direction="vertical" size={4} style={{ width: '100%' }}>
          <Title level={3} style={{ margin: 0, color: '#ffffff', fontSize: '18px' }}>
            Generator Controls
          </Title>
        </Space>
      }
      style={{ height: 'fit-content' }}
      styles={{ body: { padding: '16px' } }}
    >
      <style>
        {`
          .compact-form .ant-form-item {
            margin-bottom: 8px !important;
          }
          .compact-form .ant-form-item:last-child {
            margin-bottom: 0 !important;
          }
        `}
      </style>
      <Form
        form={form}
        layout="vertical"
        onFinish={handleFormFinish}
        onFinishFailed={handleFormFinishFailed}
        size="small"
        className="compact-form"
        initialValues={{
          aspectRatio: '16:9',
          steps: 28,
          guidance: 3,
          safetyTolerance: 2,
          seed: 42,
          promptUpsampling: false,
        }}
      >
        <Form.Item
          label="Prompt"
          name="prompt"
                    rules={[
            { required: true, message: 'Please enter a prompt' },
            { min: 3, message: 'Prompt must be at least 3 characters long' }
          ]}
        >
          <TextArea
            rows={2}
            placeholder="Describe the image you want to generate..."
            style={{ resize: 'vertical' }}
          />
        </Form.Item>

        <Form.Item label="Aspect Ratio" name="aspectRatio" style={{ marginBottom: '8px' }}>
          <Select>
            <Select.Option value="16:9">16:9 (Landscape)</Select.Option>
            <Select.Option value="1:1">1:1 (Square)</Select.Option>
            <Select.Option value="9:16">9:16 (Portrait)</Select.Option>
          </Select>
        </Form.Item>

        <Form.Item label="Steps" name="steps" style={{ marginBottom: '8px' }}>
          <Space direction="vertical" size={4} style={{ width: '100%' }}>
            <Text type="secondary" style={{ fontSize: '11px' }}>
              More steps = better quality, but slower generation
            </Text>
            <Slider
              min={1}
              max={50}
              tooltip={{ formatter: (value) => `${value} steps` }}
            />
          </Space>
        </Form.Item>

        <Form.Item label="Guidance" name="guidance" style={{ marginBottom: '8px' }}>
          <Space direction="vertical" size={4} style={{ width: '100%' }}>
            <Text type="secondary" style={{ fontSize: '11px' }}>
              High guidance scales improve prompt adherence at the cost of reduced realism
            </Text>
            <Slider
              min={1.5}
              max={5}
              step={0.1}
              tooltip={{ formatter: (value) => `${value}` }}
            />
          </Space>
        </Form.Item>

        <Form.Item label="Safety Tolerance" name="safetyTolerance" style={{ marginBottom: '8px' }}>
          <Slider
            min={0}
            max={6}
            step={1}
            tooltip={{ formatter: (value) => `Level ${value}` }}
          />
        </Form.Item>

        <Form.Item label="Seed" name="seed" style={{ marginBottom: '8px' }}>
          <Space direction="vertical" size={4} style={{ width: '100%' }}>
            <Text type="secondary" style={{ fontSize: '11px' }}>
              Use -1 for random, or specific number for reproducible results
            </Text>
            <InputNumber
              style={{ width: '100%' }}
              placeholder="Enter seed or -1 for random"
            />
          </Space>
        </Form.Item>

        <Form.Item name="promptUpsampling" valuePropName="checked" style={{ marginBottom: '8px' }}>
          <Checkbox>Prompt Upsampling</Checkbox>
        </Form.Item>

        <Form.Item style={{ marginBottom: 0, marginTop: '8px' }}>
          <Button
            type="primary"
            htmlType="submit"
            loading={isLoading}
            icon={isLoading ? <LoadingOutlined /> : <ThunderboltOutlined />}
            size="middle"
            block
          >
            {isLoading ? 'Submitting...' : 'Generate Art'}
          </Button>
        </Form.Item>
      </Form>

      <Divider style={{ margin: '12px 0 8px 0' }} />
      
      <JobStatus />
    </Card>
  );
};

export default ControlPanel;