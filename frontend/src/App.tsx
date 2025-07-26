import React from 'react';
import ArtReviewCard from './components/artReviewCard';

// Import Firestore functions and the db connection
import { db } from './firebase'; 
import { collection, addDoc, serverTimestamp } from 'firebase/firestore';

// Your mockJob can stay for now to keep the UI from being empty
const mockJob = {
  id: 'job123',
  generatedImageUrl: 'https://placehold.co/600x400/223344/E0E0E0?text=Generated+Art',
  prompt: 'A cozy, lamp-lit reading nook on a rainy night, impressionist style, visible brushstrokes.',
  model: 'FLUX.1.1 [pro]',
  aspectRatio: '16:9',
  steps: 50,
  guidance: 3.5,
  safetyTolerance: 2,
  seed: -1,
  generationCount: 1,
  status: 'pending_review'
};

function App() {
  const handleGenerateClick = async () => {
    const samplePrompt = "A quiet, forgotten corner of a Parisian library in late afternoon, shafts of golden sunlight streaming through a tall, arched window and illuminating dust motes dancing in the air, impressionist style.";
    
    try {
      await addDoc(collection(db, "jobs"), {
        // Set the status the worker is listening for
        status: 'pending_art_generation',
        // Include the prompt directly
        prompt: samplePrompt,
        createdAt: serverTimestamp(),
        aspectRatio: '16:9',
      });
      alert("Art generation job has been submitted!");
    } catch (e) {
      console.error("Error adding document: ", e);
      alert("Error submitting job.");
    }
};

  return (
    <div style={{ maxWidth: '1000px', margin: '2rem auto', padding: '0 1rem', fontFamily: 'sans-serif' }}>
      <header style={{ marginBottom: '2rem', textAlign: 'center' }}>
        <h1>Etsy Pipeline Dashboard</h1>
        <p>Click the button below to have AI generate a new art prompt and image for your review.</p>
        <button 
          onClick={handleGenerateClick}
          style={{ padding: '15px 30px', fontSize: '1.2rem', cursor: 'pointer', border: 'none', background: '#007bff', color: 'white', borderRadius: '5px' }}
        >
          ✨ Generate New Art Idea
        </button>
      </header>
      <hr style={{margin: '2rem 0', border: 'none', borderTop: '1px solid #eee'}} />
      <main>
        <h2 style={{textAlign: 'center', marginBottom: '1.5rem'}}>Art for Review</h2>
        {/* The mock job is still here, but soon we will replace this with a real-time list */}
        {mockJob && <ArtReviewCard job={mockJob} />}
      </main>
    </div>
  );
}

export default App;