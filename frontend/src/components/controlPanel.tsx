import React, { useState } from 'react';
import { db } from '../firebase';
import { collection, addDoc, serverTimestamp } from 'firebase/firestore';

const ControlPanel = () => {
  const [prompt, setPrompt] = useState('');
  const [aspectRatio, setAspectRatio] = useState('16:9');
  const [steps, setSteps] = useState(28);
  const [guidance, setGuidance] = useState(3);
  const [safetyTolerance, setSafetyTolerance] = useState(2);
  const [seed, setSeed] = useState(42);
  const [promptUpsampling, setPromptUpsampling] = useState(false);

  const handleGenerateClick = async () => {
    if (!prompt.trim()) {
      alert("Please enter a prompt before generating.");
      return;
    }
    
    console.log("Submitting new job to Firestore...");
    try {
      await addDoc(collection(db, "jobs"), {
        status: 'pending_art_generation',
        prompt: prompt.trim(),
        createdAt: serverTimestamp(),
        aspectRatio,
        steps,
        guidance,
        safetyTolerance,
        seed,
        promptUpsampling,
        generationCount: 0,
      });
      alert("New art generation job has been submitted!");
      setPrompt('');
    } catch (e) {
      console.error("Error adding document: ", e);
      alert("Error submitting job. Check the console for details.");
    }
  };

  const theme = {
    colors: {
      primary: '#5865f2',
      surface: '#23272a',
      text: '#ffffff',
      textMuted: '#99aab5',
      border: '#40444b',
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
      fontWeight: 'bold'
    },
  };

  return (
    <div style={styles.card}>
      <h3 style={styles.title}>Generator Controls</h3>
      <p style={styles.subtitle}>Configure your art generation parameters.</p>
      
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

      <button onClick={handleGenerateClick} style={styles.button}>
        ✨ Generate Art
      </button>
    </div>
  );
};

export default ControlPanel;