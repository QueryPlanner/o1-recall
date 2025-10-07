import React from 'react';
import type { Topic } from '../types';

interface TopicListPageProps {
  topics: Topic[];
  onSelectTopic: (topic: Topic) => void;
  onStartRandom: () => void;
}

const TOPIC_ICONS = ['📚', '🎓', '🔬', '💻', '🌍', '🎨', '🎵', '⚽', '🍔', '🚀'];

const TopicListPage: React.FC<TopicListPageProps> = ({ topics, onSelectTopic, onStartRandom }) => {
  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-extrabold text-center text-gray-800 mb-8">
        Choose a Topic
      </h1>

      {/* Pinned Random Mode Card */}
      <button
        onClick={onStartRandom}
        className="w-full bg-gradient-to-r from-[#58CC02] to-[#46A302] text-white p-6 rounded-2xl shadow-lg hover:shadow-xl transition-all duration-200 transform hover:-translate-y-0.5"
      >
        <div className="flex items-center gap-4">
          <div className="text-5xl">🎲</div>
          <div className="flex-1 text-left">
            <h2 className="text-xl font-extrabold">Random Practice</h2>
            <p className="text-sm opacity-90">Select a random topic</p>
          </div>
          <svg
            className="w-6 h-6 opacity-90"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
        </div>
      </button>

      <div className="grid gap-4 md:grid-cols-2">
        {topics.map((topic, index) => {
          const icon = TOPIC_ICONS[index % TOPIC_ICONS.length];

          return (
            <button
              key={topic.id}
              onClick={() => onSelectTopic(topic)}
              className="group relative bg-white p-6 rounded-2xl border-2 border-gray-200 hover:border-[#58CC02] hover:shadow-xl transition-all duration-200 transform hover:-translate-y-1"
            >
              <div className="flex items-center gap-4">
                <div className="text-5xl group-hover:scale-110 transition-transform duration-200">
                  {icon}
                </div>
                <div className="flex-1 text-left">
                  <h2 className="text-xl font-bold text-gray-800 group-hover:text-[#58CC02] transition-colors">
                    {topic.name}
                  </h2>
                  <p className="text-sm text-gray-500 mt-1">
                    Tap to explore
                  </p>
                </div>
                <svg
                  className="w-6 h-6 text-gray-300 group-hover:text-[#58CC02] transition-colors"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9 5l7 7-7 7"
                  />
                </svg>
              </div>
            </button>
          );
        })}
      </div>

      {topics.length === 0 && (
        <div className="text-center py-12 text-gray-500">
          <p className="text-xl font-medium">No topics available yet.</p>
          <p className="text-sm mt-2">Upload content to generate questions!</p>
        </div>
      )}
    </div>
  );
};

export default TopicListPage;
