import React, { useState, useEffect, lazy, Suspense, useMemo } from 'react';
import { ConfigProvider, Layout, Typography, Tabs, Empty, Card, Spin } from 'antd';
import { GenerationProvider, useGeneration } from './context/GenerationContext';
import {
  PictureOutlined,
  HistoryOutlined,
  MobileOutlined,
  DollarCircleOutlined,
  FileImageOutlined,
} from '@ant-design/icons';
import ArtReviewCard from './components/artReviewCard';
import ControlPanel from './components/controlPanel';
import ErrorBoundary from './components/ErrorBoundary';
import { Job } from './types';
import { db } from './firebase';
import { collection, onSnapshot, query, where, orderBy, limit } from 'firebase/firestore';
import { antdDarkTheme } from './theme/antdTheme';
import 'antd/dist/reset.css';

// Lazy load tabs for better performance
const HistoryTab = lazy(() => import('./components/historyTab'));
const MockupTab = lazy(() => import('./components/MockupTab'));
const DraftsTab = lazy(() => import('./components/DraftsTab'));
const CostMonitoring = lazy(() => import('./components/CostMonitoring'));

const { Header, Content, Sider } = Layout;
const { Title, Text } = Typography;

// Loading component for lazy loaded tabs
const TabLoading = () => (
  <div
    style={{
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      height: '400px',
    }}
  >
    <Spin size="large" tip="Loading..." />
  </div>
);

function AppContent() {
  const { isGenerating, setIsGenerating } = useGeneration();
  const [reviewJobs, setReviewJobs] = useState<Job[]>([]);
  const [activeTab, setActiveTab] = useState<'review' | 'history' | 'mockups' | 'drafts' | 'costs'>(
    'review'
  );

  // Listen for only the most recent pending_review job
  useEffect(() => {
    const jobsCollection = collection(db, 'jobs');
    const q = query(
      jobsCollection,
      where('status', '==', 'pending_review'),
      orderBy('createdAt', 'desc'),
      limit(1)
    );

    const unsubscribe = onSnapshot(q, (snapshot) => {
      const jobsFromFirestore: Job[] = [];
      snapshot.forEach((doc) => {
        const data = doc.data();
        jobsFromFirestore.push({ id: doc.id, ...data } as Job);
      });

      setReviewJobs(jobsFromFirestore);

      // Clear loading state when a new job appears for review
      if (jobsFromFirestore.length > 0) {
        setIsGenerating(false);
      }
    });

    return () => unsubscribe();
  }, [setIsGenerating]);

  // Apply the dark theme to the page
  useEffect(() => {
    document.body.style.backgroundColor = '#1a1a1a';
    document.body.style.color = '#e0e0e0';
  }, []);

  const tabItems = useMemo(
    () => [
      {
        key: 'review',
        label: (
          <span style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <PictureOutlined />
            Review ({reviewJobs.length})
          </span>
        ),
        children: (
          <>
            {isGenerating && (
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'center',
                  alignItems: 'center',
                  height: '400px',
                  marginBottom: '16px',
                }}
              >
                <Card style={{ width: '100%', textAlign: 'center' }}>
                  <div
                    style={{
                      display: 'flex',
                      flexDirection: 'column',
                      alignItems: 'center',
                      gap: '16px',
                      padding: '40px',
                    }}
                  >
                    <Spin size="large" />
                    <Text style={{ color: '#b9bbbe', fontSize: '16px' }}>
                      Generating your image...
                    </Text>
                    <Text type="secondary" style={{ fontSize: '14px' }}>
                      This may take a few moments
                    </Text>
                  </div>
                </Card>
              </div>
            )}

            {reviewJobs.length > 0 ? (
              <div
                style={{ display: 'flex', flexDirection: 'column', gap: '16px', padding: '4px 0' }}
              >
                {reviewJobs.map((job) => (
                  <ErrorBoundary key={job.id}>
                    <ArtReviewCard job={job} />
                  </ErrorBoundary>
                ))}
              </div>
            ) : !isGenerating ? (
              <Empty
                image={Empty.PRESENTED_IMAGE_SIMPLE}
                description="No images are currently waiting for review. Use the form on the left to generate new art."
                style={{ color: '#99aab5' }}
              />
            ) : null}
          </>
        ),
      },
      {
        key: 'history',
        label: (
          <span style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <HistoryOutlined />
            History
          </span>
        ),
        children: (
          <Suspense fallback={<TabLoading />}>
            <HistoryTab />
          </Suspense>
        ),
      },
      {
        key: 'mockups',
        label: (
          <span style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <MobileOutlined />
            Mockups
          </span>
        ),
        children: (
          <Suspense fallback={<TabLoading />}>
            <MockupTab />
          </Suspense>
        ),
      },
      {
        key: 'drafts',
        label: (
          <span style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <FileImageOutlined />
            Drafts
          </span>
        ),
        children: (
          <Suspense fallback={<TabLoading />}>
            <DraftsTab />
          </Suspense>
        ),
      },
      {
        key: 'costs',
        label: (
          <span style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <DollarCircleOutlined />
            Costs
          </span>
        ),
        children: (
          <Suspense fallback={<TabLoading />}>
            <CostMonitoring />
          </Suspense>
        ),
      },
    ],
    [reviewJobs, isGenerating]
  );

  return (
    <ConfigProvider theme={antdDarkTheme}>
      <ErrorBoundary>
        <Layout style={{ height: '100vh', overflow: 'hidden' }}>
          <Header
            style={{
              padding: '0 32px',
              borderBottom: '1px solid #40444b',
              height: '60px',
              lineHeight: 'normal',
              display: 'flex',
              alignItems: 'center',
              flexShrink: 0,
            }}
          >
            <Title
              level={1}
              style={{
                color: '#ffffff',
                margin: 0,
                lineHeight: '1.2',
                fontSize: '24px',
              }}
            >
              Etsy Pipeline Dashboard
            </Title>
          </Header>

          <Layout>
            <Sider
              width={360}
              style={{
                background: '#23272a',
                padding: '16px',
                borderRight: '1px solid #40444b',
                overflow: 'auto',
                height: 'calc(100vh - 60px)',
                flexShrink: 0,
              }}
            >
              <ErrorBoundary>
                <ControlPanel />
              </ErrorBoundary>
            </Sider>

            <Content
              style={{
                padding: '20px',
                background: '#1a1a1a',
                overflow: 'auto',
                height: 'calc(100vh - 60px)',
                display: 'flex',
                flexDirection: 'column',
              }}
            >
              <ErrorBoundary>
                <Tabs
                  activeKey={activeTab}
                  onChange={(key) =>
                    setActiveTab(key as 'review' | 'history' | 'mockups' | 'drafts' | 'costs')
                  }
                  items={tabItems}
                  size="large"
                  style={{ height: '100%', display: 'flex', flexDirection: 'column' }}
                  tabBarStyle={{ flexShrink: 0, marginBottom: '16px' }}
                />
              </ErrorBoundary>
            </Content>
          </Layout>
        </Layout>
      </ErrorBoundary>
    </ConfigProvider>
  );
}

function App() {
  return (
    <GenerationProvider>
      <AppContent />
    </GenerationProvider>
  );
}

export default App;
