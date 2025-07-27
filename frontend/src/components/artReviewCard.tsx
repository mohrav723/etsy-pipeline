import React, { useState } from 'react';
import { db } from '../firebase';
import { doc, updateDoc, deleteDoc, collection, addDoc, serverTimestamp } from 'firebase/firestore';

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
  originalJobId?: string; // Optional reference to the job this was regenerated from
};

type ArtReviewCardProps = {
  job: Job;
};

const ArtReviewCard = ({ job }: ArtReviewCardProps) => {
  const [isRegenerating, setIsRegenerating] = useState(false);
  const [isApproving, setIsApproving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showParameterEditor, setShowParameterEditor] = useState(false);
  
  // Editable parameters with current job values as defaults
  const [editableParams, setEditableParams] = useState({
    prompt: job.prompt,
    aspectRatio: job.aspectRatio,
    steps: job.steps,
    guidance: job.guidance,
    safetyTolerance: job.safetyTolerance,
    seed: job.seed,
    promptUpsampling: job.promptUpsampling
  });

  const handleRegenerate = async () => {
    setError(null);
    setIsRegenerating(true);
    
    console.log(`Creating new generation from job ${job.id} with parameters:`, editableParams);

    try {
      // Create a new job entry instead of updating the existing one
      // This preserves the current generation in history
      const newJobData = {
        status: 'pending_art_generation',
        prompt: editableParams.prompt,
        aspectRatio: editableParams.aspectRatio,
        steps: editableParams.steps,
        guidance: editableParams.guidance,
        safetyTolerance: editableParams.safetyTolerance,
        seed: editableParams.seed,
        promptUpsampling: editableParams.promptUpsampling,
        createdAt: serverTimestamp(),
        // Preserve any other fields that might be useful
        originalJobId: job.id, // Reference to the job this was regenerated from
      };
      
      const docRef = await addDoc(collection(db, 'jobs'), newJobData);
      console.log(`New regeneration job created with ID: ${docRef.id}`);
      
      setShowParameterEditor(false);
      // Note: Don't alert here as the current card will remain in review, 
      // and the new generation will appear separately when completed
    } catch (error: any) {
      console.error("Error creating regeneration job:", error);
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
    },
    parameterEditor: {
      backgroundColor: '#2f3136',
      border: '1px solid #40444b',
      borderRadius: '8px',
      padding: '1rem',
      margin: '1rem 0',
      display: 'flex',
      flexDirection: 'column',
      gap: '0.75rem'
    },
    parameterRow: {
      display: 'flex',
      flexDirection: 'column',
      gap: '0.25rem'
    },
    parameterLabel: {
      color: '#b9bbbe',
      fontSize: '0.75rem',
      fontWeight: 'bold'
    },
    parameterInput: {
      backgroundColor: '#40444b',
      border: '1px solid #72767d',
      borderRadius: '4px',
      padding: '8px',
      color: '#dcddde',
      fontSize: '0.8rem'
    },
    parameterTextarea: {
      backgroundColor: '#40444b',
      border: '1px solid #72767d',
      borderRadius: '4px',
      padding: '8px',
      color: '#dcddde',
      fontSize: '0.8rem',
      minHeight: '60px',
      resize: 'vertical' as const
    },
    parameterSelect: {
      backgroundColor: '#40444b',
      border: '1px solid #72767d',
      borderRadius: '4px',
      padding: '8px',
      color: '#dcddde',
      fontSize: '0.8rem'
    },
    parameterCheckbox: {
      marginRight: '8px'
    },
    toggleButton: {
      backgroundColor: '#4f545c',
      color: '#dcddde',
      border: '1px solid #72767d',
      borderRadius: '4px',
      padding: '6px 12px',
      fontSize: '0.75rem',
      cursor: 'pointer',
      alignSelf: 'flex-start'
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
      </div>

      <button 
        onClick={() => setShowParameterEditor(!showParameterEditor)}
        style={styles.toggleButton}
      >
        {showParameterEditor ? '▲ Hide Parameters' : '▼ Edit Parameters'}
      </button>

      {showParameterEditor && (
        <div style={styles.parameterEditor}>
          <div style={styles.parameterRow}>
            <label style={styles.parameterLabel}>Prompt</label>
            <textarea
              style={styles.parameterTextarea}
              value={editableParams.prompt}
              onChange={(e) => setEditableParams({...editableParams, prompt: e.target.value})}
            />
          </div>

          <div style={styles.parameterRow}>
            <label style={styles.parameterLabel}>Aspect Ratio</label>
            <select
              style={styles.parameterSelect}
              value={editableParams.aspectRatio}
              onChange={(e) => setEditableParams({...editableParams, aspectRatio: e.target.value})}
            >
              <option value="16:9">16:9 (Landscape)</option>
              <option value="1:1">1:1 (Square)</option>
              <option value="9:16">9:16 (Portrait)</option>
            </select>
          </div>

          <div style={styles.parameterRow}>
            <label style={styles.parameterLabel}>Steps ({editableParams.steps})</label>
            <input
              type="range"
              min="1"
              max="50"
              style={styles.parameterInput}
              value={editableParams.steps}
              onChange={(e) => setEditableParams({...editableParams, steps: parseInt(e.target.value)})}
            />
          </div>

          <div style={styles.parameterRow}>
            <label style={styles.parameterLabel}>Guidance ({editableParams.guidance})</label>
            <input
              type="range"
              min="1"
              max="5"
              step="0.1"
              style={styles.parameterInput}
              value={editableParams.guidance}
              onChange={(e) => setEditableParams({...editableParams, guidance: parseFloat(e.target.value)})}
            />
          </div>

          <div style={styles.parameterRow}>
            <label style={styles.parameterLabel}>Safety Tolerance ({editableParams.safetyTolerance})</label>
            <input
              type="range"
              min="1"
              max="6"
              style={styles.parameterInput}
              value={editableParams.safetyTolerance}
              onChange={(e) => setEditableParams({...editableParams, safetyTolerance: parseInt(e.target.value)})}
            />
          </div>

          <div style={styles.parameterRow}>
            <label style={styles.parameterLabel}>Seed</label>
            <input
              type="number"
              style={styles.parameterInput}
              value={editableParams.seed}
              onChange={(e) => setEditableParams({...editableParams, seed: parseInt(e.target.value) || 0})}
            />
          </div>

          <div style={styles.parameterRow}>
            <label style={styles.parameterLabel}>
              <input
                type="checkbox"
                style={styles.parameterCheckbox}
                checked={editableParams.promptUpsampling}
                onChange={(e) => setEditableParams({...editableParams, promptUpsampling: e.target.checked})}
              />
              Prompt Upsampling
            </label>
          </div>
        </div>
      )}

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
          {isRegenerating ? '🔄 Regenerating...' : '🔄 Regenerate with Current Parameters'}
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