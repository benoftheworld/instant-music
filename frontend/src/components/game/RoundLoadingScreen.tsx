import { useEffect, useState, useRef } from 'react';

interface RoundLoadingScreenProps {
  roundNumber: number;
  onComplete: () => void;
  duration?: number; // in seconds, default 10
}

export default function RoundLoadingScreen({ 
  roundNumber, 
  onComplete, 
  duration = 10 
}: RoundLoadingScreenProps) {
  const [timeRemaining, setTimeRemaining] = useState(duration);
  const [progress, setProgress] = useState(0);
  const onCompleteRef = useRef(onComplete);

  // Keep ref updated with latest callback
  useEffect(() => {
    onCompleteRef.current = onComplete;
  }, [onComplete]);

  useEffect(() => {
    const startTime = Date.now();
    const endTime = startTime + (duration * 1000);

    const interval = setInterval(() => {
      const now = Date.now();
      const remaining = Math.max(0, Math.ceil((endTime - now) / 1000));
      const progressPercent = Math.min(100, ((duration - remaining) / duration) * 100);
      
      setTimeRemaining(remaining);
      setProgress(progressPercent);

      if (remaining <= 0) {
        clearInterval(interval);
        onCompleteRef.current();
      }
    }, 100);

    return () => clearInterval(interval);
  }, [duration]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 flex items-center justify-center p-4">
      <div className="max-w-md w-full">
        <div className="bg-white/10 backdrop-blur-lg rounded-2xl shadow-2xl p-8 text-center">
          {/* Round Number */}
          <div className="mb-8">
            <div className="inline-block bg-gradient-to-r from-yellow-400 to-orange-500 text-white px-6 py-2 rounded-full text-sm font-bold mb-4 shadow-lg">
              Round {roundNumber}
            </div>
            <h2 className="text-4xl font-bold text-white mb-2">
              Préparez-vous !
            </h2>
            <p className="text-purple-200 text-lg">
              Le round va commencer...
            </p>
          </div>

          {/* Countdown */}
          <div className="mb-8">
            <div className={`text-8xl font-bold transition-all duration-300 ${
              timeRemaining <= 3 ? 'text-red-400 animate-pulse scale-110' : 'text-white'
            }`}>
              {timeRemaining}
            </div>
            <p className="text-purple-200 mt-2">secondes</p>
          </div>

          {/* Progress Bar */}
          <div className="w-full bg-white/20 rounded-full h-3 overflow-hidden">
            <div 
              className="h-full bg-gradient-to-r from-green-400 to-blue-500 transition-all duration-300 ease-linear rounded-full"
              style={{ width: `${progress}%` }}
            />
          </div>

          {/* Animation */}
          <div className="mt-8 flex justify-center gap-2">
            {[0, 1, 2].map((i) => (
              <div
                key={i}
                className="w-4 h-4 bg-purple-400 rounded-full animate-bounce"
                style={{ animationDelay: `${i * 0.15}s` }}
              />
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
