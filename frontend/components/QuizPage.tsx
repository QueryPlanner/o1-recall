import React, { useState, useMemo, useCallback } from 'react';
import type { Question } from '../types';
import { api } from '../api';
import ProgressBar from './ProgressBar';
import { CloseIcon, HeartIcon, InfinityIcon } from './icons';

interface QuizPageProps {
  subTopicName: string;
  questions: Question[];
  onClose: () => void;
}

const QuizPage: React.FC<QuizPageProps> = ({ subTopicName, questions, onClose }) => {
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [selectedChoiceId, setSelectedChoiceId] = useState<number | null>(null);
  const [isCorrect, setIsCorrect] = useState<boolean | null>(null);
  const [correctChoiceId, setCorrectChoiceId] = useState<number | null>(null);
  const [lives, setLives] = useState(5);
  const [totalCorrect, setTotalCorrect] = useState(0);
  const [showCompletion, setShowCompletion] = useState(false);
  const [completionStats, setCompletionStats] = useState<{
    xp: number;
    accuracyPercent: number;
    correctCount: number;
    totalCount: number;
  } | null>(null);

  const currentQuestion = questions[currentQuestionIndex];

  // Prefetch: compute correct choice id from question payload
  const correctChoiceIdFromPayload = useMemo(() => {
    return currentQuestion?.choices.find(c => c.is_correct)?.id ?? null;
  }, [currentQuestion]);

  const handleAnswerSelect = useCallback((choiceId: number) => {
    if (selectedChoiceId !== null) return;

    // Instant UI feedback using pre-fetched correct id
    const immediateCorrectId = correctChoiceIdFromPayload;
    const immediateIsCorrect = choiceId === immediateCorrectId;

    setSelectedChoiceId(choiceId);
    setIsCorrect(immediateIsCorrect);
    if (immediateCorrectId !== null) setCorrectChoiceId(immediateCorrectId);

    if (immediateIsCorrect) {
      setTotalCorrect(prev => prev + 1);
    } else {
      setLives(prev => Math.max(0, prev - 1));
    }

    // Log to backend in the background (non-blocking)
    (async () => {
      try {
        await api.submitAnswer({
          question_id: currentQuestion.id,
          choice_id: choiceId,
        });
      } catch (error) {
        // Non-blocking; log error for observability
        console.error('Failed to submit answer:', error);
      }
    })();
  }, [selectedChoiceId, currentQuestion, correctChoiceIdFromPayload]);

  const handleContinue = () => {
    const isLastQuestion = currentQuestionIndex >= questions.length - 1;

    if (!isLastQuestion) {
      setCurrentQuestionIndex(prev => prev + 1);
      setSelectedChoiceId(null);
      setIsCorrect(null);
      setCorrectChoiceId(null);
      return;
    }

    const totalCount = questions.length;
    const correctCount = totalCorrect;
    const accuracyPercent = totalCount > 0
      ? Math.round((correctCount / totalCount) * 100)
      : 0;
    const xp = correctCount * 10;

    setCompletionStats({ xp, accuracyPercent, correctCount, totalCount });
    setShowCompletion(true);
  };

  const handleRetry = () => {
    setCurrentQuestionIndex(0);
    setSelectedChoiceId(null);
    setIsCorrect(null);
    setCorrectChoiceId(null);
    setLives(5);
    setTotalCorrect(0);
    setShowCompletion(false);
    setCompletionStats(null);
  };

  if (!currentQuestion) {
    return (
      <div className="text-center p-8">
        <h2 className="text-2xl font-bold">No questions available.</h2>
        <button
          onClick={onClose}
          className="mt-4 px-6 py-2 bg-[#58CC02] text-white rounded-2xl font-bold hover:bg-[#46A302] transition"
        >
          Back
        </button>
      </div>
    );
  }

  const getButtonClass = (choiceId: number) => {
    if (selectedChoiceId === null) {
      return 'bg-white border-gray-200 hover:bg-gray-50 hover:border-gray-300';
    }

    if (choiceId === selectedChoiceId) {
      return isCorrect
        ? 'bg-green-50 border-green-400 text-green-700'
        : 'bg-red-50 border-red-400 text-red-700';
    }

    if (choiceId === correctChoiceId) {
      return 'bg-green-50 border-green-400 text-green-700';
    }

    return 'bg-gray-50 border-gray-200 text-gray-400 cursor-not-allowed';
  };

  const progress = ((currentQuestionIndex) / questions.length) * 100;

  return (
    <div className="flex flex-col h-full min-h-[calc(100vh-2rem)]">
      {/* Header */}
      <header className="p-4 bg-white border-b-2 border-gray-200">
        <div className="flex items-center gap-4">
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition"
          >
            <CloseIcon />
          </button>
          <ProgressBar value={progress} />
          <div className="flex items-center text-red-500">
            <HeartIcon />
            <span className="font-bold text-lg ml-1">
              {lives > 0 ? lives : <InfinityIcon />}
            </span>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-grow flex flex-col items-center justify-center px-4 py-8 bg-white">
        <div className="w-full max-w-2xl">
          <h1 className="text-2xl md:text-3xl font-bold text-gray-800 mb-8">
            {currentQuestion.question_text}
          </h1>

          {currentQuestion.image_url && (
            <img
              src={currentQuestion.image_url}
              alt="Question illustration"
              className="mb-8 rounded-xl max-w-full h-auto max-h-60 mx-auto shadow-md"
            />
          )}

          <div className="w-full space-y-3">
            {currentQuestion.choices.map((choice) => (
              <button
                key={choice.id}
                onClick={() => handleAnswerSelect(choice.id)}
                disabled={selectedChoiceId !== null}
                className={`w-full text-left p-4 rounded-2xl border-2 text-lg font-bold transition-all duration-200 ${getButtonClass(
                  choice.id
                )}`}
              >
                {choice.choice_text}
              </button>
            ))}
          </div>
        </div>
      </main>

      {/* Answer Feedback Footer */}
      {selectedChoiceId !== null && (
        <footer
          className={`p-6 border-t-4 ${
            isCorrect
              ? 'bg-green-50 border-green-400'
              : 'bg-red-50 border-red-400'
          }`}
        >
          <div className="max-w-2xl mx-auto">
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
              <div className="flex-1">
                <h2
                  className={`text-2xl font-extrabold mb-2 ${
                    isCorrect ? 'text-green-600' : 'text-red-600'
                  }`}
                >
                  {isCorrect ? 'Excellent! 🎉' : 'Not quite right'}
                </h2>
                {currentQuestion.explanation && (
                  <p className="text-gray-700 text-sm leading-relaxed">
                    {currentQuestion.explanation}
                  </p>
                )}
              </div>

              <button
                onClick={handleContinue}
                className={`px-10 py-4 rounded-2xl text-white font-bold uppercase text-lg shadow-lg transition-all duration-200 ${
                  isCorrect
                    ? 'bg-[#58CC02] hover:bg-[#46A302] hover:shadow-xl'
                    : 'bg-red-500 hover:bg-red-600 hover:shadow-xl'
                }`}
              >
                Continue
              </button>
            </div>
          </div>
        </footer>
      )}

      {/* Completion Modal */}
      {showCompletion && completionStats && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div className="absolute inset-0 bg-black/50" aria-hidden="true" />
          <div
            role="dialog"
            aria-modal="true"
            className="relative bg-white rounded-3xl shadow-2xl w-[90%] max-w-lg p-8 text-center border-2 border-gray-200"
          >
            <h2 className="text-3xl font-extrabold text-gray-800 mb-2">Practice Complete 🎉</h2>
            <p className="text-gray-600 mb-6">Great work on "{subTopicName}"</p>

            <div className="grid grid-cols-3 gap-4 mb-8">
              <div className="bg-gray-50 rounded-2xl p-4 border border-gray-200">
                <div className="text-xs uppercase tracking-wider text-gray-500 font-bold">XP</div>
                <div className="text-2xl font-extrabold text-[#58CC02] mt-1">{completionStats.xp}</div>
              </div>
              <div className="bg-gray-50 rounded-2xl p-4 border border-gray-200">
                <div className="text-xs uppercase tracking-wider text-gray-500 font-bold">Accuracy</div>
                <div className="text-2xl font-extrabold text-gray-800 mt-1">{completionStats.accuracyPercent}%</div>
              </div>
              <div className="bg-gray-50 rounded-2xl p-4 border border-gray-200">
                <div className="text-xs uppercase tracking-wider text-gray-500 font-bold">Correct</div>
                <div className="text-2xl font-extrabold text-gray-800 mt-1">{completionStats.correctCount}/{completionStats.totalCount}</div>
              </div>
            </div>

            <div className="flex flex-col sm:flex-row gap-3 justify-center">
              <button
                onClick={onClose}
                className="px-8 py-3 rounded-2xl bg-[#58CC02] hover:bg-[#46A302] text-white font-bold uppercase shadow-lg transition"
              >
                Finish
              </button>
              <button
                onClick={handleRetry}
                className="px-8 py-3 rounded-2xl bg-white border-2 border-gray-300 hover:border-gray-400 text-gray-700 font-bold uppercase shadow-sm transition"
              >
                Retry
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default QuizPage;
