import React, { useState, useEffect } from 'react';
import { db } from '../firebase';
import { collection, onSnapshot, query, orderBy, limit, Timestamp } from 'firebase/firestore';
import { JobStatus as JobStatusType } from '../types';

type JobStatusProps = {
  className?: string;
};

type JobUpdate = {
  id: string;
  status: JobStatusType;
  prompt: string;
  createdAt: Timestamp;
};

const JobStatus = ({ className }: JobStatusProps) => {
  const [recentJobs, setRecentJobs] = useState<JobUpdate[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const jobsCollection = collection(db, 'jobs');
    const q = query(
      jobsCollection,
      orderBy('createdAt', 'desc'),
      limit(3)
    );

    const unsubscribe = onSnapshot(q, (snapshot) => {
      const jobs: JobUpdate[] = [];
      snapshot.forEach(doc => {
        const data = doc.data();
        jobs.push({
          id: doc.id,
          status: data.status,
          prompt: data.prompt?.substring(0, 30) + (data.prompt?.length > 30 ? '...' : ''),
          createdAt: data.createdAt
        });
      });
      setRecentJobs(jobs);
      setIsLoading(false);
    });

    return () => unsubscribe();
  }, []);

  const getStatusColor = (status: JobStatusType) => {
    switch (status) {
      case 'pending_art_generation': return '#ffa500';
      case 'processing': return '#5865f2';
      case 'pending_review': return '#57f287';
      case 'approved': return '#00ff00';
      case 'failed': return '#ed4245';
      default: return '#99aab5';
    }
  };

  const getStatusEmoji = (status: JobStatusType) => {
    switch (status) {
      case 'pending_art_generation': return '⏳';
      case 'processing': return '🔄';
      case 'pending_review': return '👀';
      case 'approved': return '✅';
      case 'failed': return '❌';
      default: return '📝';
    }
  };

  const formatStatus = (status: JobStatusType) => {
    return status.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
  };

  const styles = {
    container: {
      backgroundColor: '#23272a',
      border: '1px solid #40444b',
      borderRadius: '8px',
      padding: '1rem',
      marginTop: '1rem',
    },
    title: {
      color: '#ffffff',
      margin: '0 0 0.75rem 0',
      fontSize: '0.9rem',
      fontWeight: 'bold',
    },
    jobItem: {
      display: 'flex',
      alignItems: 'center',
      padding: '0.5rem 0',
      borderBottom: '1px solid #40444b',
      fontSize: '0.8rem',
    },
    jobItemLast: {
      borderBottom: 'none',
    },
    statusBadge: {
      display: 'inline-flex',
      alignItems: 'center',
      gap: '4px',
      fontSize: '0.7rem',
      padding: '2px 6px',
      borderRadius: '4px',
      fontWeight: 'bold',
      marginRight: '8px',
      minWidth: '80px',
      justifyContent: 'center',
    },
    prompt: {
      color: '#99aab5',
      flex: 1,
      fontSize: '0.75rem',
    },
    loading: {
      color: '#99aab5',
      textAlign: 'center' as const,
      padding: '1rem 0',
      fontSize: '0.8rem',
    },
    empty: {
      color: '#99aab5',
      textAlign: 'center' as const,
      padding: '0.5rem 0',
      fontSize: '0.8rem',
    }
  };

  return (
    <div style={styles.container} className={className}>
      <h4 style={styles.title}>📊 Recent Jobs</h4>
      
      {isLoading ? (
        <div style={styles.loading}>Loading...</div>
      ) : recentJobs.length === 0 ? (
        <div style={styles.empty}>No jobs yet</div>
      ) : (
        recentJobs.map((job, index) => (
          <div 
            key={job.id} 
            style={{
              ...styles.jobItem,
              ...(index === recentJobs.length - 1 ? styles.jobItemLast : {})
            }}
          >
            <div 
              style={{
                ...styles.statusBadge,
                backgroundColor: `${getStatusColor(job.status)}20`,
                color: getStatusColor(job.status),
                border: `1px solid ${getStatusColor(job.status)}40`,
              }}
            >
              {getStatusEmoji(job.status)} {formatStatus(job.status)}
            </div>
            <div style={styles.prompt}>
              {job.prompt}
            </div>
          </div>
        ))
      )}
    </div>
  );
};

export default JobStatus;