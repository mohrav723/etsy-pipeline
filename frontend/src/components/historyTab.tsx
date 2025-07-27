import React, { useState, useEffect } from 'react';
import { db } from '../firebase';
import { collection, onSnapshot, query, where, orderBy } from 'firebase/firestore';
import { Job } from './artReviewCard';

type HistoryTabProps = {};

const HistoryTab = ({}: HistoryTabProps) => {
  const [historyJobs, setHistoryJobs] = useState<Job[]>([]);
  const [selectedJob, setSelectedJob] = useState<Job | null>(null);

  useEffect(() => {
    const jobsCollection = collection(db, 'jobs');
    const q = query(
      jobsCollection,
      where('status', 'in', ['approved', 'pending_review']),
      orderBy('createdAt', 'desc')
    );

    const unsubscribe = onSnapshot(q, (snapshot) => {
      const jobsFromFirestore: Job[] = [];
      snapshot.forEach(doc => {
        const data = doc.data();
        if (data.generatedImageUrl) {
          jobsFromFirestore.push({ id: doc.id, ...data } as Job);
        }
      });
      setHistoryJobs(jobsFromFirestore);
    });

    return () => unsubscribe();
  }, []);

  const styles = {
    historyGrid: {
      display: 'grid',
      gridTemplateColumns: 'repeat(auto-fill, minmax(250px, 1fr))',
      gap: '1rem',
      padding: '1rem 0'
    },
    imageCard: {
      backgroundColor: '#23272a',
      border: '1px solid #40444b',
      borderRadius: '8px',
      overflow: 'hidden',
      cursor: 'pointer',
      transition: 'transform 0.2s ease, border-color 0.2s ease'
    },
    imageCardHover: {
      transform: 'scale(1.02)',
      borderColor: '#5865f2'
    },
    image: {
      width: '100%',
      height: '200px',
      objectFit: 'cover' as const
    },
    imageInfo: {
      padding: '0.75rem',
      color: '#99aab5',
      fontSize: '0.8rem'
    },
    prompt: {
      color: '#ffffff',
      fontSize: '0.9rem',
      marginBottom: '0.5rem',
      overflow: 'hidden',
      textOverflow: 'ellipsis',
      whiteSpace: 'nowrap' as const
    },
    modal: {
      position: 'fixed' as const,
      top: 0,
      left: 0,
      width: '100%',
      height: '100%',
      backgroundColor: 'rgba(0, 0, 0, 0.8)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 1000
    },
    modalContent: {
      backgroundColor: '#23272a',
      border: '1px solid #40444b',
      borderRadius: '8px',
      padding: '2rem',
      maxWidth: '800px',
      maxHeight: '90vh',
      overflow: 'auto',
      position: 'relative' as const
    },
    modalImage: {
      maxWidth: '100%',
      height: 'auto',
      borderRadius: '8px',
      marginBottom: '1rem'
    },
    closeButton: {
      position: 'absolute' as const,
      top: '1rem',
      right: '1rem',
      background: 'none',
      border: 'none',
      color: '#99aab5',
      fontSize: '1.5rem',
      cursor: 'pointer'
    },
    detailRow: {
      display: 'flex',
      justifyContent: 'space-between',
      marginBottom: '0.5rem',
      color: '#e0e0e0'
    },
    detailLabel: {
      color: '#99aab5',
      fontWeight: 'bold'
    },
    promptDetail: {
      color: '#ffffff',
      fontSize: '1.1rem',
      marginBottom: '1rem',
      lineHeight: '1.4'
    }
  } as const;

  const handleImageClick = (job: Job) => {
    setSelectedJob(job);
  };

  const closeModal = () => {
    setSelectedJob(null);
  };

  return (
    <>
      <div style={styles.historyGrid}>
        {historyJobs.map(job => (
          <div
            key={job.id}
            style={styles.imageCard}
            onClick={() => handleImageClick(job)}
            onMouseEnter={(e) => {
              Object.assign(e.currentTarget.style, styles.imageCardHover);
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.transform = 'scale(1)';
              e.currentTarget.style.borderColor = '#40444b';
            }}
          >
            <img
              src={job.generatedImageUrl}
              alt="Generated art"
              style={styles.image}
            />
            <div style={styles.imageInfo}>
              <div style={styles.prompt}>"{job.prompt}"</div>
            </div>
          </div>
        ))}
      </div>

      {selectedJob && (
        <div style={styles.modal} onClick={closeModal}>
          <div style={styles.modalContent} onClick={(e) => e.stopPropagation()}>
            <button style={styles.closeButton} onClick={closeModal}>×</button>
            
            <img
              src={selectedJob.generatedImageUrl}
              alt="Generated art"
              style={styles.modalImage}
            />
            
            <div style={styles.promptDetail}>"{selectedJob.prompt}"</div>
            
            <div style={styles.detailRow}>
              <span style={styles.detailLabel}>Aspect Ratio:</span>
              <span>{selectedJob.aspectRatio}</span>
            </div>
            
            <div style={styles.detailRow}>
              <span style={styles.detailLabel}>Steps:</span>
              <span>{selectedJob.steps}</span>
            </div>
            
            <div style={styles.detailRow}>
              <span style={styles.detailLabel}>Guidance:</span>
              <span>{selectedJob.guidance}</span>
            </div>
            
            <div style={styles.detailRow}>
              <span style={styles.detailLabel}>Safety Tolerance:</span>
              <span>{selectedJob.safetyTolerance}</span>
            </div>
            
            <div style={styles.detailRow}>
              <span style={styles.detailLabel}>Seed:</span>
              <span>{selectedJob.seed}</span>
            </div>
            
            <div style={styles.detailRow}>
              <span style={styles.detailLabel}>Prompt Upsampling:</span>
              <span>{selectedJob.promptUpsampling ? 'Yes' : 'No'}</span>
            </div>
            
          </div>
        </div>
      )}
    </>
  );
};

export default HistoryTab;