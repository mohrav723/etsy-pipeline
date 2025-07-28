import React, { useState } from 'react';
import { Button, Drawer, Typography, Collapse, Space, Tag } from 'antd';
import { QuestionCircleOutlined, RobotOutlined, ClockCircleOutlined, CheckCircleOutlined } from '@ant-design/icons';

const { Title, Text, Paragraph } = Typography;
const { Panel } = Collapse;

const IntelligentMockupHelp: React.FC = () => {
  const [visible, setVisible] = useState(false);

  return (
    <>
      <Button
        icon={<QuestionCircleOutlined />}
        onClick={() => setVisible(true)}
        type="text"
        size="small"
      >
        Help
      </Button>
      
      <Drawer
        title={
          <Space>
            <RobotOutlined style={{ color: '#1890ff' }} />
            Intelligent Mockups Guide
          </Space>
        }
        placement="right"
        onClose={() => setVisible(false)}
        open={visible}
        width={400}
      >
        <Space direction="vertical" size="large" style={{ width: '100%' }}>
          <div>
            <Title level={5}>What are Intelligent Mockups?</Title>
            <Paragraph>
              Intelligent Mockups use AI to automatically detect the best placement areas in your templates 
              and apply perspective correction to make your artwork look realistic and professional.
            </Paragraph>
          </div>

          <div>
            <Title level={5}>How it Works</Title>
            <Collapse defaultActiveKey={['1']}>
              <Panel header="1. Object Detection" key="1">
                <Text>
                  Our AI analyzes your mockup template to find suitable regions like:
                </Text>
                <ul>
                  <li>Picture frames</li>
                  <li>T-shirt designs</li>
                  <li>Mug surfaces</li>
                  <li>Phone cases</li>
                  <li>Wall spaces</li>
                </ul>
              </Panel>
              <Panel header="2. Perspective Transformation" key="2">
                <Text>
                  Your artwork is automatically warped and adjusted to match the perspective 
                  of the detected region, ensuring it looks natural and realistic.
                </Text>
              </Panel>
              <Panel header="3. Final Composition" key="3">
                <Text>
                  The transformed artwork is seamlessly integrated into the mockup, 
                  with proper shadows and blending for a professional result.
                </Text>
              </Panel>
            </Collapse>
          </div>

          <div>
            <Title level={5}>Processing Time</Title>
            <Space direction="vertical">
              <Text>
                <ClockCircleOutlined /> Typical: 2-3 minutes
              </Text>
              <Text type="secondary">
                Processing time varies based on template complexity and server load. 
                Complex templates may take up to 5 minutes.
              </Text>
            </Space>
          </div>

          <div>
            <Title level={5}>Best Practices</Title>
            <Space direction="vertical" size="small">
              <Text>
                <CheckCircleOutlined style={{ color: '#52c41a' }} /> Use templates with clear placement areas
              </Text>
              <Text>
                <CheckCircleOutlined style={{ color: '#52c41a' }} /> Upload high-quality mockup templates
              </Text>
              <Text>
                <CheckCircleOutlined style={{ color: '#52c41a' }} /> Ensure good contrast between placement area and background
              </Text>
            </Space>
          </div>

          <div>
            <Title level={5}>Troubleshooting</Title>
            <Collapse>
              <Panel header="Detection Failed" key="detection">
                <Paragraph>
                  If AI can't detect suitable regions:
                  <ul>
                    <li>Try a template with clearer objects (frames, shirts, mugs)</li>
                    <li>Avoid overly complex or abstract templates</li>
                    <li>Use the simple mockup option instead</li>
                  </ul>
                </Paragraph>
              </Panel>
              <Panel header="Timeout Errors" key="timeout">
                <Paragraph>
                  If processing takes too long:
                  <ul>
                    <li>Try again during off-peak hours</li>
                    <li>Use a simpler template</li>
                    <li>Ensure your image isn't too large (max 10MB)</li>
                  </ul>
                </Paragraph>
              </Panel>
              <Panel header="Poor Results" key="quality">
                <Paragraph>
                  If the result doesn't look right:
                  <ul>
                    <li>Check if your artwork resolution matches the template</li>
                    <li>Try a different template with better defined areas</li>
                    <li>Ensure your artwork has transparent background if needed</li>
                  </ul>
                </Paragraph>
              </Panel>
            </Collapse>
          </div>

          <div>
            <Title level={5}>When to Use</Title>
            <Space direction="vertical" size="small">
              <div>
                <Tag color="green">Recommended for:</Tag>
                <Text>Professional product mockups, complex templates, realistic placement</Text>
              </div>
              <div>
                <Tag color="orange">Not ideal for:</Tag>
                <Text>Quick previews, simple overlays, or when you need instant results</Text>
              </div>
            </Space>
          </div>
        </Space>
      </Drawer>
    </>
  );
};

export default IntelligentMockupHelp;