import React from 'react';
import type { SubTopic } from '../types';

interface SubTopicListPageProps {
  topicName: string;
  subTopics: SubTopic[];
  onSelectSubTopic: (subTopic: SubTopic) => void;
  onBack: () => void;
}

const SUB_TOPIC_COLORS = [
  'bg-red-500',
  'bg-green-500',
  'bg-purple-500',
  'bg-yellow-500',
  'bg-blue-500',
  'bg-pink-500',
];

const SubTopicListPage: React.FC<SubTopicListPageProps> = ({
  topicName,
  subTopics,
  onSelectSubTopic,
  onBack,
}) => {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <button
          onClick={onBack}
          className="p-2 text-gray-600 hover:text-gray-900 transition"
        >
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
        </button>
        <h1 className="text-2xl font-bold text-gray-800">{topicName}</h1>
        <div className="w-6" />
      </div>

      {/* Sub-topics Grid - Achievement Style */}
      <div className="space-y-4">
        {subTopics.map((subTopic, index) => {
          const colorClass = SUB_TOPIC_COLORS[index % SUB_TOPIC_COLORS.length];
          
          return (
            <button
              key={subTopic.id}
              onClick={() => onSelectSubTopic(subTopic)}
              className="w-full bg-white rounded-2xl p-4 border-2 border-gray-200 hover:border-gray-300 transition-all duration-200 hover:shadow-lg"
            >
              <div className="flex items-center gap-4">
                {/* Icon/Badge */}
                <div className={`${colorClass} rounded-xl p-4 flex items-center justify-center min-w-[80px] min-h-[80px]`}>
                  <span className="text-white text-3xl font-bold">
                    {subTopic.name.charAt(0).toUpperCase()}
                  </span>
                </div>

                {/* Content */}
                <div className="flex-1 text-left">
                  <h3 className="text-xl font-bold text-gray-800 mb-1">{subTopic.name}</h3>
                  <div className="w-full bg-gray-200 rounded-full h-3 mb-2">
                    <div className="bg-yellow-400 h-3 rounded-full" style={{ width: '100%' }} />
                  </div>
                  <p className="text-sm text-gray-600">Start practicing</p>
                </div>

                {/* Arrow */}
                <svg className="w-6 h-6 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
};

export default SubTopicListPage;

