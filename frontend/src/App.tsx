import React, { useState, useEffect } from 'react';
import ArtReviewCard, { Job } from './components/artReviewCard';
import ControlPanel from './components/controlPanel';
import { db } from './firebase';
import { collection, onSnapshot, query, where } from 'firebase/firestore';

function App() {
  // State to hold the list of jobs fetched from Firestore
  const [reviewJobs, setReviewJobs] = useState<Job[]>([]);

  // This useEffect hook sets up the real-time listener when the app loads
  useEffect(() => {
    // Reference to the 'jobs' collection in Firestore
    const jobsCollection = collection(db, 'jobs');
    
    // Create a query to only listen for documents where the status is 'pending_review'
    const q = query(jobsCollection, where('status', '==', 'pending_review'));

    // onSnapshot creates the real-time listener. This function will be called
    // every time the query results change.
    const unsubscribe = onSnapshot(q, (snapshot) => {
      const jobsFromFirestore: Job[] = [];
      snapshot.forEach(doc => {
        // Important: We cast the document data to our Job type
        jobsFromFirestore.push({ id: doc.id, ...doc.data() } as Job);
      });
      
      console.log("Real-time update. Jobs for review:", jobsFromFirestore);
      setReviewJobs(jobsFromFirestore);
    });

    // This is a cleanup function. It unsubscribes from the listener
    // when the component is removed, preventing memory leaks.
    return () => unsubscribe();
  }, []); // The empty array [] means this effect runs only once on mount

  // Apply the dark theme to the page
  useEffect(() => {
    document.body.style.backgroundColor = '#1a1a1a';
    document.body.style.color = '#e0e0e0';
  }, []);

  const styles = {
    app: { maxWidth: '1400px', margin: '2rem auto', padding: '0 2rem', fontFamily: 'system-ui, sans-serif' },
    header: { paddingBottom: '1rem', borderBottom: '1px solid #333' },
    title: { color: '#ffffff', fontWeight: 600, margin: 0 },
    mainLayout: { display: 'flex', gap: '2rem', marginTop: '2rem' },
    leftColumn: { width: '300px', flexShrink: 0 },
    rightColumn: { flexGrow: 1, display: 'flex', flexDirection: 'column', gap: '1.5rem' },
    sectionTitle: { marginTop: 0, color: '#ffffff' },
    noJobsMessage: { color: '#99aab5', textAlign: 'center', padding: '2rem', border: '2px dashed #40444b', borderRadius: '8px' }
  } as const;

  return (
    <div style={styles.app}>
      <header style={styles.header}>
        <h1 style={styles.title}>Etsy Pipeline Dashboard</h1>
      </header>
      
      <div style={styles.mainLayout}>
        <div style={styles.leftColumn}>
          <ControlPanel />
        </div>

        <div style={styles.rightColumn}>
          <h2 style={styles.sectionTitle}>Art for Review ({reviewJobs.length})</h2>
          
          {reviewJobs.length > 0 ? (
            // Map over the real jobs from Firestore and render a card for each
            reviewJobs.map(job => (
              <ArtReviewCard key={job.id} job={job} />
            ))
          ) : (
            <div style={styles.noJobsMessage}>
              <p>No images are currently waiting for review.</p>
              <p>Click "Generate New Art Idea" to start.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default App;