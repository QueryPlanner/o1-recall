import React from 'react';

export const TopicSkeleton: React.FC = () => (
  <div className="space-y-4 animate-pulse">
    {[1, 2, 3, 4].map((i) => (
      <div key={i} className="bg-white p-6 rounded-2xl border-2 border-gray-200">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 bg-gray-200 rounded-xl" />
          <div className="flex-1">
            <div className="h-6 bg-gray-200 rounded w-3/4 mb-2" />
            <div className="h-4 bg-gray-200 rounded w-1/2" />
          </div>
        </div>
      </div>
    ))}
  </div>
);

export const SubTopicSkeleton: React.FC = () => (
  <div className="space-y-4 animate-pulse">
    {[1, 2, 3].map((i) => (
      <div key={i} className="bg-white p-4 rounded-2xl border-2 border-gray-200">
        <div className="flex items-center gap-4">
          <div className="w-20 h-20 bg-gray-200 rounded-xl" />
          <div className="flex-1">
            <div className="h-6 bg-gray-200 rounded w-2/3 mb-2" />
            <div className="h-3 bg-gray-200 rounded-full w-full mb-2" />
            <div className="h-4 bg-gray-200 rounded w-1/3" />
          </div>
        </div>
      </div>
    ))}
  </div>
);

export const QuestionSkeleton: React.FC = () => (
  <div className="animate-pulse">
    <div className="h-8 bg-gray-200 rounded w-3/4 mb-8" />
    <div className="space-y-3">
      {[1, 2, 3, 4].map((i) => (
        <div key={i} className="h-16 bg-gray-200 rounded-2xl" />
      ))}
    </div>
  </div>
);

export const StreakSkeleton: React.FC = () => (
  <div className="bg-gradient-to-r from-orange-400 to-orange-500 rounded-2xl p-6 shadow-lg animate-pulse">
    <div className="flex items-center justify-between mb-4">
      <div className="flex items-center gap-3">
        <div className="w-14 h-14 bg-orange-300 rounded-full" />
        <div>
          <div className="h-10 w-16 bg-orange-300 rounded mb-2" />
          <div className="h-4 w-24 bg-orange-300 rounded" />
        </div>
      </div>
      <div className="text-right">
        <div className="h-8 w-16 bg-orange-300 rounded mb-2 ml-auto" />
        <div className="h-3 w-28 bg-orange-300 rounded ml-auto" />
      </div>
    </div>

    {/* Progress bar skeleton */}
    <div className="w-full bg-orange-300 rounded-full h-3 overflow-hidden mb-3">
      <div className="bg-white/50 h-full rounded-full w-1/2" />
    </div>

    <div className="h-3 w-3/4 bg-orange-300 rounded mx-auto" />
  </div>
);

