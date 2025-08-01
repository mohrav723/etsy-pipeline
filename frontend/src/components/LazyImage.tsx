import React, { useState, useEffect, useRef } from 'react';
import { Spin } from 'antd';

interface LazyImageProps {
  src: string;
  alt: string;
  className?: string;
  style?: React.CSSProperties;
  placeholder?: string;
  onLoad?: () => void;
  onError?: () => void;
}

const LazyImage: React.FC<LazyImageProps> = ({
  src,
  alt,
  className,
  style,
  placeholder,
  onLoad,
  onError,
}) => {
  const [isIntersecting, setIsIntersecting] = useState(false);
  const [isLoaded, setIsLoaded] = useState(false);
  const [hasError, setHasError] = useState(false);
  const imgRef = useRef<HTMLDivElement>(null);
  const [imageSrc, setImageSrc] = useState(placeholder || '');

  useEffect(() => {
    if (!imgRef.current) return;

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsIntersecting(true);
          observer.disconnect();
        }
      },
      {
        threshold: 0.1,
        rootMargin: '50px',
      }
    );

    observer.observe(imgRef.current);

    return () => {
      observer.disconnect();
    };
  }, []);

  useEffect(() => {
    if (isIntersecting && src) {
      const img = new Image();
      img.src = src;
      
      img.onload = () => {
        setImageSrc(src);
        setIsLoaded(true);
        setHasError(false);
        onLoad?.();
      };
      
      img.onerror = () => {
        setHasError(true);
        setIsLoaded(true);
        onError?.();
      };
    }
  }, [isIntersecting, src, onLoad, onError]);

  const containerStyle: React.CSSProperties = {
    position: 'relative',
    backgroundColor: '#2a2a2a',
    overflow: 'hidden',
    ...style,
  };

  const imageStyle: React.CSSProperties = {
    width: '100%',
    height: '100%',
    objectFit: 'cover',
    transition: 'opacity 0.3s ease-in-out',
    opacity: isLoaded ? 1 : 0,
  };

  const loadingStyle: React.CSSProperties = {
    position: 'absolute',
    top: '50%',
    left: '50%',
    transform: 'translate(-50%, -50%)',
  };

  return (
    <div ref={imgRef} className={className} style={containerStyle}>
      {!isLoaded && !hasError && (
        <div style={loadingStyle}>
          <Spin />
        </div>
      )}
      
      {isIntersecting && !hasError && (
        <img
          src={imageSrc}
          alt={alt}
          style={imageStyle}
          loading="lazy"
        />
      )}
      
      {hasError && (
        <div
          style={{
            ...imageStyle,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            backgroundColor: '#1a1a1a',
            color: '#666',
          }}
        >
          Failed to load image
        </div>
      )}
    </div>
  );
};

export default LazyImage;