import React, { useState, useEffect } from 'react';
import { db } from '../firebase';
import { collection, onSnapshot, query, orderBy, where } from 'firebase/firestore';
import { Card, Typography, Empty, Spin, Image } from 'antd';
import { FileImageOutlined } from '@ant-design/icons';

const { Text, Title } = Typography;

type Draft = {
  id: string;
  originalImageUrl: string;
  mockupImageUrl: string;
  mockupName: string;
  originalJobId: string;
  createdAt: any;
  status: 'processing' | 'completed' | 'failed';
};

const DraftsTab = () => {
  const [drafts, setDrafts] = useState<Draft[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const draftsCollection = collection(db, 'drafts');
    const q = query(draftsCollection, orderBy('createdAt', 'desc'));

    const unsubscribe = onSnapshot(q, (snapshot) => {
      const draftsFromFirestore: Draft[] = [];
      snapshot.forEach(doc => {
        draftsFromFirestore.push({ id: doc.id, ...doc.data() } as Draft);
      });
      setDrafts(draftsFromFirestore);
      setLoading(false);
    });

    return () => unsubscribe();
  }, []);

  const styles = {
    container: {
      display: 'flex',
      flexDirection: 'column' as const,
      gap: '1.5rem'
    },
    header: {
      color: '#ffffff',
      fontSize: '1.2rem',
      fontWeight: 'bold',
      marginBottom: '1rem'
    },
    draftsGrid: {
      display: 'grid',
      gridTemplateColumns: 'repeat(auto-fill, minmax(350px, 1fr))',
      gap: '1rem'
    },
    draftCard: {
      backgroundColor: '#23272a',
      border: '1px solid #40444b',
      borderRadius: '8px',
      overflow: 'hidden'
    },
    imageContainer: {
      display: 'flex',
      gap: '8px',
      padding: '16px'
    },
    imageWrapper: {
      flex: 1,
      textAlign: 'center' as const
    },
    imageLabel: {
      color: '#99aab5',
      fontSize: '0.8rem',
      marginBottom: '8px',
      fontWeight: 'bold'
    },
    image: {
      width: '100%',
      height: '150px',
      objectFit: 'cover' as const,
      borderRadius: '4px',
      border: '1px solid #40444b'
    },
    cardInfo: {
      padding: '16px',
      borderTop: '1px solid #40444b'
    },
    mockupName: {
      color: '#ffffff',
      fontSize: '1rem',
      fontWeight: 'bold',
      marginBottom: '8px'
    },
    status: {
      fontSize: '0.8rem',
      padding: '4px 8px',
      borderRadius: '4px',
      display: 'inline-block',
      marginBottom: '8px'
    },
    statusProcessing: {
      backgroundColor: '#ffa50020',
      color: '#ffa500',
      border: '1px solid #ffa50040'
    },
    statusCompleted: {
      backgroundColor: '#57f28720',
      color: '#57f287',
      border: '1px solid #57f28740'
    },
    statusFailed: {
      backgroundColor: '#ed424520',
      color: '#ed4245',
      border: '1px solid #ed424540'
    },
    date: {
      color: '#99aab5',
      fontSize: '0.8rem'
    },
    loadingContainer: {
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      height: '200px'
    },
    emptyState: {
      textAlign: 'center' as const,
      padding: '40px',
      color: '#99aab5'
    }
  };

  const getStatusStyle = (status: string) => {
    switch (status) {
      case 'processing':
        return { ...styles.status, ...styles.statusProcessing };
      case 'completed':
        return { ...styles.status, ...styles.statusCompleted };
      case 'failed':
        return { ...styles.status, ...styles.statusFailed };
      default:
        return styles.status;
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'processing':
        return '⏳ Processing';
      case 'completed':
        return '✅ Completed';
      case 'failed':
        return '❌ Failed';
      default:
        return status;
    }
  };

  if (loading) {
    return (
      <div style={styles.loadingContainer}>
        <Spin size="large" />
      </div>
    );
  }

  return (
    <div style={styles.container}>
      <Title level={3} style={styles.header}>
        <FileImageOutlined style={{ marginRight: '8px' }} />
        Draft Mockups ({drafts.length})
      </Title>

      {drafts.length === 0 ? (
        <div style={styles.emptyState}>
          <Empty
            image={Empty.PRESENTED_IMAGE_SIMPLE}
            description={
              <span style={{ color: '#99aab5' }}>
                No draft mockups yet. Approve images from the Review tab to generate mockups.
              </span>
            }
          />
        </div>
      ) : (
        <div style={styles.draftsGrid}>
          {drafts.map((draft) => (
            <Card key={draft.id} style={styles.draftCard}>
              <div style={styles.imageContainer}>
                <div style={styles.imageWrapper}>
                  <div style={styles.imageLabel}>Original</div>
                  <Image
                    src={draft.originalImageUrl}
                    alt="Original image"
                    style={styles.image}
                    preview={true}
                  />
                </div>
                <div style={styles.imageWrapper}>
                  <div style={styles.imageLabel}>Mockup</div>
                  {draft.status === 'processing' ? (
                    <div style={{
                      ...styles.image,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      backgroundColor: '#2f3136'
                    }}>
                      <Spin />
                    </div>
                  ) : draft.status === 'completed' ? (
                    <Image
                      src={draft.mockupImageUrl}
                      alt="Mockup"
                      style={styles.image}
                      preview={true}
                    />
                  ) : (
                    <div style={{
                      ...styles.image,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      backgroundColor: '#2f3136',
                      color: '#ed4245'
                    }}>
                      Failed
                    </div>
                  )}
                </div>
              </div>
              
              <div style={styles.cardInfo}>
                <div style={styles.mockupName}>{draft.mockupName}</div>
                <div style={getStatusStyle(draft.status)}>
                  {getStatusText(draft.status)}
                </div>
                <div style={styles.date}>
                  {draft.createdAt?.toDate ? 
                    draft.createdAt.toDate().toLocaleDateString() : 
                    'Unknown date'
                  }
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
};

export default DraftsTab;