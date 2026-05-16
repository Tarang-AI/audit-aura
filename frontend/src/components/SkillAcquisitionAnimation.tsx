import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface Skill {
  skill_id: string;
  name: string;
  description: string;
  category: string;
  control_id?: string;
  standard?: string;
  severity?: string;
}

interface SkillAcquisitionAnimationProps {
  skills: Skill[];
  onComplete?: () => void;
}

const SkillAcquisitionAnimation: React.FC<SkillAcquisitionAnimationProps> = ({
  skills,
  onComplete,
}) => {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isVisible, setIsVisible] = useState(true);

  useEffect(() => {
    if (currentIndex < skills.length) {
      const timer = setTimeout(() => {
        setCurrentIndex(currentIndex + 1);
      }, 3000); // Show each skill for 3 seconds

      return () => clearTimeout(timer);
    } else if (currentIndex === skills.length && skills.length > 0) {
      // All skills shown, fade out after a delay
      const fadeTimer = setTimeout(() => {
        setIsVisible(false);
        if (onComplete) {
          setTimeout(onComplete, 500);
        }
      }, 2000);

      return () => clearTimeout(fadeTimer);
    }
  }, [currentIndex, skills.length, onComplete]);

  // Move early returns AFTER all hooks
  if (!isVisible || skills.length === 0) {
    return null;
  }

  const currentSkill = skills[currentIndex];

  if (!currentSkill) {
    return null;
  }

  const getCategoryColor = (category: string) => {
    switch (category.toLowerCase()) {
      case 'detection':
        return 'from-blue-500 to-cyan-500';
      case 'analysis':
        return 'from-orange-500 to-amber-500';
      case 'remediation':
        return 'from-green-500 to-emerald-500';
      default:
        return 'from-gray-500 to-slate-500';
    }
  };

  const getSeverityColor = (severity?: string) => {
    switch (severity?.toLowerCase()) {
      case 'critical':
        return 'text-red-500';
      case 'high':
        return 'text-orange-500';
      case 'medium':
        return 'text-yellow-500';
      case 'low':
        return 'text-blue-500';
      default:
        return 'text-gray-500';
    }
  };

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50 backdrop-blur-sm"
      >
        <motion.div
          key={currentSkill.skill_id}
          initial={{ scale: 0, rotate: -180 }}
          animate={{ scale: 1, rotate: 0 }}
          exit={{ scale: 0, rotate: 180 }}
          transition={{
            type: 'spring',
            stiffness: 260,
            damping: 20,
          }}
          className="relative max-w-md w-full mx-4"
        >
          {/* Glow effect */}
          <motion.div
            className={`absolute inset-0 bg-gradient-to-r ${getCategoryColor(
              currentSkill.category
            )} rounded-2xl blur-xl opacity-75`}
            animate={{
              scale: [1, 1.1, 1],
              opacity: [0.75, 0.9, 0.75],
            }}
            transition={{
              duration: 2,
              repeat: Infinity,
              ease: 'easeInOut',
            }}
          />

          {/* Card */}
          <div className="relative bg-gray-900 rounded-2xl p-8 shadow-2xl border border-gray-700">
            {/* Header */}
            <motion.div
              initial={{ y: -20, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              transition={{ delay: 0.2 }}
              className="text-center mb-6"
            >
              <motion.div
                animate={{
                  rotate: [0, 360],
                }}
                transition={{
                  duration: 2,
                  repeat: Infinity,
                  ease: 'linear',
                }}
                className="inline-block mb-4"
              >
                <svg
                  className="w-16 h-16 text-cyan-400"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M13 10V3L4 14h7v7l9-11h-7z"
                  />
                </svg>
              </motion.div>
              <h2 className="text-2xl font-bold text-white mb-2">
                New Skill Acquired!
              </h2>
              <p className="text-gray-400 text-sm">
                Detection Agent Enhanced
              </p>
            </motion.div>

            {/* Skill Details */}
            <motion.div
              initial={{ y: 20, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              transition={{ delay: 0.4 }}
              className="space-y-4"
            >
              {/* Skill Name */}
              <div>
                <h3 className="text-xl font-semibold text-white mb-2">
                  {currentSkill.name}
                </h3>
                <p className="text-gray-300 text-sm">
                  {currentSkill.description}
                </p>
              </div>

              {/* Metadata */}
              <div className="flex flex-wrap gap-2">
                <span
                  className={`px-3 py-1 rounded-full text-xs font-medium bg-gradient-to-r ${getCategoryColor(
                    currentSkill.category
                  )} text-white`}
                >
                  {currentSkill.category}
                </span>
                {currentSkill.standard && (
                  <span className="px-3 py-1 rounded-full text-xs font-medium bg-gray-700 text-gray-200">
                    {currentSkill.standard}
                  </span>
                )}
                {currentSkill.severity && (
                  <span
                    className={`px-3 py-1 rounded-full text-xs font-medium bg-gray-700 ${getSeverityColor(
                      currentSkill.severity
                    )}`}
                  >
                    {currentSkill.severity.toUpperCase()}
                  </span>
                )}
              </div>

              {currentSkill.control_id && (
                <div className="text-xs text-gray-400">
                  Control ID: {currentSkill.control_id}
                </div>
              )}
            </motion.div>

            {/* Progress */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.6 }}
              className="mt-6"
            >
              <div className="flex justify-between text-xs text-gray-400 mb-2">
                <span>
                  Skill {currentIndex + 1} of {skills.length}
                </span>
                <span>
                  {Math.round(((currentIndex + 1) / skills.length) * 100)}%
                </span>
              </div>
              <div className="w-full bg-gray-700 rounded-full h-2 overflow-hidden">
                <motion.div
                  className={`h-full bg-gradient-to-r ${getCategoryColor(
                    currentSkill.category
                  )}`}
                  initial={{ width: 0 }}
                  animate={{
                    width: `${((currentIndex + 1) / skills.length) * 100}%`,
                  }}
                  transition={{ duration: 0.5 }}
                />
              </div>
            </motion.div>

            {/* Particles effect */}
            {[...Array(6)].map((_, i) => (
              <motion.div
                key={i}
                className="absolute w-2 h-2 bg-cyan-400 rounded-full"
                initial={{
                  x: '50%',
                  y: '50%',
                  opacity: 1,
                }}
                animate={{
                  x: `${50 + Math.cos((i * Math.PI) / 3) * 150}%`,
                  y: `${50 + Math.sin((i * Math.PI) / 3) * 150}%`,
                  opacity: 0,
                }}
                transition={{
                  duration: 1.5,
                  repeat: Infinity,
                  delay: i * 0.1,
                }}
              />
            ))}
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
};

export default SkillAcquisitionAnimation;