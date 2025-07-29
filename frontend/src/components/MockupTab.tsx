import React, { useState, useEffect, useRef } from 'react';
import { db } from '../firebase';
import {
  collection,
  addDoc,
  onSnapshot,
  query,
  orderBy,
  deleteDoc,
  doc,
  Timestamp,
} from 'firebase/firestore';
import { getStorage, ref, uploadBytes, getDownloadURL, deleteObject } from 'firebase/storage';
import { Mockup } from '../types';
import { FILE_SIZE_LIMIT_BYTES, ALLOWED_FILE_TYPES, IMAGE_PREVIEW_HEIGHT } from '../constants';

const MockupTab = () => {
  const [mockups, setMockups] = useState<Mockup[]>([]);
  const [uploading, setUploading] = useState(false);
  const [dragActive, setDragActive] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const storage = getStorage();

  useEffect(() => {
    const mockupsCollection = collection(db, 'mockups');
    const q = query(mockupsCollection, orderBy('uploadedAt', 'desc'));

    const unsubscribe = onSnapshot(q, (snapshot) => {
      const mockupsFromFirestore: Mockup[] = [];
      snapshot.forEach((doc) => {
        mockupsFromFirestore.push({ id: doc.id, ...doc.data() } as Mockup);
      });
      setMockups(mockupsFromFirestore);
    });

    return () => unsubscribe();
  }, []);

  const handleFileUpload = async (files: FileList | null) => {
    if (!files || files.length === 0) return;

    setUploading(true);
    setError(null);
    setSuccessMessage(null);

    try {
      for (let i = 0; i < files.length; i++) {
        const file = files[i];

        // Validate file type and size
        if (!ALLOWED_FILE_TYPES.includes(file.type)) {
          throw new Error(`File ${file.name} must be JPEG, PNG, or WebP format`);
        }

        if (file.size > FILE_SIZE_LIMIT_BYTES) {
          throw new Error(
            `File ${file.name} is too large. Maximum size is ${FILE_SIZE_LIMIT_BYTES / (1024 * 1024)}MB`
          );
        }

        // Create a reference to the file in Firebase Storage
        const storageRef = ref(storage, `mockups/${Date.now()}_${file.name}`);

        // Upload the file
        const snapshot = await uploadBytes(storageRef, file);
        const downloadURL = await getDownloadURL(snapshot.ref);

        // Save metadata to Firestore
        await addDoc(collection(db, 'mockups'), {
          name: file.name.split('.')[0], // Remove file extension
          fileName: file.name,
          imageUrl: downloadURL,
          uploadedAt: Timestamp.now(),
        });
      }

      setSuccessMessage(`Successfully uploaded ${files.length} mockup(s)!`);
      setTimeout(() => setSuccessMessage(null), 3000);
    } catch (error) {
      setError(`Failed to upload: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setUploading(false);
    }
  };

  const handleDeleteMockup = async (mockup: Mockup) => {
    if (!confirm(`Are you sure you want to delete "${mockup.name}"?`)) return;

    try {
      // Delete from Firebase Storage
      const storageRef = ref(storage, mockup.imageUrl);
      await deleteObject(storageRef);

      // Delete from Firestore
      await deleteDoc(doc(db, 'mockups', mockup.id));

      setSuccessMessage('Mockup deleted successfully!');
      setTimeout(() => setSuccessMessage(null), 3000);
    } catch (error) {
      setError(`Failed to delete: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragActive(false);
    handleFileUpload(e.dataTransfer.files);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setDragActive(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setDragActive(false);
  };

  const styles = {
    container: {
      display: 'flex',
      flexDirection: 'column' as const,
      gap: '1.5rem',
    },
    uploadArea: {
      border: `2px dashed ${dragActive ? '#5865f2' : '#40444b'}`,
      borderRadius: '8px',
      padding: '2rem',
      textAlign: 'center' as const,
      backgroundColor: dragActive ? '#5865f220' : '#23272a',
      cursor: 'pointer',
      transition: 'all 0.2s ease',
    },
    uploadText: {
      color: '#99aab5',
      fontSize: '1.1rem',
      marginBottom: '1rem',
    },
    uploadButton: {
      backgroundColor: '#5865f2',
      color: 'white',
      border: 'none',
      padding: '0.75rem 1.5rem',
      borderRadius: '6px',
      cursor: 'pointer',
      fontSize: '1rem',
      fontWeight: 'bold',
    },
    hiddenInput: {
      display: 'none',
    },
    message: {
      padding: '12px',
      borderRadius: '6px',
      fontSize: '0.9rem',
      textAlign: 'center' as const,
    },
    errorMessage: {
      backgroundColor: '#ed424520',
      color: '#ed4245',
      border: '1px solid #ed424540',
    },
    successMessage: {
      backgroundColor: '#57f28720',
      color: '#57f287',
      border: '1px solid #57f28740',
    },
    mockupsGrid: {
      display: 'grid',
      gridTemplateColumns: 'repeat(auto-fill, minmax(250px, 1fr))',
      gap: '1rem',
    },
    mockupCard: {
      backgroundColor: '#23272a',
      border: '1px solid #40444b',
      borderRadius: '8px',
      overflow: 'hidden',
      transition: 'transform 0.2s ease',
    },
    mockupImage: {
      width: '100%',
      height: IMAGE_PREVIEW_HEIGHT,
      objectFit: 'cover' as const,
    },
    mockupInfo: {
      padding: '1rem',
    },
    mockupName: {
      color: '#ffffff',
      fontSize: '1rem',
      fontWeight: 'bold',
      marginBottom: '0.5rem',
    },
    mockupDate: {
      color: '#99aab5',
      fontSize: '0.8rem',
      marginBottom: '1rem',
    },
    deleteButton: {
      backgroundColor: '#ed4245',
      color: 'white',
      border: 'none',
      padding: '0.5rem 1rem',
      borderRadius: '4px',
      cursor: 'pointer',
      fontSize: '0.8rem',
    },
    loadingOverlay: {
      position: 'fixed' as const,
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      backgroundColor: 'rgba(0, 0, 0, 0.5)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 1000,
    },
    loadingContent: {
      backgroundColor: '#23272a',
      padding: '2rem',
      borderRadius: '8px',
      color: '#ffffff',
      textAlign: 'center' as const,
    },
    sectionTitle: {
      color: '#ffffff',
      fontSize: '1.2rem',
      fontWeight: 'bold',
      marginBottom: '1rem',
    },
  };

  return (
    <div style={styles.container}>
      {/* Upload Area */}
      <div
        style={styles.uploadArea}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onClick={() => fileInputRef.current?.click()}
      >
        <div style={styles.uploadText}>
          {dragActive
            ? 'Drop your mockup images here!'
            : 'Drag & drop mockup images here, or click to browse'}
        </div>
        <button style={styles.uploadButton} type="button">
          Choose Files
        </button>
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept="image/*"
          style={styles.hiddenInput}
          onChange={(e) => handleFileUpload(e.target.files)}
        />
      </div>

      {/* Messages */}
      {error && <div style={{ ...styles.message, ...styles.errorMessage }}>❌ {error}</div>}

      {successMessage && (
        <div style={{ ...styles.message, ...styles.successMessage }}>✅ {successMessage}</div>
      )}

      {/* Mockups Grid */}
      <div>
        <h3 style={styles.sectionTitle}>Your Mockups ({mockups.length})</h3>

        {mockups.length === 0 ? (
          <div
            style={{
              ...styles.message,
              backgroundColor: '#40444b20',
              color: '#99aab5',
              border: '1px solid #40444b',
            }}
          >
            No mockups uploaded yet. Upload some mockup images to get started!
          </div>
        ) : (
          <div style={styles.mockupsGrid}>
            {mockups.map((mockup) => (
              <div key={mockup.id} style={styles.mockupCard}>
                <img src={mockup.imageUrl} alt={mockup.name} style={styles.mockupImage} />
                <div style={styles.mockupInfo}>
                  <div style={styles.mockupName}>{mockup.name}</div>
                  <div style={styles.mockupDate}>
                    {mockup.uploadedAt?.toDate
                      ? mockup.uploadedAt.toDate().toLocaleDateString()
                      : 'Unknown date'}
                  </div>
                  <button style={styles.deleteButton} onClick={() => handleDeleteMockup(mockup)}>
                    Delete
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Loading Overlay */}
      {uploading && (
        <div style={styles.loadingOverlay}>
          <div style={styles.loadingContent}>
            <div>Uploading mockups...</div>
            <div style={{ marginTop: '1rem', fontSize: '0.9rem', color: '#99aab5' }}>
              Please wait while we process your images
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default MockupTab;
