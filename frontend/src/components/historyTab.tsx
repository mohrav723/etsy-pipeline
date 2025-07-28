import React, { useState, useEffect } from 'react';
import { Typography, Card, Modal, Row, Col, Divider, Space, Pagination, Spin } from 'antd';
import { db } from '../firebase';
import { collection, getDocs, query, where, orderBy, limit, startAfter, DocumentSnapshot, Timestamp } from 'firebase/firestore';
import { Job } from '../types';
import MockupButton from './MockupButton';

const { Title, Text } = Typography;

type HistoryTabProps = {};

interface GroupedJobs {
  [date: string]: Job[];
}

const HistoryTab = ({}: HistoryTabProps) => {
  const [historyJobs, setHistoryJobs] = useState<Job[]>([]);
  const [selectedJob, setSelectedJob] = useState<Job | null>(null);
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const [loading, setLoading] = useState(false);
  const [totalJobs, setTotalJobs] = useState(0);
  const [lastVisible, setLastVisible] = useState<DocumentSnapshot | null>(null);
  const [pageSnapshots, setPageSnapshots] = useState<{ [key: number]: DocumentSnapshot | null }>({});
  
  const JOBS_PER_PAGE = 20;

  // Fetch total count for pagination
  const fetchTotalCount = async () => {
    try {
      const jobsCollection = collection(db, 'jobs');
      const countQuery = query(
        jobsCollection,
        where('status', 'in', ['approved', 'pending_review'])
      );
      const snapshot = await getDocs(countQuery);
      let count = 0;
      snapshot.forEach(doc => {
        const data = doc.data();
        if (data.generatedImageUrl) {
          count++;
        }
      });
      setTotalJobs(count);
    } catch (error) {
      // Error fetching total count
    }
  };

  // Fetch jobs for a specific page
  const fetchJobsForPage = async (page: number) => {
    setLoading(true);
    try {
      const jobsCollection = collection(db, 'jobs');
      let q = query(
        jobsCollection,
        where('status', 'in', ['approved', 'pending_review']),
        orderBy('createdAt', 'desc'),
        limit(JOBS_PER_PAGE)
      );

      // If not the first page, start after the last document of the previous page
      if (page > 1 && pageSnapshots[page - 1]) {
        q = query(
          jobsCollection,
          where('status', 'in', ['approved', 'pending_review']),
          orderBy('createdAt', 'desc'),
          startAfter(pageSnapshots[page - 1]),
          limit(JOBS_PER_PAGE)
        );
      }

      const snapshot = await getDocs(q);
      const jobsFromFirestore: Job[] = [];
      let lastDoc: DocumentSnapshot | null = null;
      
      snapshot.forEach(doc => {
        const data = doc.data();
        if (data.generatedImageUrl) {
          jobsFromFirestore.push({ id: doc.id, ...data } as Job);
          lastDoc = doc;
        }
      });
      
      setHistoryJobs(jobsFromFirestore);
      setLastVisible(lastDoc);
      
      // Store the last document for this page to enable navigation
      if (lastDoc) {
        setPageSnapshots(prev => ({ ...prev, [page]: lastDoc }));
      }
      
    } catch (error) {
      // Error fetching jobs
    } finally {
      setLoading(false);
    }
  };

  // Load initial data
  useEffect(() => {
    fetchTotalCount();
    fetchJobsForPage(1);
  }, []);

  // Handle page change
  const handlePageChange = (page: number) => {
    setCurrentPage(page);
    fetchJobsForPage(page);
  };

  // Helper function to format date from Firebase timestamp
  const formatDate = (timestamp: Timestamp | Date | null): string => {
    if (!timestamp) return 'Unknown Date';
    
    let date: Date;
    if (timestamp.toDate) {
      // Firebase Timestamp
      date = timestamp.toDate();
    } else if (timestamp.seconds) {
      // Firebase Timestamp object
      date = new Date(timestamp.seconds * 1000);
    } else {
      // Regular Date or timestamp
      date = new Date(timestamp);
    }

    const today = new Date();
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);

    const jobDate = new Date(date.getFullYear(), date.getMonth(), date.getDate());
    const todayDate = new Date(today.getFullYear(), today.getMonth(), today.getDate());
    const yesterdayDate = new Date(yesterday.getFullYear(), yesterday.getMonth(), yesterday.getDate());

    if (jobDate.getTime() === todayDate.getTime()) {
      return 'Today';
    } else if (jobDate.getTime() === yesterdayDate.getTime()) {
      return 'Yesterday';
    } else {
      return date.toLocaleDateString('en-US', { 
        weekday: 'long', 
        year: 'numeric', 
        month: 'long', 
        day: 'numeric' 
      });
    }
  };

  // Group jobs by date
  const groupJobsByDate = (jobs: Job[]): GroupedJobs => {
    return jobs.reduce((groups: GroupedJobs, job) => {
      const dateKey = formatDate(job.createdAt);
      if (!groups[dateKey]) {
        groups[dateKey] = [];
      }
      groups[dateKey].push(job);
      return groups;
    }, {});
  };

  const handleImageClick = (job: Job) => {
    setSelectedJob(job);
    setIsModalVisible(true);
  };

  const closeModal = () => {
    setSelectedJob(null);
    setIsModalVisible(false);
  };

  const groupedJobs = groupJobsByDate(historyJobs);

  return (
    <>
      {totalJobs > JOBS_PER_PAGE && (
        <div style={{ textAlign: 'center', marginBottom: '24px', paddingTop: '8px' }}>
          <Pagination
            current={currentPage}
            total={totalJobs}
            pageSize={JOBS_PER_PAGE}
            onChange={handlePageChange}
            showSizeChanger={false}
            showQuickJumper
            showTotal={(total, range) => `${range[0]}-${range[1]} of ${total} images`}
            style={{
              '& .ant-pagination-item': {
                backgroundColor: '#23272a',
                borderColor: '#40444b'
              },
              '& .ant-pagination-item a': {
                color: '#b9bbbe'
              },
              '& .ant-pagination-item-active': {
                backgroundColor: '#5865f2',
                borderColor: '#5865f2'
              },
              '& .ant-pagination-item-active a': {
                color: '#ffffff'
              }
            } as React.CSSProperties}
          />
        </div>
      )}
      
      <Spin spinning={loading}>
        <div style={{ padding: '8px 0', minHeight: '400px' }}>
        {Object.keys(groupedJobs).length === 0 ? (
          <Card style={{ textAlign: 'center', padding: '40px' }}>
            <Text type="secondary">No images in history yet. Generate some art to see them here!</Text>
          </Card>
        ) : (
          Object.entries(groupedJobs).map(([date, jobs]) => (
            <div key={date} style={{ marginBottom: '32px' }}>
              <Title level={4} style={{ color: '#ffffff', marginBottom: '16px' }}>
                {date}
              </Title>
              <Row gutter={[16, 16]}>
                {jobs.map(job => (
                  <Col key={job.id} xs={12} sm={8} md={6} lg={4}>
                    <Card
                      hoverable
                      cover={
                        <div style={{ height: '200px', overflow: 'hidden' }}>
                          <img
                            src={job.generatedImageUrl}
                            alt="Generated art"
                            style={{
                              width: '100%',
                              height: '100%',
                              objectFit: 'cover',
                              transition: 'transform 0.3s ease'
                            }}
                            onMouseEnter={(e) => {
                              e.currentTarget.style.transform = 'scale(1.05)';
                            }}
                            onMouseLeave={(e) => {
                              e.currentTarget.style.transform = 'scale(1)';
                            }}
                          />
                        </div>
                      }
                      onClick={() => handleImageClick(job)}
                      style={{ 
                        height: 'fit-content',
                        backgroundColor: '#23272a',
                        border: '1px solid #40444b'
                      }}
                      styles={{
                        body: { padding: '12px' }
                      }}
                    >
                      <Card.Meta
                        description={
                          <Text 
                            style={{ 
                              color: '#b9bbbe', 
                              fontSize: '12px',
                              display: 'block',
                              overflow: 'hidden',
                              textOverflow: 'ellipsis',
                              whiteSpace: 'nowrap'
                            }}
                          >
                            "{job.prompt}"
                          </Text>
                        }
                      />
                    </Card>
                  </Col>
                ))}
              </Row>
              {Object.entries(groupedJobs).indexOf([date, jobs]) < Object.entries(groupedJobs).length - 1 && (
                <Divider style={{ borderColor: '#40444b', margin: '24px 0' }} />
              )}
            </div>
          ))
        )}
        </div>
      </Spin>

      <Modal
        title={null}
        open={isModalVisible}
        onCancel={closeModal}
        footer={null}
        width={800}
        centered
        styles={{
          content: {
            backgroundColor: '#23272a',
            border: '1px solid #40444b'
          }
        }}
      >
        {selectedJob && (
          <div>
            <div style={{ textAlign: 'center', marginBottom: '20px' }}>
              <img
                src={selectedJob.generatedImageUrl}
                alt="Generated art"
                style={{
                  maxWidth: '100%',
                  height: 'auto',
                  borderRadius: '8px',
                  maxHeight: '500px'
                }}
              />
            </div>
            
            <div style={{ marginBottom: '16px' }}>
              <Text strong style={{ color: '#ffffff', fontSize: '16px' }}>
                "{selectedJob.prompt}"
              </Text>
            </div>
            
            <Space direction="vertical" size="small" style={{ width: '100%' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <Text style={{ color: '#99aab5' }}>Aspect Ratio:</Text>
                <Text style={{ color: '#ffffff' }}>{selectedJob.aspectRatio}</Text>
              </div>
              
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <Text style={{ color: '#99aab5' }}>Steps:</Text>
                <Text style={{ color: '#ffffff' }}>{selectedJob.steps}</Text>
              </div>
              
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <Text style={{ color: '#99aab5' }}>Guidance:</Text>
                <Text style={{ color: '#ffffff' }}>{selectedJob.guidance}</Text>
              </div>
              
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <Text style={{ color: '#99aab5' }}>Safety Tolerance:</Text>
                <Text style={{ color: '#ffffff' }}>{selectedJob.safetyTolerance}</Text>
              </div>
              
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <Text style={{ color: '#99aab5' }}>Seed:</Text>
                <Text style={{ color: '#ffffff' }}>{selectedJob.seed}</Text>
              </div>
              
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <Text style={{ color: '#99aab5' }}>Prompt Upsampling:</Text>
                <Text style={{ color: '#ffffff' }}>{selectedJob.promptUpsampling ? 'Yes' : 'No'}</Text>
              </div>
              
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <Text style={{ color: '#99aab5' }}>Created:</Text>
                <Text style={{ color: '#ffffff' }}>{formatDate(selectedJob.createdAt)}</Text>
              </div>
            </Space>
            
            <div style={{ marginTop: '24px', textAlign: 'center' }}>
              <MockupButton
                jobId={selectedJob.id}
                imageUrl={selectedJob.generatedImageUrl}
                prompt={selectedJob.prompt}
                size="large"
                block={true}
              />
            </div>
          </div>
        )}
      </Modal>
    </>
  );
};

export default HistoryTab;