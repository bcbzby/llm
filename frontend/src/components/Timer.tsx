import { useTimer } from '../hooks/useTimer';

interface TimerProps {
  totalSeconds: number;
  onTimeout: () => void;
}

export default function Timer({ totalSeconds, onTimeout }: TimerProps) {
  const { formatTime, remaining } = useTimer(totalSeconds, onTimeout);

  const isWarning = remaining < 300; // 5 分钟警告
  const isDanger = remaining < 60;   // 1 分钟危险

  return (
    <div className={`flex items-center space-x-2 px-4 py-2 rounded-lg font-mono text-lg font-bold ${
      isDanger
        ? 'bg-red-100 text-red-600 animate-pulse'
        : isWarning
        ? 'bg-yellow-100 text-yellow-700'
        : 'bg-gray-100 text-gray-700'
    }`}>
      <span>⏱</span>
      <span>{formatTime()}</span>
    </div>
  );
}
