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
  // State to manage the form fields, initialized with the job's data from Firestore
  const [prompt, setPrompt] = useState(job.prompt);
  const [aspectRatio, setAspectRatio] = useState(job.aspectRatio);
  const [steps, setSteps] = useState(job.steps);
  const [guidance, setGuidance] = useState(job.guidance);
  const [seed, setSeed] = useState(job.seed);
  const [promptUpsampling, setPromptUpsampling] = useState(job.promptUpsampling);
  const [safetyTolerance, setSafetyTolerance] = useState(job.safetyTolerance);

  const handleRegenerate = async () => {
    console.log(`Regenerating job ${job.id} with new parameters...`);
    const jobRef = doc(db, 'jobs', job.id);

    try {
      // Update the document in Firestore with the new settings from the UI
      await updateDoc(jobRef, {
        status: 'pending_art_generation', // Set status back for the worker to pick it up
        prompt,
        aspectRatio,
        steps,
        guidance,
        seed,
        promptUpsampling,
        safetyTolerance,
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

  // Basic styles to make the card look better
  const styles = {
    card: { border: '1px solid #ddd', padding: '1.5rem', borderRadius: '8px', display: 'flex', gap: '2rem', background: '#f9f9f9' },
    image: { width: '50%', objectFit: 'contain', borderRadius: '4px', background: '#e0e0e0', alignSelf: 'flex-start' },
    controls: { width: '50%', display: 'flex', flexDirection: 'column', gap: '1rem' },
    label: { marginBottom: '-0.5rem', fontSize: '0.9rem', color: '#555' },
    input: { width: '100%', padding: '8px', boxSizing: 'border-box' },
    buttonContainer: { marginTop: '1rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' },
    generationCount: { fontSize: '0.8rem', color: '#777' }
  } as const;

  // Helper function to calculate the aspect ratio for CSS
  const getAspectRatioValue = (ratio: string) => {
    const [width, height] = ratio.split(':').map(Number);
    return width / height;
  }

  return (
    <div style={styles.card}>
      {/* The image tag now has its aspect-ratio set dynamically */}
      <img 
        src={job.generatedImageUrl} 
        alt="AI generated art" 
        style={{
          ...styles.image,
          aspectRatio: getAspectRatioValue(aspectRatio)
        }} 
      />
      
      <div style={styles.controls}>
        <div>
          <label style={styles.label}>Aspect Ratio</label>
          <select value={aspectRatio} onChange={(e) => setAspectRatio(e.target.value)} style={styles.input}>
            <option value="16:9">16:9 (Landscape)</option>
            <option value="1:1">1:1 (Square)</option>
            <option value="9:16">9:16 (Portrait)</option>
          </select>
        </div>
        
        {/* The rest of the controls remain the same... */}
        <div>
          <label style={styles.label}>Prompt</label>
          <textarea value={prompt} onChange={(e) => setPrompt(e.target.value)} rows={3} style={styles.input}/>
        </div>
        
        <div>
          <label style={styles.label}>Steps: {steps}</label>
          <input type="range" min="10" max="100" value={steps} onChange={(e) => setSteps(Number(e.target.value))} style={{width: '100%'}} />
        </div>

        <div>
          <label style={styles.label}>Guidance: {guidance}</label>
          <input type="range" min="1" max="10" step="0.1" value={guidance} onChange={(e) => setGuidance(Number(e.target.value))} style={{width: '100%'}} />
        </div>

         <div>
          <label style={styles.label}>Safety Tolerance: {safetyTolerance}</label>
          <input type="range" min="1" max="10" step="0.5" value={safetyTolerance} onChange={(e) => setSafetyTolerance(Number(e.target.value))} style={{width: '100%'}} />
        </div>
        
        <div>
          <label style={styles.label}>Seed</label>
          <input type="number" value={seed} onChange={(e) => setSeed(Number(e.target.value))} style={styles.input}/>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <input 
                type="checkbox" 
                id="promptUpsampling" 
                checked={promptUpsampling} 
                onChange={(e) => setPromptUpsampling(e.target.checked)}
            />
            <label htmlFor="promptUpsampling" style={{ ...styles.label, marginBottom: 0 }}>Prompt Upsampling</label>
        </div>
        
        <div style={styles.buttonContainer}>
            <div>
              <button onClick={handleRegenerate}>Regenerate</button>
              <button onClick={handleApprove} style={{marginLeft: '0.5rem'}}>Approve</button>
            </div>
            <span style={styles.generationCount}>Generation: #{job.generationCount}</span>
        </div>
      </div>
    </div>
  );
};

export default ArtReviewCard;