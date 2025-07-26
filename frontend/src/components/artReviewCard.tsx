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
  const handleRegenerate = async () => {
    console.log(`Regenerating job ${job.id}...`);
    const jobRef = doc(db, 'jobs', job.id);

    try {
      await updateDoc(jobRef, {
        status: 'pending_art_generation',
      });
      alert("Job has been submitted for regeneration!");
    } catch (error) {
      console.error("Error regenerating job:", error);
      alert("Failed to submit for regeneration.");
    }
  };
  
  const handleApprove = async () => {
    console.log(`Approving job ${job.id}...`);
    const jobRef = doc(db, 'jobs', job.id);
    try {
        await updateDoc(jobRef, { status: 'approved' });
        alert("Job approved! The final pipeline will now run.");
    } catch (error) {
        console.error("Error approving job:", error);
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
    }
  } as const;

  return (
    <div style={styles.card}>
      <img 
        src={job.generatedImageUrl} 
        alt="AI generated art" 
        style={styles.image}
      />
      
      <div style={styles.info}>
        <p>"{job.prompt}"</p>
        <p>Generation #{job.generationCount}</p>
      </div>
      
      <div style={styles.buttonContainer}>
        <button 
          onClick={handleRegenerate} 
          style={{...styles.button, ...styles.regenerateButton}}
        >
          🔄 Regenerate
        </button>
        <button 
          onClick={handleApprove} 
          style={{...styles.button, ...styles.approveButton}}
        >
          ✅ Approve
        </button>
      </div>
    </div>
  );
};

export default ArtReviewCard;