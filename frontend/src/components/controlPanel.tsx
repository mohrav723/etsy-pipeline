import React from 'react';
import { db } from '../firebase';
import { collection, addDoc, serverTimestamp } from 'firebase/firestore';

const ControlPanel = () => {
  const handleGenerateClick = async () => {
    const samplePrompt = "A quiet, forgotten corner of a Parisian library in late afternoon, shafts of golden sunlight streaming through a tall, arched window and illuminating dust motes dancing in the air, impressionist style.";
    
    console.log("Submitting new job to Firestore...");
    try {
      await addDoc(collection(db, "jobs"), {
        // This is the status the backend worker is listening for
        status: 'pending_art_generation',
        // Provide all the default parameters for the first run
        prompt: samplePrompt,
        createdAt: serverTimestamp(),
        aspectRatio: '16:9',
        steps: 28,
        guidance: 3,
        safetyTolerance: 2,
        seed: 42,
        promptUpsampling: false,
        generationCount: 0, // The worker will increment this to 1
      });
      alert("New art generation job has been submitted!");
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
      textAlign: 'center' as const,
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
      <p style={styles.subtitle}>Start a new creation cycle.</p>
      <button onClick={handleGenerateClick} style={styles.button}>
        ✨ Generate New Art Idea
      </button>
    </div>
  );
};

export default ControlPanel;