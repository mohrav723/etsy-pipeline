/**
 * Firebase configuration with environment variable validation
 */

interface FirebaseConfig {
  apiKey: string;
  authDomain: string;
  projectId: string;
  storageBucket: string;
  messagingSenderId: string;
  appId: string;
  measurementId?: string;
}

interface ValidationError {
  field: string;
  message: string;
}

/**
 * Validates Firebase configuration
 */
function validateFirebaseConfig(): { config: FirebaseConfig | null; errors: ValidationError[] } {
  const errors: ValidationError[] = [];
  
  const requiredFields = [
    'VITE_FIREBASE_API_KEY',
    'VITE_FIREBASE_AUTH_DOMAIN',
    'VITE_FIREBASE_PROJECT_ID',
    'VITE_FIREBASE_STORAGE_BUCKET',
    'VITE_FIREBASE_MESSAGING_SENDER_ID',
    'VITE_FIREBASE_APP_ID',
  ] as const;

  // Check for missing required fields
  requiredFields.forEach((field) => {
    if (!import.meta.env[field]) {
      errors.push({
        field,
        message: `Missing required environment variable: ${field}`,
      });
    }
  });

  // Validate field formats
  const apiKey = import.meta.env.VITE_FIREBASE_API_KEY;
  if (apiKey && !apiKey.startsWith('AIza')) {
    errors.push({
      field: 'VITE_FIREBASE_API_KEY',
      message: 'Invalid Firebase API key format',
    });
  }

  const projectId = import.meta.env.VITE_FIREBASE_PROJECT_ID;
  if (projectId && !/^[a-z0-9-]+$/.test(projectId)) {
    errors.push({
      field: 'VITE_FIREBASE_PROJECT_ID',
      message: 'Invalid Firebase project ID format',
    });
  }

  if (errors.length > 0) {
    return { config: null, errors };
  }

  const config: FirebaseConfig = {
    apiKey: import.meta.env.VITE_FIREBASE_API_KEY!,
    authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN!,
    projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID!,
    storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET!,
    messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID!,
    appId: import.meta.env.VITE_FIREBASE_APP_ID!,
    measurementId: import.meta.env.VITE_FIREBASE_MEASUREMENT_ID,
  };

  return { config, errors: [] };
}

export { validateFirebaseConfig, type FirebaseConfig, type ValidationError };