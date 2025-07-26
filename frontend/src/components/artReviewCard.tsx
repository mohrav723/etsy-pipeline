import React, { useState } from 'react';

// Define the structure of a Job object with the new fields
type Job = {
  id: string;
  generatedImageUrl: string;
  prompt: string;
  model: string;
  aspectRatio: string;
  steps: number;
  guidance: number;
  safetyTolerance: number;
  seed: number;
  generationCount: number;
};

// The props for our component will be a single job object
type ArtReviewCardProps = {
  job: Job;
};

const ArtReviewCard = ({ job }: ArtReviewCardProps) => {
  // Use state to manage the form fields, initialized with the job's data
  const [prompt, setPrompt] = useState(job.prompt);
  const [model, setModel] = useState(job.model);
  const [aspectRatio, setAspectRatio] = useState(job.aspectRatio);
  const [steps, setSteps] = useState(job.steps);
  const [guidance, setGuidance] = useState(job.guidance);
  const [safetyTolerance, setSafetyTolerance] = useState(job.safetyTolerance);
  const [seed, setSeed] = useState(job.seed);

  const handleRegenerate = () => {
    // Placeholder: This will eventually update the Firestore document
    console.log('Regenerating with new parameters:', {
      ...job,
      prompt,
      model,
      aspectRatio,
      steps,
      guidance,
      safetyTolerance,
      seed,
    });
  };
  
  const handleApprove = () => {
    // Placeholder: This will set the job status to 'approved'
    console.log('Approving job:', job.id);
  }

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
          <label style={styles.label}>Model</label>
          <select value={model} onChange={(e) => setModel(e.target.value)} style={styles.input}>
            <option value="FLUX.1.1 [pro]">FLUX.1.1 [pro] ($0.04/image)</option>
            <option value="FLUX.1.0 [schnell]">FLUX.1.0 [schnell]</option>
          </select>
        </div>

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