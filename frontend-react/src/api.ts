import axios from 'axios';
import type { QueryResult, ExampleCategory } from './types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const executeQuery = async (question: string): Promise<QueryResult> => {
  const response = await api.post<QueryResult>('/api/query', { question });
  return response.data;
};

export const getExampleQuestions = async (): Promise<ExampleCategory> => {
  const response = await api.get<{ categories: ExampleCategory }>('/api/examples');
  return response.data.categories;
};

export const exportConversation = async (messages: any[], mode: string = 'seller') => {
  const response = await api.post('/api/conversation/export', { messages, mode });
  return response.data;
};

export const getStatistics = async () => {
  const response = await api.get('/api/stats');
  return response.data;
};
