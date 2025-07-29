/**
 * Secure download utility with URL validation
 */

interface DownloadOptions {
  filename?: string;
  onProgress?: (progress: number) => void;
  onError?: (error: Error) => void;
}

/**
 * Validates if a URL is safe for download
 */
function isValidDownloadUrl(url: string): boolean {
  try {
    const parsed = new URL(url);
    
    // Only allow HTTPS in production
    if (import.meta.env.MODE === 'production' && parsed.protocol !== 'https:') {
      return false;
    }
    
    // Allow HTTP and HTTPS in development
    if (!['http:', 'https:'].includes(parsed.protocol)) {
      return false;
    }
    
    // Check for suspicious patterns
    const suspiciousPatterns = [
      /javascript:/i,
      /data:(?!image\/(png|jpeg|jpg|gif|webp))/i, // Allow only image data URLs
      /vbscript:/i,
      /file:/i,
      /about:/i,
    ];
    
    return !suspiciousPatterns.some(pattern => pattern.test(url));
  } catch {
    return false;
  }
}

/**
 * Validates if URL is from trusted domains
 */
function isTrustedDomain(url: string, trustedDomains: string[] = []): boolean {
  try {
    const parsed = new URL(url);
    const hostname = parsed.hostname.toLowerCase();
    
    // Default trusted domains
    const defaultTrusted = [
      'firebasestorage.googleapis.com',
      'storage.googleapis.com',
      'your-bucket-name.appspot.com', // Replace with your actual bucket
    ];
    
    const allTrusted = [...defaultTrusted, ...trustedDomains];
    
    return allTrusted.some(domain => 
      hostname === domain || hostname.endsWith(`.${domain}`)
    );
  } catch {
    return false;
  }
}

/**
 * Securely download a file using blob URL
 */
async function secureDownload(
  url: string, 
  options: DownloadOptions = {},
  trustedDomains?: string[]
): Promise<void> {
  const { filename, onProgress, onError } = options;
  
  // Validate URL
  if (!isValidDownloadUrl(url)) {
    const error = new Error('Invalid download URL');
    if (onError) onError(error);
    throw error;
  }
  
  // Check trusted domains if specified
  if (trustedDomains && !isTrustedDomain(url, trustedDomains)) {
    const error = new Error('URL is not from a trusted domain');
    if (onError) onError(error);
    throw error;
  }
  
  try {
    // Fetch the file with progress tracking
    const response = await fetch(url);
    
    if (!response.ok) {
      throw new Error(`Download failed: ${response.statusText}`);
    }
    
    // Get content length for progress tracking
    const contentLength = response.headers.get('content-length');
    const total = contentLength ? parseInt(contentLength, 10) : 0;
    
    // Read the response as a stream
    const reader = response.body?.getReader();
    if (!reader) {
      throw new Error('Unable to read response body');
    }
    
    const chunks: Uint8Array[] = [];
    let receivedLength = 0;
    
    while (true) {
      const { done, value } = await reader.read();
      
      if (done) break;
      
      chunks.push(value);
      receivedLength += value.length;
      
      // Report progress
      if (onProgress && total > 0) {
        onProgress((receivedLength / total) * 100);
      }
    }
    
    // Create blob from chunks
    const blob = new Blob(chunks);
    
    // Create secure blob URL
    const blobUrl = URL.createObjectURL(blob);
    
    // Create download link
    const link = document.createElement('a');
    link.href = blobUrl;
    link.download = filename || getFilenameFromUrl(url) || 'download';
    
    // Trigger download
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    // Clean up blob URL after a delay
    setTimeout(() => URL.revokeObjectURL(blobUrl), 100);
    
  } catch (error) {
    const downloadError = error instanceof Error ? error : new Error('Download failed');
    if (onError) onError(downloadError);
    throw downloadError;
  }
}

/**
 * Extract filename from URL
 */
function getFilenameFromUrl(url: string): string | null {
  try {
    const parsed = new URL(url);
    const pathname = parsed.pathname;
    const filename = pathname.split('/').pop();
    return filename || null;
  } catch {
    return null;
  }
}

/**
 * Create a secure download handler for React components
 */
function useSecureDownload(trustedDomains?: string[]) {
  const download = async (
    url: string, 
    filename?: string,
    onProgress?: (progress: number) => void
  ) => {
    try {
      await secureDownload(url, { filename, onProgress }, trustedDomains);
    } catch (error) {
      console.error('Download failed:', error);
      throw error;
    }
  };
  
  return { download };
}

export { 
  secureDownload, 
  isValidDownloadUrl, 
  isTrustedDomain,
  useSecureDownload,
  type DownloadOptions 
};