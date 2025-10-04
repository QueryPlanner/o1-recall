import React from 'react';
import type { StreakResponse } from '../types';

interface StreakDisplayProps {
  streak: StreakResponse;
}

const StreakDisplay: React.FC<StreakDisplayProps> = ({ streak }) => {
  const { current_streak_days, today_answers_count, streak_goal } = streak;
  const progressPercent = Math.min((today_answers_count / streak_goal) * 100, 100);

  return (
    <div className="bg-gradient-to-r from-orange-400 to-orange-500 rounded-2xl p-6 text-white shadow-lg">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="text-5xl">🔥</div>
          <div>
            <div className="text-3xl font-extrabold">{current_streak_days}</div>
            <div className="text-sm font-medium opacity-90">day streak!</div>
          </div>
        </div>
        <div className="text-right">
          <div className="text-2xl font-bold">{today_answers_count}/{streak_goal}</div>
          <div className="text-xs font-medium opacity-90">questions today</div>
        </div>
      </div>

      {/* Progress bar */}
      <div className="w-full bg-orange-300 rounded-full h-3 overflow-hidden">
        <div
          className="bg-white h-full rounded-full transition-all duration-500 ease-out"
          style={{ width: `${progressPercent}%` }}
        />
      </div>

      <p className="text-xs mt-3 text-center opacity-90">
        {today_answers_count >= streak_goal
          ? 'Great job! Your streak is safe today! 🎉'
          : `Answer ${streak_goal - today_answers_count} more to keep your streak!`}
      </p>
    </div>
  );
};

export default StreakDisplay;

