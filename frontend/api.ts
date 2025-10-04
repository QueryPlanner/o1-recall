import type { Topic, SubTopic, Question, AnswerRequest, AnswerResponse, StreakResponse } from './types';

const API_BASE_URL = 'http://localhost:8000';

export const api = {
  async getTopics(): Promise<Topic[]> {
    const response = await fetch(`${API_BASE_URL}/topics`);
    if (!response.ok) throw new Error('Failed to fetch topics');
    return response.json();
  },

  async getSubTopics(topicId: number): Promise<SubTopic[]> {
    const response = await fetch(`${API_BASE_URL}/topics/${topicId}/sub_topics`);
    if (!response.ok) throw new Error('Failed to fetch sub-topics');
    return response.json();
  },

  async getQuestions(subTopicId: number, limit: number = 5): Promise<Question[]> {
    const response = await fetch(`${API_BASE_URL}/sub_topics/${subTopicId}/questions?limit=${limit}`);
    if (!response.ok) throw new Error('Failed to fetch questions');
    return response.json();
  },

  async getRandomQuestions(limit: number = 5): Promise<Question[]> {
    const response = await fetch(`${API_BASE_URL}/questions/random?limit=${limit}`);
    if (!response.ok) throw new Error('Failed to fetch random questions');
    return response.json();
  },

  async submitAnswer(data: AnswerRequest): Promise<AnswerResponse> {
    const response = await fetch(`${API_BASE_URL}/answers`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!response.ok) throw new Error('Failed to submit answer');
    return response.json();
  },

  async getStreak(): Promise<StreakResponse> {
    const response = await fetch(`${API_BASE_URL}/streak`);
    if (!response.ok) throw new Error('Failed to fetch streak');
    return response.json();
  },

  async generateFromLink(params: { url: string; size: 'small' | 'large'; topic?: string; sub_topic?: string }): Promise<{status:string;created:number;requested:number;topic:string}> {
    const body = new URLSearchParams();
    body.append('url', params.url);
    body.append('size', params.size);
    if (params.topic) body.append('topic', params.topic);
    if (params.sub_topic) body.append('sub_topic', params.sub_topic);

    const response = await fetch(`${API_BASE_URL}/generate/from-link`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body,
    });
    if (!response.ok) throw new Error('Failed to generate from link');
    return response.json();
  },

  async generateFromPdf(params: { file: File; size: 'small' | 'large'; topic?: string; sub_topic?: string }): Promise<{status:string;created:number;requested:number;topic:string}> {
    const form = new FormData();
    form.append('pdf', params.file);
    form.append('size', params.size);
    if (params.topic) form.append('topic', params.topic);
    if (params.sub_topic) form.append('sub_topic', params.sub_topic);

    const response = await fetch(`${API_BASE_URL}/generate/from-pdf`, {
      method: 'POST',
      body: form,
    });
    if (!response.ok) throw new Error('Failed to generate from pdf');
    return response.json();
  },
};

