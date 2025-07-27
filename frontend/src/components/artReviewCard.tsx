import React, { useState } from 'react';
import { db } from '../firebase';
import { doc, updateDoc, deleteDoc } from 'firebase/firestore';

// Export the Job type so other components can use it
export type Job = {
  id: string;
  generatedImageUrl: string;
  prompt: string;
  model: string;
  aspectRatio: string;
  steps: number;
  guidance: number;
  safetyTolerance: number;
  seed: number;
  promptUpsampling: boolean;
  generationCount: number;
};

type ArtReviewCardProps = {
  job: Job;
};

const ArtReviewCard = ({ job }: ArtReviewCardProps) => {
  const [isRegenerating, setIsRegenerating] = useState(false);
  const [isApproving, setIsApproving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleRegenerate = async () => {
    setError(null);
    setIsRegenerating(true);
    
    console.log(`Regenerating job ${job.id}...`);
    const jobRef = doc(db, 'jobs', job.id);

    try {
      await updateDoc(jobRef, {
        status: 'pending_art_generation',
      });
      // Note: Don't alert here as the card will disappear from review
    } catch (error: any) {
      console.error("Error regenerating job:", error);
      setError(`Failed to regenerate: ${error.message || 'Unknown error'}`);
    } finally {
      setIsRegenerating(false);
    }
  };
  
  const handleApprove = async () => {
    setError(null);
    setIsApproving(true);
    
    console.log(`Approving job ${job.id}...`);
    const jobRef = doc(db, 'jobs', job.id);
    
    try {
      await updateDoc(jobRef, { status: 'approved' });
      // Note: Don't alert here as the card will disappear from review
    } catch (error: any) {
      console.error("Error approving job:", error);
      setError(`Failed to approve: ${error.message || 'Unknown error'}`);
    } finally {
      setIsApproving(false);
    }
  };

  const styles = {
    card: { 
      border: '1px solid #40444b', 
      padding: '1.5rem', 
      borderRadius: '8px', 
      background: '#23272a',
      display: 'flex',
      flexDirection: 'column',
      gap: '1rem',
      alignItems: 'center'
    },
    image: { 
      maxWidth: '100%', 
      height: 'auto',
      borderRadius: '8px', 
      objectFit: 'contain' 
    },
    info: {
      color: '#99aab5',
      fontSize: '0.9rem',
      textAlign: 'center' as const
    },
    buttonContainer: { 
      display: 'flex', 
      gap: '1rem',
      justifyContent: 'center'
    },
    button: {
      padding: '10px 20px',
      borderRadius: '6px',
      border: 'none',
      cursor: 'pointer',
      fontWeight: 'bold',
      fontSize: '0.9rem'
    },
    approveButton: {
      backgroundColor: '#57f287',
      color: '#000'
    },
    regenerateButton: {
      backgroundColor: '#5865f2',
      color: '#fff'
    },
    buttonDisabled: {
      opacity: 0.6,
      cursor: 'not-allowed'
    },
    errorMessage: {
      backgroundColor: '#ed424520',
      color: '#ed4245',
      border: '1px solid #ed424540',
      padding: '8px',
      borderRadius: '4px',
      fontSize: '0.8rem',
      textAlign: 'center' as const,
      margin: '8px 0'
    }
  } as const;

  return (
    <div style={styles.card}>
      <img 
        src={job.generatedImageUrl} 
        alt="AI generated art" 
        style={styles.image}
        onError={() => {
          console.error('Failed to load image:', job.generatedImageUrl);
          setError('Failed to load image');
        }}
      />
      
      <div style={styles.info}>
        <p>"{job.prompt}"</p>
        <p>Generation #{job.generationCount}</p>
      </div>

      {error && (
        <div style={styles.errorMessage}>
          ❌ {error}
        </div>
      )}
      
      <div style={styles.buttonContainer}>
        <button 
          onClick={handleRegenerate}
          disabled={isRegenerating || isApproving}
          style={{
            ...styles.button, 
            ...styles.regenerateButton,
            ...(isRegenerating || isApproving ? styles.buttonDisabled : {})
          }}
        >
          {isRegenerating ? '🔄 Regenerating...' : '🔄 Regenerate'}
        </button>
        <button 
          onClick={handleApprove}
          disabled={isRegenerating || isApproving}
          style={{
            ...styles.button, 
            ...styles.approveButton,
            ...(isRegenerating || isApproving ? styles.buttonDisabled : {})
          }}
        >
          {isApproving ? '⏳ Approving...' : '✅ Approve'}
        </button>
      </div>
    </div>
  );
};

export default ArtReviewCard;