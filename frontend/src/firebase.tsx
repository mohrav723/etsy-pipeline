/// <reference types="vite/client" />
// Import the functions you need from the SDKs you need
import { initializeApp, FirebaseApp } from 'firebase/app';
import { getFirestore, Firestore } from 'firebase/firestore';
import { validateFirebaseConfig } from './config/firebase.config';

// Validate Firebase configuration
const { config: firebaseConfig, errors } = validateFirebaseConfig();

if (errors.length > 0) {
  const errorMessage = errors.map((e) => `${e.field}: ${e.message}`).join('\n');
  
  // In development, show detailed error
  if (import.meta.env.MODE === 'development') {
    console.error('Firebase configuration errors:\n', errorMessage);
    throw new Error(`Firebase configuration validation failed:\n${errorMessage}`);
  } else {
    // In production, show generic error
    throw new Error('Firebase configuration error. Please check your environment variables.');
  }
}

if (!firebaseConfig) {
  throw new Error('Firebase configuration is missing');
}

// Initialize Firebase with validated config
let app: FirebaseApp;
let db: Firestore;

try {
  app = initializeApp(firebaseConfig);
  db = getFirestore(app);
} catch (error) {
  console.error('Failed to initialize Firebase:', error);
  throw new Error('Failed to initialize Firebase. Please check your configuration.');
}

export { db };
