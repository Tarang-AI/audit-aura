import React from 'react';

/**
 * Props for the ComplianceScoreGauge component
 */
interface ComplianceScoreGaugeProps {
  /** Compliance score (0-100) */
  score: number;
  /** Size of the gauge in pixels (default: 150) */
  size?: number;
  /** Whether to show percentage sign (default: true) */
  showPercentage?: boolean;
  /** Additional CSS classes */
  className?: string;
  /** Whether to show status text below the score (default: true) */
  showStatus?: boolean;
}

/**
 * Professional ComplianceScoreGauge component with orange/coral accent theme
 */
export const ComplianceScoreGauge: React.FC<ComplianceScoreGaugeProps> = ({
  score,
  size = 150,
  showPercentage = true,
  className = '',
  showStatus = true
}) => {
  // Clamp score between 0 and 100
  const clampedScore = Math.min(100, Math.max(0, score));

  // Calculate gauge colors based on score with professional accent colors
  const getGaugeColor = (): string => {
    if (clampedScore >= 90) return '#00ff88'; // status-success
    if (clampedScore >= 70) return '#ffea00'; // status-warning
    if (clampedScore >= 50) return '#FF6B35'; // accent-primary
    return '#ff006e'; // status-error
  };

  // Get status text based on score
  const getStatusText = (): string => {
    if (clampedScore >= 90) return 'Excellent';
    if (clampedScore >= 70) return 'Good';
    if (clampedScore >= 50) return 'Fair';
    if (clampedScore > 0) return 'Poor';
    return 'No Data';
  };

  // Get status badge class
  const getStatusBadgeClass = (): string => {
    if (clampedScore >= 90) return 'badge-success';
    if (clampedScore >= 70) return 'badge-warning';
    if (clampedScore >= 50) return 'badge-accent';
    return 'badge-error';
  };

  // Calculate stroke dasharray for the gauge
  const radius = (size / 2) - 14;
  const circumference = radius * 2 * Math.PI;
  const strokeDashoffset = circumference - (clampedScore / 100) * circumference;

  // Gradient ID for unique identification
  const gradientId = `gauge-gradient-${size}-${Math.random()}`;
  const glowId = `gauge-glow-${size}-${Math.random()}`;

  return (
    <div className={`relative inline-flex items-center justify-center ${className}`}>
      {/* Outer glow effect with accent color */}
      <div 
        className="absolute -inset-4 rounded-full opacity-20 blur-3xl animate-pulse-glow"
        style={{ background: `radial-gradient(circle, ${getGaugeColor()} 0%, transparent 70%)` }} 
      />

      {/* Gauge container */}
      <svg
        className="transform -rotate-90"
        width={size}
        height={size}
        viewBox={`0 0 ${size} ${size}`}
      >
        {/* Define gradient and glow */}
        <defs>
          <linearGradient id={gradientId} x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor={getGaugeColor()} stopOpacity={1} />
            <stop offset="100%" stopColor={getGaugeColor()} stopOpacity={0.7} />
          </linearGradient>
          <filter id={glowId}>
            <feGaussianBlur stdDeviation="4" result="coloredBlur"/>
            <feMerge>
              <feMergeNode in="coloredBlur"/>
              <feMergeNode in="SourceGraphic"/>
            </feMerge>
          </filter>
        </defs>

        {/* Background track */}
        <circle
          strokeWidth="16"
          stroke="var(--border-medium)"
          fill="transparent"
          r={radius}
          cx={size / 2}
          cy={size / 2}
        />

        {/* Tick marks */}
        {[0, 25, 50, 75, 100].map((tick) => {
          const tickRadius = radius + 8;
          const angle = (tick / 100) * 360 - 90;
          const x1 = size / 2 + tickRadius * Math.cos((angle * Math.PI) / 180);
          const y1 = size / 2 + tickRadius * Math.sin((angle * Math.PI) / 180);
          const x2 = size / 2 + (tickRadius + 4) * Math.cos((angle * Math.PI) / 180);
          const y2 = size / 2 + (tickRadius + 4) * Math.sin((angle * Math.PI) / 180);

          return (
            <line
              key={`tick-${tick}`}
              x1={x1}
              y1={y1}
              x2={x2}
              y2={y2}
              stroke="var(--border-strong)"
              strokeWidth={2}
            />
          );
        })}

        {/* Main gauge with gradient and glow */}
        <circle
          strokeWidth="16"
          strokeDasharray={circumference}
          strokeDashoffset={strokeDashoffset}
          strokeLinecap="round"
          stroke={`url(#${gradientId})`}
          fill="transparent"
          r={radius}
          cx={size / 2}
          cy={size / 2}
          filter={`url(#${glowId})`}
          className="transition-all duration-1000 ease-out"
          style={{
            transform: 'rotate(-90deg)',
            transformOrigin: '50% 50%',
          }}
        />
      </svg>

      {/* Score text with professional styling */}
      <div className="absolute text-center">
        <div
          className="text-4xl font-bold tracking-tight animate-pulse-glow"
          style={{ 
            color: getGaugeColor(), 
            textShadow: `0 0 20px ${getGaugeColor()}60`,
            fontFamily: 'inherit'
          }}
        >
          {showPercentage ? `${Math.round(clampedScore)}%` : Math.round(clampedScore)}
        </div>
        <div className="text-caption mt-1">
          {showPercentage ? 'Compliance' : 'Score'}
        </div>

        {/* Status indicator with professional badge */}
        {showStatus && (
          <div className={`badge ${getStatusBadgeClass()} mt-3 text-xs`}>
            {getStatusText()}
          </div>
        )}
      </div>
    </div>
  );
};

// Made with Bob