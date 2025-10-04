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
    if (currentQuestionIndex < questions.length - 1) {
      setCurrentQuestionIndex(prev => prev + 1);
      setSelectedChoiceId(null);
      setIsCorrect(null);
      setCorrectChoiceId(null);
    } else {
      // End of quiz - show completion screen
      const accuracy = Math.round((totalCorrect / questions.length) * 100);
      alert(`Practice Complete!\n\nTotal XP: ${totalCorrect * 10}\nAccuracy: ${accuracy}%`);
      onClose();
    }
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
    </div>
  );
};

export default QuizPage;
