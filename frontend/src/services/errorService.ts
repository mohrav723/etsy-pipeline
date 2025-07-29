import { message } from 'antd';
import { FirebaseError } from 'firebase/app';
import { AppError } from '../types';

export class ErrorService {
  private static isDevelopment = import.meta.env.DEV;

  /**
   * Main error handler - processes any error and returns a user-friendly message
   */
  static handle(error: unknown, context: string): AppError {
    // Log to console in development only
    if (this.isDevelopment) {
      console.error(`Error in ${context}:`, error);
    }

    // Handle Firebase errors
    if (error instanceof FirebaseError) {
      return this.handleFirebaseError(error);
    }

    // Handle generic Error instances
    if (error instanceof Error) {
      return {
        message: error.message,
        code: 'GENERIC_ERROR',
        context,
      };
    }

    // Handle unknown errors
    return {
      message: 'An unexpected error occurred',
      code: 'UNKNOWN_ERROR',
      context,
    };
  }

  /**
   * Firebase-specific error handler
   */
  private static handleFirebaseError(error: FirebaseError): AppError {
    const errorMap: Record<string, string> = {
      'auth/user-not-found': 'User not found',
      'auth/wrong-password': 'Invalid password',
      'auth/email-already-in-use': 'Email is already registered',
      'auth/weak-password': 'Password is too weak',
      'auth/invalid-email': 'Invalid email address',
      'permission-denied': 'You do not have permission to perform this action',
      unavailable: 'Service is temporarily unavailable',
      'deadline-exceeded': 'Operation timed out',
      'resource-exhausted': 'Quota exceeded',
      'failed-precondition': 'Operation failed due to system state',
      aborted: 'Operation was cancelled',
      'already-exists': 'Resource already exists',
      'not-found': 'Resource not found',
    };

    const message = errorMap[error.code] || `Firebase error: ${error.message}`;

    return {
      message,
      code: error.code,
      context: 'firebase',
    };
  }

  /**
   * Display error message to user using Ant Design message
   */
  static showError(error: unknown, context: string): void {
    const appError = this.handle(error, context);
    message.error(appError.message);
  }

  /**
   * Get error message string from any error type
   */
  static getMessage(error: unknown): string {
    if (error instanceof Error) {
      return error.message;
    }
    if (typeof error === 'string') {
      return error;
    }
    return 'An unexpected error occurred';
  }

  /**
   * Check if error is a specific Firebase error code
   */
  static isFirebaseError(error: unknown, code: string): boolean {
    return error instanceof FirebaseError && error.code === code;
  }

  /**
   * Check if error is a network error
   */
  static isNetworkError(error: unknown): boolean {
    if (error instanceof Error) {
      return (
        error.message.toLowerCase().includes('network') ||
        error.message.toLowerCase().includes('fetch')
      );
    }
    return false;
  }

  /**
   * Format error for logging
   */
  static format(error: unknown, context: string): string {
    const appError = this.handle(error, context);
    return `[${appError.code}] ${appError.message} (Context: ${appError.context})`;
  }
}
