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
  Spin,
} from 'antd';
import { ReloadOutlined, SettingOutlined, LoadingOutlined } from '@ant-design/icons';
import { db } from '../firebase';
import { collection, addDoc, serverTimestamp } from 'firebase/firestore';
import MockupButton from './MockupButton';
import { REGENERATION_TIMEOUT_MS, SLIDER_RANGES, ASPECT_RATIOS, JOB_STATUS } from '../constants';
import { ErrorService } from '../services/errorService';
import { Job } from '../types';

const { Text } = Typography;
const { TextArea } = Input;

type ArtReviewCardProps = {
  job: Job;
};

const ArtReviewCard = ({ job }: ArtReviewCardProps) => {
  const [isRegenerating, setIsRegenerating] = useState(false);
  const [form] = Form.useForm();
  const timeoutRef = React.useRef<NodeJS.Timeout | null>(null);

  // Initialize form with current job values
  React.useEffect(() => {
    form.setFieldsValue({
      prompt: job.prompt,
      aspectRatio: job.aspectRatio,
      steps: job.steps,
      guidance: job.guidance,
      safetyTolerance: job.safetyTolerance,
      seed: job.seed,
      promptUpsampling: job.promptUpsampling,
    });
  }, [job, form]);

  // Clear regenerating state when the job changes (new image loaded)
  React.useEffect(() => {
    if (isRegenerating) {
      setIsRegenerating(false);
    }
  }, [job.generatedImageUrl, isRegenerating]);

  // Cleanup timeout on unmount
  React.useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, []);

  const handleRegenerate = async () => {
    try {
      const values = await form.validateFields();
      setIsRegenerating(true);

      // Creating new generation from job

      // Create a new job entry instead of updating the existing one
      const newJobData = {
        status: JOB_STATUS.PENDING_ART,
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

      await addDoc(collection(db, 'jobs'), newJobData);

      message.success('Regeneration job submitted successfully!');

      // Set a timeout to clear loading state if no new image appears
      timeoutRef.current = setTimeout(() => {
        setIsRegenerating(false);
        timeoutRef.current = null;
      }, REGENERATION_TIMEOUT_MS);
    } catch (error) {
      ErrorService.showError(error, 'Art regeneration');
      setIsRegenerating(false);
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
        <Form form={form} layout="vertical" size="small">
          <Form.Item
            label="Prompt"
            name="prompt"
            rules={[{ required: true, message: 'Prompt is required' }]}
          >
            <TextArea rows={3} />
          </Form.Item>

          <Form.Item label="Aspect Ratio" name="aspectRatio">
            <Select>
              {ASPECT_RATIOS.map((ratio) => (
                <Select.Option key={ratio.value} value={ratio.value}>
                  {ratio.label}
                </Select.Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item label="Steps" name="steps">
            <Slider
              min={SLIDER_RANGES.steps.min}
              max={SLIDER_RANGES.steps.max}
              tooltip={{ formatter: (value) => `${value} steps` }}
            />
          </Form.Item>

          <Form.Item label="Guidance" name="guidance">
            <Slider
              min={SLIDER_RANGES.guidance.min}
              max={SLIDER_RANGES.guidance.max}
              step={SLIDER_RANGES.guidance.step}
              tooltip={{ formatter: (value) => `${value}` }}
            />
          </Form.Item>

          <Form.Item label="Safety Tolerance" name="safetyTolerance">
            <Slider
              min={SLIDER_RANGES.safetyTolerance.min}
              max={SLIDER_RANGES.safetyTolerance.max}
              step={SLIDER_RANGES.safetyTolerance.step}
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
        <div
          style={{
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            padding: '20px',
            backgroundColor: '#2f3136',
            minHeight: '300px',
          }}
        >
          {isRegenerating ? (
            <div
              style={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                gap: '16px',
                color: '#ffffff',
              }}
            >
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
                objectFit: 'contain',
              }}
              onError={() => {
                ErrorService.showError(new Error('Failed to load image'), 'Image loading');
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
          onClick={handleRegenerate}
          size="large"
        >
          {isRegenerating ? 'Regenerating...' : 'Regenerate'}
        </Button>,
        <MockupButton
          key="mockups"
          jobId={job.id}
          imageUrl={job.generatedImageUrl || ''}
          prompt={job.prompt}
          disabled={isRegenerating || !job.generatedImageUrl}
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
