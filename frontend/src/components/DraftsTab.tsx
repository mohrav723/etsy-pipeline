import React, { useState, useEffect } from 'react';
import { db } from '../firebase';
import { collection, onSnapshot, query, orderBy, addDoc, updateDoc, doc, serverTimestamp } from 'firebase/firestore';
import { Typography, Empty, Spin, message } from 'antd';
import { RobotOutlined } from '@ant-design/icons';
import { IntelligentMockupJob } from '../types';
import IntelligentMockupCard from './IntelligentMockupCard';
import IntelligentMockupSkeleton from './IntelligentMockupSkeleton';
import IntelligentMockupHelp from './IntelligentMockupHelp';
import { ErrorService } from '../services/errorService';
import './DraftsTab.css';

const { Title } = Typography;

const DraftsTab = () => {
  const [intelligentJobs, setIntelligentJobs] = useState<IntelligentMockupJob[]>([]);
  const [loadingIntelligent, setLoadingIntelligent] = useState(true);

  useEffect(() => {
    // Listen to intelligent mockup jobs
    const intelligentJobsCollection = collection(db, 'intelligent_mockup_jobs');
    const q = query(intelligentJobsCollection, orderBy('createdAt', 'desc'));

    const unsubscribe = onSnapshot(q, (snapshot) => {
      const jobsFromFirestore: IntelligentMockupJob[] = [];
      snapshot.forEach(doc => {
        const data = doc.data();
        jobsFromFirestore.push({ 
          id: doc.id, 
          ...data,
          // Ensure timestamps are properly typed
          createdAt: data.createdAt,
          processingStartTime: data.processingStartTime || null,
          completionTime: data.completionTime || null,
          retriedAt: data.retriedAt || undefined
        } as IntelligentMockupJob);
      });
      setIntelligentJobs(jobsFromFirestore);
      setLoadingIntelligent(false);
    }, (error) => {
      console.error('Error listening to intelligent mockup jobs:', error);
      setLoadingIntelligent(false);
    });

    return () => unsubscribe();
  }, []);

  const styles = {
    container: {
      display: 'flex',
      flexDirection: 'column' as const,
      gap: '1.5rem'
    },
    header: {
      color: '#ffffff',
      fontSize: '1.2rem',
      fontWeight: 'bold',
      marginBottom: '1rem'
    },
    imageContainer: {
      display: 'flex',
      gap: '8px',
      padding: '16px'
    },
    imageWrapper: {
      flex: 1,
      textAlign: 'center' as const
    },
    imageLabel: {
      color: '#99aab5',
      fontSize: '0.8rem',
      marginBottom: '8px',
      fontWeight: 'bold'
    },
    image: {
      width: '100%',
      height: '150px',
      objectFit: 'cover' as const,
      borderRadius: '4px',
      border: '1px solid #40444b'
    },
    cardInfo: {
      padding: '16px',
      borderTop: '1px solid #40444b'
    },
    mockupName: {
      color: '#ffffff',
      fontSize: '1rem',
      fontWeight: 'bold',
      marginBottom: '8px'
    },
    status: {
      fontSize: '0.8rem',
      padding: '4px 8px',
      borderRadius: '4px',
      display: 'inline-block',
      marginBottom: '8px'
    },
    statusProcessing: {
      backgroundColor: '#ffa50020',
      color: '#ffa500',
      border: '1px solid #ffa50040'
    },
    statusCompleted: {
      backgroundColor: '#57f28720',
      color: '#57f287',
      border: '1px solid #57f28740'
    },
    statusFailed: {
      backgroundColor: '#ed424520',
      color: '#ed4245',
      border: '1px solid #ed424540'
    },
    date: {
      color: '#99aab5',
      fontSize: '0.8rem'
    },
    loadingContainer: {
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      height: '200px'
    },
    emptyState: {
      textAlign: 'center' as const,
      padding: '40px',
      color: '#99aab5'
    }
  };


  // Handle retry for intelligent mockups
  const handleRetryIntelligentMockup = async (jobId: string) => {
    try {
      const job = intelligentJobs.find(j => j.id === jobId);
      if (!job) return;

      // Mark old job as retried
      const { id, ...jobData } = job;
      await updateDoc(doc(db, 'intelligent_mockup_jobs', jobId), {
        status: 'retried',
        retriedAt: serverTimestamp()
      });

      // Create new job
      await addDoc(collection(db, 'intelligent_mockup_jobs'), {
        ...jobData,
        status: 'pending',
        createdAt: serverTimestamp(),
        processingStartTime: null,
        completionTime: null,
        error: null,
        resultUrl: null,
        detectedRegions: null
      });

      message.success('Retrying intelligent mockup generation...');
    } catch (error) {
      ErrorService.showError(error, 'Retry intelligent mockup');
    }
  };

  if (loadingIntelligent) {
    return (
      <div style={styles.loadingContainer}>
        <Spin size="large" />
      </div>
    );
  }

  return (
    <div style={styles.container}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Title level={3} style={styles.header}>
          <RobotOutlined style={{ marginRight: '8px' }} />
          AI-Powered Mockups {`(${intelligentJobs.length})`}
        </Title>
        <IntelligentMockupHelp />
      </div>

      {intelligentJobs.length === 0 ? (
        <div style={styles.emptyState}>
          <Empty
            image={Empty.PRESENTED_IMAGE_SIMPLE}
            description={
              <span style={{ color: '#99aab5' }}>
                No AI mockups yet. Generate mockups from the Review tab to see them here.
              </span>
            }
          />
        </div>
      ) : (
        <div className="intelligent-mockup-container">
          {intelligentJobs.map((job) => (
            <div key={job.id} className="intelligent-mockup-wrapper">
              <IntelligentMockupCard 
                job={job} 
                onRetry={handleRetryIntelligentMockup}
              />
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default DraftsTab;