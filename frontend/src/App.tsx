import React, { useState, useEffect } from 'react';
import ArtReviewCard, { Job } from './components/artReviewCard';
import ControlPanel from './components/controlPanel';
import HistoryTab from './components/historyTab';
import { db } from './firebase';
import { collection, onSnapshot, query, where, orderBy, limit } from 'firebase/firestore';

function App() {
  const [reviewJobs, setReviewJobs] = useState<Job[]>([]);
  const [activeTab, setActiveTab] = useState<'review' | 'history'>('review');

  // Listen for only the most recent pending_review job
  useEffect(() => {
    const jobsCollection = collection(db, 'jobs');
    const q = query(
      jobsCollection, 
      where('status', '==', 'pending_review'),
      orderBy('createdAt', 'desc'),
      limit(1)
    );

    const unsubscribe = onSnapshot(q, (snapshot) => {
      const jobsFromFirestore: Job[] = [];
      snapshot.forEach(doc => {
        const data = doc.data();
        console.log("Most recent job:", doc.id, data);
        jobsFromFirestore.push({ id: doc.id, ...data } as Job);
      });
      
      console.log("Latest job for review:", jobsFromFirestore);
      setReviewJobs(jobsFromFirestore);
    });

    return () => unsubscribe();
  }, []);

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
    noJobsMessage: { color: '#99aab5', textAlign: 'center', padding: '2rem', border: '2px dashed #40444b', borderRadius: '8px' },
    tabContainer: { display: 'flex', gap: '0.5rem', marginBottom: '1rem' },
    tab: {
      padding: '0.75rem 1.5rem',
      border: '1px solid #40444b',
      borderRadius: '8px 8px 0 0',
      backgroundColor: '#1a1a1a',
      color: '#99aab5',
      cursor: 'pointer',
      fontWeight: 'bold'
    },
    activeTab: {
      backgroundColor: '#23272a',
      color: '#ffffff',
      borderBottomColor: '#23272a'
    }
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
          <div style={styles.tabContainer}>
            <button
              style={{
                ...styles.tab,
                ...(activeTab === 'review' ? styles.activeTab : {})
              }}
              onClick={() => setActiveTab('review')}
            >
              Review ({reviewJobs.length})
            </button>
            <button
              style={{
                ...styles.tab,
                ...(activeTab === 'history' ? styles.activeTab : {})
              }}
              onClick={() => setActiveTab('history')}
            >
              History
            </button>
          </div>

          {activeTab === 'review' ? (
            reviewJobs.length > 0 ? (
              reviewJobs.map(job => (
                <ArtReviewCard key={job.id} job={job} />
              ))
            ) : (
              <div style={styles.noJobsMessage}>
                <p>No images are currently waiting for review.</p>
                <p>Use the form on the left to generate new art.</p>
              </div>
            )
          ) : (
            <HistoryTab />
          )}
        </div>
      </div>
    </div>
  );
}

export default App;