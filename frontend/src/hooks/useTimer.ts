import { useState, useEffect, useCallback, useRef } from 'react';

export function useTimer(totalSeconds: number, onTimeout: () => void) {
  const [remaining, setRemaining] = useState(totalSeconds);
  const [isRunning, setIsRunning] = useState(true);
  const onTimeoutRef = useRef(onTimeout);

  onTimeoutRef.current = onTimeout;

  useEffect(() => {
    if (!isRunning || remaining <= 0) return;
    const interval = setInterval(() => {
      setRemaining((prev) => {
        if (prev <= 1) {
          setIsRunning(false);
          onTimeoutRef.current();
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
    return () => clearInterval(interval);
  }, [isRunning, remaining]);

  const formatTime = useCallback(() => {
    const h = Math.floor(remaining / 3600);
    const m = Math.floor((remaining % 3600) / 60);
    const s = remaining % 60;
    return `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  }, [remaining]);

  const pause = useCallback(() => setIsRunning(false), []);
  const resume = useCallback(() => setIsRunning(true), []);

  return {
    remaining,
    isRunning,
    formatTime,
    pause,
    resume,
    setRemaining,
  };
}
