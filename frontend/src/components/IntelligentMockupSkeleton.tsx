import React from 'react';
import { Card, Skeleton, Space } from 'antd';
import { RobotOutlined } from '@ant-design/icons';

const IntelligentMockupSkeleton: React.FC = () => {
  return (
    <Card
      title={
        <Space>
          <RobotOutlined style={{ color: '#1890ff' }} />
          <span>Intelligent Mockup</span>
          <Skeleton.Button active size="small" style={{ width: 80 }} />
        </Space>
      }
      extra={<Skeleton.Input active size="small" style={{ width: 150 }} />}
      style={{ marginBottom: 16 }}
    >
      <Skeleton active paragraph={{ rows: 4 }} />
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
        <Skeleton.Input active size="small" style={{ width: 120 }} />
        <Skeleton.Input active size="small" style={{ width: 100 }} />
      </div>
    </Card>
  );
};

export default IntelligentMockupSkeleton;
