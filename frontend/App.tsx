import React, { useState, useEffect, useRef } from 'react';
import type { Topic, SubTopic, Question, StreakResponse } from './types';
import { api } from './api';
import TopicListPage from './components/TopicListPage';
import SubTopicListPage from './components/SubTopicListPage';
import QuizPage from './components/QuizPage';
import StreakDisplay from './components/StreakDisplay';
import { TopicSkeleton, SubTopicSkeleton, QuestionSkeleton, StreakSkeleton } from './components/SkeletonLoader';
import GeneratePage from './components/GeneratePage';

type View = 'topics' | 'subtopics' | 'quiz' | 'generate';

const App: React.FC = () => {
  const [view, setView] = useState<View>('topics');
  const [topics, setTopics] = useState<Topic[]>([]);
  const [selectedTopic, setSelectedTopic] = useState<Topic | null>(null);
  const [subTopics, setSubTopics] = useState<SubTopic[]>([]);
  const [selectedSubTopic, setSelectedSubTopic] = useState<SubTopic | null>(null);
  const [questions, setQuestions] = useState<Question[]>([]);
  const [streak, setStreak] = useState<StreakResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Cache for pre-fetched sub-topics
  const subTopicsCache = useRef<Map<number, SubTopic[]>>(new Map());

  // Load topics and streak on mount
  useEffect(() => {
    loadTopics();
    loadStreak();
  }, []);

  const loadTopics = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getTopics();
      setTopics(data);
      
      // Pre-fetch sub-topics for all topics in the background
      data.forEach(topic => {
        if (!subTopicsCache.current.has(topic.id)) {
          api.getSubTopics(topic.id)
            .then(subTopics => {
              subTopicsCache.current.set(topic.id, subTopics);
            })
            .catch(err => console.error(`Failed to pre-fetch sub-topics for topic ${topic.id}:`, err));
        }
      });
    } catch (err) {
      setError('Failed to load topics. Please check your connection and ensure the backend is running.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const loadStreak = async () => {
    try {
      const data = await api.getStreak();
      setStreak(data);
    } catch (err) {
      console.error('Failed to load streak:', err);
    }
  };

  const handleStartRandom = async () => {
    setLoading(true);
    setError(null);
    setSelectedTopic(null);
    setSelectedSubTopic(null);
    try {
      const data = await api.getRandomQuestions(5);
      if (data.length === 0) {
        alert('No questions available yet!');
        return;
      }
      setQuestions(data);
      setView('quiz');
    } catch (err) {
      setError('Failed to load random questions');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleOpenGenerate = () => {
    setSuccess(null);
    setView('generate');
  };

  const handleSelectTopic = async (topic: Topic) => {
    setSelectedTopic(topic);
    setError(null);

    // Check cache first
    const cached = subTopicsCache.current.get(topic.id);
    if (cached) {
      setSubTopics(cached);
      setView('subtopics');
      return;
    }

    // If not cached, fetch with loading state
    setLoading(true);
    try {
      const data = await api.getSubTopics(topic.id);
      subTopicsCache.current.set(topic.id, data);
      setSubTopics(data);
      setView('subtopics');
    } catch (err) {
      setError('Failed to load sub-topics');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleSelectSubTopic = async (subTopic: SubTopic) => {
    setLoading(true);
    setError(null);
    setSelectedSubTopic(subTopic);
    try {
      const data = await api.getQuestions(subTopic.id, 5);
      if (data.length === 0) {
        alert('No questions available for this sub-topic yet!');
        return;
      }
      setQuestions(data);
      setView('quiz');
    } catch (err) {
      setError('Failed to load questions');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleQuizClose = () => {
    // If quiz started from random, go back to topics; otherwise back to subtopics
    if (selectedSubTopic == null) {
      setView('topics');
    } else {
      setView('subtopics');
    }
    setQuestions([]);
    setSelectedSubTopic(null);
    loadStreak(); // Refresh streak after quiz
  };

  const handleBackToTopics = () => {
    setView('topics');
    setSubTopics([]);
    setSelectedTopic(null);
  };

  const handleGenerateSuccess = (summary: {created: number; requested: number; topic: string}) => {
    setSuccess(`Added ${summary.created}/${summary.requested} questions under topic “${summary.topic}”.`);
    // Refresh topics in background
    loadTopics();
    setView('topics');
  };

  // Auto-dismiss success toast after 5 seconds
  useEffect(() => {
    if (!success) return;
    const t = setTimeout(() => setSuccess(null), 5000);
    return () => clearTimeout(t);
  }, [success]);

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-50 to-gray-100">
      <div className="container mx-auto max-w-4xl p-4">
        {/* Header with Streak */}
        {view === 'topics' && (
          <div className="mb-6">
            {streak ? <StreakDisplay streak={streak} /> : <StreakSkeleton />}
          </div>
        )}

        {/* Success Toast */}
        {success && (
          <div className="mb-4 p-4 bg-green-50 border-2 border-green-200 text-green-700 rounded-2xl">
            {success}
          </div>
        )}

        {/* Error Message */}
        {error && (
          <div className="mb-6 p-4 bg-red-50 border-2 border-red-200 rounded-2xl">
            <p className="text-red-600 font-medium">{error}</p>
          </div>
        )}

        {/* Content with skeleton loaders */}
        {view === 'topics' && (
          <>
            <div className="flex justify-end mb-4">
              <button
                onClick={handleOpenGenerate}
                className="px-4 py-2 rounded-2xl bg-[#58CC02] text-white font-bold hover:bg-[#46A302] shadow"
              >
                + Create Questions
              </button>
            </div>
            {loading ? (
              <TopicSkeleton />
            ) : (
              <TopicListPage
                topics={topics}
                onSelectTopic={handleSelectTopic}
                onStartRandom={handleStartRandom}
              />
            )}
          </>
        )}

        {view === 'generate' && (
          <GeneratePage onBack={() => setView('topics')} onSuccess={handleGenerateSuccess} />)
        }

        {view === 'subtopics' && selectedTopic && (
          <>
            {loading ? (
              <SubTopicSkeleton />
            ) : (
              <SubTopicListPage
                topicName={selectedTopic.name}
                subTopics={subTopics}
                onSelectSubTopic={handleSelectSubTopic}
                onBack={handleBackToTopics}
              />
            )}
          </>
        )}

        {view === 'quiz' && (
          <>
            {loading ? (
              <div className="bg-white rounded-2xl p-8">
                <QuestionSkeleton />
              </div>
            ) : questions.length > 0 ? (
              <QuizPage
                subTopicName={selectedSubTopic ? selectedSubTopic.name : 'Random Practice'}
                questions={questions}
                onClose={handleQuizClose}
              />
            ) : null}
          </>
        )}

        {/* Footer */}
        {view === 'topics' && !loading && (
          <div className="mt-12 text-center text-sm text-gray-500">
            <p>Keep learning every day to maintain your streak! 🔥</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default App;
