import React, { useEffect, useState } from 'react';
import {
  Card,
  Spin,
  Steps,
  Button,
  Typography,
  Space,
  Image,
  Alert,
  Tag,
  Progress,
  Tooltip,
  List,
} from 'antd';
import {
  RobotOutlined,
  LoadingOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  ReloadOutlined,
  ClockCircleOutlined,
  EyeOutlined,
  DownloadOutlined,
  QuestionCircleOutlined,
  WarningOutlined,
} from '@ant-design/icons';
import DOMPurify from 'dompurify';
import { IntelligentMockupJob } from '../types';
import { INTELLIGENT_MOCKUP_STATUS } from '../constants';
import {
  getIntelligentMockupErrorMessage,
  getErrorSuggestedActions,
  formatProcessingTime,
  getProcessingProgress,
  hasJobTimedOut,
} from '../utils/intelligentMockupHelpers';
import { useSecureDownload } from '../utils/secureDownload';

const { Text, Title } = Typography;

interface IntelligentMockupCardProps {
  job: IntelligentMockupJob;
  onRetry?: (jobId: string) => void;
}

const IntelligentMockupCard: React.FC<IntelligentMockupCardProps> = ({ job, onRetry }) => {
  const [showTimeout, setShowTimeout] = useState(false);
  const [progress, setProgress] = useState(0);
  const { download } = useSecureDownload(['firebasestorage.googleapis.com']);

  // Check for timeout and update progress
  useEffect(() => {
    if (job.status === INTELLIGENT_MOCKUP_STATUS.PROCESSING) {
      const interval = setInterval(() => {
        setProgress(getProcessingProgress(job));
        setShowTimeout(hasJobTimedOut(job));
      }, 1000);

      return () => clearInterval(interval);
    }
  }, [job]);

  // Get current step for progress display
  const _getCurrentStep = (): number => {
    switch (job.status) {
      case INTELLIGENT_MOCKUP_STATUS.PENDING:
        return 0;
      case INTELLIGENT_MOCKUP_STATUS.PROCESSING:
        return 1;
      case INTELLIGENT_MOCKUP_STATUS.COMPLETED:
        return 3;
      case INTELLIGENT_MOCKUP_STATUS.FAILED:
      case INTELLIGENT_MOCKUP_STATUS.RETRIED:
        return job.detectedRegions ? 2 : 1;
      default:
        return 0;
    }
  };

  // Render status-specific content
  const renderContent = () => {
    switch (job.status) {
      case INTELLIGENT_MOCKUP_STATUS.PENDING:
        return (
          <div style={{ textAlign: 'center', padding: '40px 20px' }}>
            <ClockCircleOutlined style={{ fontSize: 48, color: '#8c8c8c', marginBottom: 16 }} />
            <Title level={5} style={{ color: '#8c8c8c', margin: 0 }}>
              Waiting to Start
            </Title>
            <Text type="secondary">Your intelligent mockup will begin processing shortly</Text>
          </div>
        );

      case INTELLIGENT_MOCKUP_STATUS.PROCESSING:
        return (
          <Spin
            indicator={<LoadingOutlined style={{ fontSize: 24 }} spin />}
            tip="AI is analyzing your mockup template..."
          >
            <div style={{ padding: '40px 20px' }}>
              <Steps
                current={1}
                size="small"
                items={[
                  {
                    title: 'Queued',
                    description: 'Ready to process',
                    icon: <CheckCircleOutlined />,
                  },
                  {
                    title: 'Detecting Regions',
                    description: (
                      <Tooltip title="AI analyzes the template to find frames, products, or surfaces where your artwork can be placed">
                        Finding suitable areas
                      </Tooltip>
                    ),
                    icon: <LoadingOutlined spin />,
                  },
                  {
                    title: 'Transforming',
                    description: (
                      <Tooltip title="Your artwork is warped and adjusted to match the perspective and shape of the detected region">
                        Applying perspective
                      </Tooltip>
                    ),
                  },
                  {
                    title: 'Composing',
                    description: (
                      <Tooltip title="The transformed artwork is seamlessly integrated into the mockup template">
                        Creating final image
                      </Tooltip>
                    ),
                  },
                ]}
              />
              <div style={{ marginTop: 24 }}>
                <Progress
                  percent={progress}
                  status={showTimeout ? 'exception' : 'active'}
                  strokeColor={showTimeout ? '#ff4d4f' : '#1890ff'}
                />
                <div style={{ textAlign: 'center', marginTop: 8 }}>
                  <Text type="secondary">
                    Processing time: {formatProcessingTime(job.processingStartTime)}
                  </Text>
                </div>
                {showTimeout && (
                  <Alert
                    type="warning"
                    message="Taking longer than expected"
                    description="This process usually takes 2-5 minutes. If it takes much longer, you may want to retry."
                    showIcon
                    icon={<WarningOutlined />}
                    style={{ marginTop: 16 }}
                    action={
                      onRetry && (
                        <Button size="small" onClick={() => onRetry(job.id)}>
                          Cancel & Retry
                        </Button>
                      )
                    }
                  />
                )}
              </div>
            </div>
          </Spin>
        );

      case INTELLIGENT_MOCKUP_STATUS.COMPLETED: {
        const hasMultipleResults = job.mockup_results && job.mockup_results.length > 0;
        const hasSingleResult = job.result_url && !hasMultipleResults;

        return (
          <div>
            {hasMultipleResults ? (
              <>
                <Space
                  direction="vertical"
                  size="small"
                  style={{ width: '100%', marginBottom: 16 }}
                >
                  <Text type="secondary">
                    Completed in{' '}
                    {formatProcessingTime(
                      job.processingStartTime || job.processing_started_at,
                      job.completionTime || job.processing_completed_at
                    )}
                  </Text>
                  <Text>
                    Generated {job.total_mockups_generated || job.mockup_results.length} intelligent
                    mockups
                    {job.detected_regions_total &&
                      ` across ${job.detected_regions_total} detected regions`}
                  </Text>
                </Space>

                <div
                  style={{
                    display: 'grid',
                    gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))',
                    gap: 12,
                    marginBottom: 16,
                  }}
                >
                  {job.mockup_results.map((result, index) => (
                    <div
                      key={index}
                      style={{
                        border: '1px solid #f0f0f0',
                        borderRadius: 8,
                        overflow: 'hidden',
                        background: '#fafafa',
                      }}
                    >
                      <Image
                        src={result.url}
                        alt={`${result.template_name} mockup`}
                        style={{ width: '100%', height: 200, objectFit: 'cover' }}
                        placeholder={
                          <div
                            style={{
                              background: '#f0f0f0',
                              height: 200,
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'center',
                            }}
                          >
                            <Spin size="small" />
                          </div>
                        }
                      />
                      <div style={{ padding: 8 }}>
                        <Text strong style={{ fontSize: 12 }}>
                          {result.template_name}
                        </Text>
                        <br />
                        <Text type="secondary" style={{ fontSize: 11 }}>
                          {result.detected_regions} regions • {result.selected_region}
                        </Text>
                        <div style={{ marginTop: 8 }}>
                          <Button
                            size="small"
                            icon={<DownloadOutlined />}
                            onClick={async () => {
                              try {
                                await download(
                                  result.url,
                                  `intelligent-mockup-${job.id}-${result.template_name}.png`
                                );
                              } catch (error) {
                                console.error('Download failed:', error);
                              }
                            }}
                            block
                          >
                            Download
                          </Button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </>
            ) : hasSingleResult ? (
              <>
                <div style={{ marginBottom: 16, position: 'relative' }}>
                  <Image
                    src={job.result_url}
                    alt="Intelligent mockup result"
                    style={{ width: '100%', borderRadius: 8 }}
                    placeholder={
                      <div
                        style={{
                          background: '#f0f0f0',
                          height: 200,
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                        }}
                      >
                        <Spin />
                      </div>
                    }
                  />
                  {job.detected_regions && job.detected_regions > 0 && (
                    <div style={{ position: 'absolute', top: 8, right: 8 }}>
                      <Tag color="success" icon={<RobotOutlined />}>
                        {job.detected_regions} region{job.detected_regions > 1 ? 's' : ''} detected
                      </Tag>
                    </div>
                  )}
                </div>
                <Space direction="vertical" size="small" style={{ width: '100%' }}>
                  <Text type="secondary">
                    Completed in{' '}
                    {formatProcessingTime(
                      job.processingStartTime || job.processing_started_at,
                      job.completionTime || job.processing_completed_at
                    )}
                  </Text>
                  {job.selected_region && (
                    <div>
                      <Text type="secondary">Selected region: </Text>
                      <Tag style={{ marginRight: 4 }}>{job.selected_region}</Tag>
                    </div>
                  )}
                  <Space>
                    <Button
                      icon={<EyeOutlined />}
                      onClick={() => window.open(job.result_url!, '_blank')}
                    >
                      View Full Size
                    </Button>
                    <Button
                      type="primary"
                      icon={<DownloadOutlined />}
                      onClick={async () => {
                        try {
                          await download(job.result_url!, `intelligent-mockup-${job.id}.png`);
                        } catch (error) {
                          console.error('Download failed:', error);
                        }
                      }}
                    >
                      Download
                    </Button>
                  </Space>
                </Space>
              </>
            ) : (
              <Alert
                type="warning"
                message="Result Not Found"
                description="The mockup was completed but the result image is not available."
              />
            )}
          </div>
        );
      }

      case INTELLIGENT_MOCKUP_STATUS.FAILED:
      case INTELLIGENT_MOCKUP_STATUS.RETRIED: {
        const suggestions = getErrorSuggestedActions(job.error);
        return (
          <div>
            <Alert
              type="error"
              message="Generation Failed"
              description={
                <Space direction="vertical" size="small" style={{ width: '100%' }}>
                  <Text>{getIntelligentMockupErrorMessage(job.error)}</Text>
                  {suggestions.length > 0 && (
                    <>
                      <Text strong>Suggestions:</Text>
                      <List
                        size="small"
                        dataSource={suggestions}
                        renderItem={(item) => (
                          <List.Item style={{ padding: '4px 0', border: 'none' }}>
                            <Text style={{ fontSize: 12 }}>• {item}</Text>
                          </List.Item>
                        )}
                      />
                    </>
                  )}
                </Space>
              }
              showIcon
              icon={<CloseCircleOutlined />}
              style={{ marginBottom: 16 }}
              action={
                job.status === INTELLIGENT_MOCKUP_STATUS.FAILED &&
                onRetry && (
                  <Space>
                    <Button
                      size="small"
                      danger
                      icon={<ReloadOutlined />}
                      onClick={() => onRetry(job.id)}
                    >
                      Retry
                    </Button>
                    <Tooltip title="Try using simple mockups for faster results">
                      <Button size="small" icon={<QuestionCircleOutlined />}>
                        Help
                      </Button>
                    </Tooltip>
                  </Space>
                )
              }
            />
            {job.error?.details && (
              <details style={{ marginTop: 8 }}>
                <summary style={{ cursor: 'pointer', color: '#8c8c8c' }}>Technical details</summary>
                <pre
                  style={{
                    fontSize: 12,
                    background: '#f5f5f5',
                    padding: 8,
                    borderRadius: 4,
                    overflow: 'auto',
                    marginTop: 8,
                  }}
                  dangerouslySetInnerHTML={{
                    __html: DOMPurify.sanitize(JSON.stringify(job.error.details, null, 2)),
                  }}
                />
              </details>
            )}
            {job.status === INTELLIGENT_MOCKUP_STATUS.RETRIED && job.retriedAt && (
              <Text type="secondary" style={{ display: 'block', marginTop: 8 }}>
                Retried {job.retriedAt.toDate().toLocaleTimeString()}
              </Text>
            )}
          </div>
        );
      }

      default:
        return null;
    }
  };

  // Get status color
  const getStatusColor = (): string => {
    switch (job.status) {
      case INTELLIGENT_MOCKUP_STATUS.PENDING:
        return '#d9d9d9';
      case INTELLIGENT_MOCKUP_STATUS.PROCESSING:
        return '#1890ff';
      case INTELLIGENT_MOCKUP_STATUS.COMPLETED:
        return '#52c41a';
      case INTELLIGENT_MOCKUP_STATUS.FAILED:
        return '#ff4d4f';
      case INTELLIGENT_MOCKUP_STATUS.RETRIED:
        return '#faad14';
      default:
        return '#d9d9d9';
    }
  };

  // Get status icon
  const getStatusIcon = () => {
    switch (job.status) {
      case INTELLIGENT_MOCKUP_STATUS.PENDING:
        return <ClockCircleOutlined />;
      case INTELLIGENT_MOCKUP_STATUS.PROCESSING:
        return <LoadingOutlined spin />;
      case INTELLIGENT_MOCKUP_STATUS.COMPLETED:
        return <CheckCircleOutlined />;
      case INTELLIGENT_MOCKUP_STATUS.FAILED:
      case INTELLIGENT_MOCKUP_STATUS.RETRIED:
        return <CloseCircleOutlined />;
      default:
        return <RobotOutlined />;
    }
  };

  return (
    <Card
      title={
        <Space>
          <RobotOutlined style={{ color: '#1890ff' }} />
          <span>Intelligent Mockup</span>
          <Tag color={getStatusColor()} icon={getStatusIcon()}>
            {job.status.charAt(0).toUpperCase() + job.status.slice(1)}
          </Tag>
        </Space>
      }
      extra={
        <Tooltip title={job.sourcePrompt}>
          <Text
            type="secondary"
            style={{
              maxWidth: 200,
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              whiteSpace: 'nowrap',
              display: 'inline-block',
            }}
          >
            {job.sourcePrompt}
          </Text>
        </Tooltip>
      }
      style={{ marginBottom: 16 }}
    >
      {renderContent()}

      <div
        style={{
          marginTop: 16,
          paddingTop: 16,
          borderTop: '1px solid #f0f0f0',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}
      >
        <Text type="secondary" style={{ fontSize: 12 }}>
          Created {job.createdAt ? job.createdAt.toDate().toLocaleString() : 'Just now'}
        </Text>
        {job.templateUsed && (
          <Text type="secondary" style={{ fontSize: 12 }}>
            Template: {job.templateUsed}
          </Text>
        )}
      </div>
    </Card>
  );
};

export default IntelligentMockupCard;
