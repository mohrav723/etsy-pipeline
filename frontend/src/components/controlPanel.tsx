import React, { useState } from 'react';
import { db } from '../firebase';
import { collection, addDoc, serverTimestamp } from 'firebase/firestore';
import JobStatus from './JobStatus';

const ControlPanel = () => {
  const [prompt, setPrompt] = useState('');
  const [aspectRatio, setAspectRatio] = useState('16:9');
  const [steps, setSteps] = useState(28);
  const [guidance, setGuidance] = useState(3);
  const [safetyTolerance, setSafetyTolerance] = useState(2);
  const [seed, setSeed] = useState(42);
  const [promptUpsampling, setPromptUpsampling] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const handleGenerateClick = async () => {
    // Clear previous messages
    setError(null);
    setSuccessMessage(null);

    // Validation
    if (!prompt.trim()) {
      setError("Please enter a prompt before generating.");
      return;
    }

    if (prompt.trim().length < 3) {
      setError("Prompt must be at least 3 characters long.");
      return;
    }

    setIsLoading(true);
    
    console.log("Submitting new job to Firestore...");
    try {
      const docRef = await addDoc(collection(db, "jobs"), {
        status: 'pending_art_generation',
        prompt: prompt.trim(),
        createdAt: serverTimestamp(),
        aspectRatio,
        steps,
        guidance,
        safetyTolerance,
        seed: seed === -1 ? Math.floor(Math.random() * 1000000) : seed,
        promptUpsampling,
      });
      
      setSuccessMessage(`Art generation job submitted successfully! Job ID: ${docRef.id.slice(0, 8)}...`);
      setPrompt('');
      
      // Clear success message after 5 seconds
      setTimeout(() => setSuccessMessage(null), 5000);
      
    } catch (e: any) {
      console.error("Error adding document: ", e);
      setError(`Failed to submit job: ${e.message || 'Unknown error'}`);
    } finally {
      setIsLoading(false);
    }
  };

  const theme = {
    colors: {
      primary: '#5865f2',
      surface: '#23272a',
      text: '#ffffff',
      textMuted: '#99aab5',
      border: '#40444b',
      error: '#ed4245',
      success: '#57f287',
    },
    borderRadius: '8px',
  };

  const styles = {
    card: {
      backgroundColor: theme.colors.surface,
      padding: '1.5rem',
      borderRadius: theme.borderRadius,
      border: `1px solid ${theme.colors.border}`,
    },
    title: {
      color: theme.colors.text,
      margin: '0 0 0.5rem 0'
    },
    subtitle: {
      color: theme.colors.textMuted,
      margin: '0 0 1.5rem 0',
      fontSize: '0.9rem'
    },
    formGroup: {
      marginBottom: '1rem',
      textAlign: 'left' as const,
    },
    label: {
      display: 'block',
      marginBottom: '0.5rem',
      color: theme.colors.text,
      fontSize: '0.9rem',
    },
    input: {
      width: '100%',
      padding: '8px',
      borderRadius: '4px',
      border: `1px solid ${theme.colors.border}`,
      backgroundColor: '#1a1a1a',
      color: theme.colors.text,
      boxSizing: 'border-box' as const,
    },
    textarea: {
      width: '100%',
      padding: '8px',
      borderRadius: '4px',
      border: `1px solid ${theme.colors.border}`,
      backgroundColor: '#1a1a1a',
      color: theme.colors.text,
      boxSizing: 'border-box' as const,
      resize: 'vertical' as const,
      minHeight: '80px',
    },
    button: {
      width: '100%',
      padding: '15px',
      fontSize: '1rem',
      cursor: 'pointer',
      border: 'none',
      background: theme.colors.primary,
      color: 'white',
      borderRadius: '8px',
      fontWeight: 'bold',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      gap: '8px',
      transition: 'all 0.2s ease',
    },
    buttonDisabled: {
      background: theme.colors.textMuted,
      cursor: 'not-allowed',
      opacity: 0.6,
    },
    message: {
      padding: '12px',
      borderRadius: '6px',
      marginBottom: '1rem',
      fontSize: '0.9rem',
      textAlign: 'center' as const,
    },
    errorMessage: {
      backgroundColor: `${theme.colors.error}20`,
      color: theme.colors.error,
      border: `1px solid ${theme.colors.error}40`,
    },
    successMessage: {
      backgroundColor: `${theme.colors.success}20`,
      color: theme.colors.success,
      border: `1px solid ${theme.colors.success}40`,
    },
    spinner: {
      width: '20px',
      height: '20px',
      border: '2px solid transparent',
      borderTop: '2px solid white',
      borderRadius: '50%',
      animation: 'spin 1s linear infinite',
    },
  };

  return (
    <div style={styles.card}>
      <style>
        {`
          @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
          }
        `}
      </style>
      <h3 style={styles.title}>Generator Controls</h3>
      <p style={styles.subtitle}>Configure your art generation parameters.</p>

      {/* Error Message */}
      {error && (
        <div style={{...styles.message, ...styles.errorMessage}}>
          ❌ {error}
        </div>
      )}

      {/* Success Message */}
      {successMessage && (
        <div style={{...styles.message, ...styles.successMessage}}>
          ✅ {successMessage}
        </div>
      )}
      
      <div style={styles.formGroup}>
        <label style={styles.label}>Prompt *</label>
        <textarea
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder="Describe the image you want to generate..."
          style={styles.textarea}
        />
      </div>

      <div style={styles.formGroup}>
        <label style={styles.label}>Aspect Ratio</label>
        <select value={aspectRatio} onChange={(e) => setAspectRatio(e.target.value)} style={styles.input}>
          <option value="16:9">16:9 (Landscape)</option>
          <option value="1:1">1:1 (Square)</option>
          <option value="9:16">9:16 (Portrait)</option>
        </select>
      </div>

      <div style={styles.formGroup}>
        <label style={styles.label}>Steps: {steps}</label>
        <p style={{...styles.subtitle, margin: '0 0 0.5rem 0', fontSize: '0.8rem'}}>
          More steps = better quality, but slower generation
        </p>
        <input
          type="range"
          min="0"
          max="50"
          value={steps}
          onChange={(e) => setSteps(Number(e.target.value))}
          style={{width: '100%'}}
        />
      </div>

      <div style={styles.formGroup}>
        <label style={styles.label}>Guidance: {guidance}</label>
        <p style={{...styles.subtitle, margin: '0 0 0.5rem 0', fontSize: '0.8rem'}}>
        High guidance scales improve prompt adherence at the cost of reduced realism
        </p>
        <input
          type="range"
          min="1.5"
          max="5"
          step="0.1"
          value={guidance}
          onChange={(e) => setGuidance(Number(e.target.value))}
          style={{width: '100%'}}
        />
      </div>

      <div style={styles.formGroup}>
        <label style={styles.label}>Safety Tolerance: {safetyTolerance}</label>
        <input
          type="range"
          min="0"
          max="6"
          step="1"
          value={safetyTolerance}
          onChange={(e) => setSafetyTolerance(Number(e.target.value))}
          style={{width: '100%'}}
        />
      </div>

      <div style={styles.formGroup}>
        <label style={styles.label}>Seed</label>
        <p style={{...styles.subtitle, margin: '0 0 0.5rem 0', fontSize: '0.8rem'}}>
          Use -1 for random, or specific number for reproducible results
        </p>
        <input
          type="number"
          value={seed}
          onChange={(e) => setSeed(Number(e.target.value))}
          style={styles.input}
        />
      </div>

      <div style={styles.formGroup}>
        <label style={styles.label}>
          <input
            type="checkbox"
            checked={promptUpsampling}
            onChange={(e) => setPromptUpsampling(e.target.checked)}
            style={{marginRight: '8px'}}
          />
          Prompt Upsampling
        </label>
      </div>

      <button 
        onClick={handleGenerateClick} 
        disabled={isLoading}
        style={{
          ...styles.button,
          ...(isLoading ? styles.buttonDisabled : {})
        }}
      >
        {isLoading ? (
          <>
            <div style={styles.spinner}></div>
            Submitting...
          </>
        ) : (
          <>
            ✨ Generate Art
          </>
        )}
      </button>

      <JobStatus />
    </div>
  );
};

export default ControlPanel;