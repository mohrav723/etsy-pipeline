import React from 'react';
import { CheckCircleOutlined } from '@ant-design/icons';
import './SuccessAnimation.css';

interface SuccessAnimationProps {
  show: boolean;
  onComplete?: () => void;
}

const SuccessAnimation: React.FC<SuccessAnimationProps> = ({ show, onComplete }) => {
  React.useEffect(() => {
    if (show && onComplete) {
      const timer = setTimeout(onComplete, 2000);
      return () => clearTimeout(timer);
    }
  }, [show, onComplete]);

  if (!show) return null;

  return (
    <div className="success-animation-overlay">
      <div className="success-animation-content">
        <CheckCircleOutlined className="success-icon" />
        <div className="success-text">Mockup Generated Successfully!</div>
      </div>
    </div>
  );
};

export default SuccessAnimation;