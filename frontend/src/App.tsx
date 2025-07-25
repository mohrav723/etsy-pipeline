import React from 'react';
import ArtReviewCard from './components/artReviewCard';

// Updated mock job with all the new fields
const mockJob = {
  id: 'job123',
  generatedImageUrl: 'https://placehold.co/600x400/223344/E0E0E0?text=Generated+Art',
  prompt: 'A cozy, lamp-lit reading nook on a rainy night, impressionist style, visible brushstrokes.',
  model: 'FLUX.1.1 [pro]',
  aspectRatio: '16:9',
  steps: 50,
  guidance: 3.5,
  safetyTolerance: 2,
  seed: 12345,
  generationCount: 1, // Starting at the first generation
  status: 'pending_review'
};


function App() {
  const handleGenerateClick = () => {
    console.log('New art generation process initiated!');
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
        {mockJob && <ArtReviewCard job={mockJob} />}
      </main>
    </div>
  );
}

export default App;