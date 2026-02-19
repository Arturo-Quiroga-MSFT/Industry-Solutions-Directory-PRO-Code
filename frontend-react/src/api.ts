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

export interface StreamCallbacks {
  onStatus: (phase: string, message: string) => void;
  onMetadata: (data: Record<string, any>) => void;
  onDelta: (content: string) => void;
  onDone: (data: { web_sources?: any[]; usage_stats?: any; elapsed_time?: number }) => void;
  onError: (error: string) => void;
}

export const executeQueryStream = async (
  question: string,
  callbacks: StreamCallbacks
): Promise<void> => {
  const response = await fetch(`${API_BASE_URL}/api/query/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question }),
  });

  if (!response.ok || !response.body) {
    callbacks.onError(`HTTP error ${response.status}`);
    return;
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });

    // Process complete SSE lines
    const lines = buffer.split('\n');
    buffer = lines.pop() || ''; // Keep incomplete line in buffer

    for (const line of lines) {
      const trimmed = line.trim();
      if (!trimmed.startsWith('data: ')) continue;

      try {
        const event = JSON.parse(trimmed.slice(6));

        switch (event.type) {
          case 'status':
            callbacks.onStatus(event.phase, event.message);
            break;
          case 'metadata':
            callbacks.onMetadata(event);
            break;
          case 'delta':
            callbacks.onDelta(event.content);
            break;
          case 'done':
            callbacks.onDone(event);
            break;
        }
      } catch {
        // Skip malformed SSE lines
      }
    }
  }
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
