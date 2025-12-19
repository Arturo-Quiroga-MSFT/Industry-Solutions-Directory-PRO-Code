export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  data?: QueryResult;
}

export interface QueryResult {
  success: boolean;
  question: string;
  intent?: {
    intent: string;
    needs_new_query: boolean;
    query_type: string;
    reasoning: string;
  };
  narrative?: string;  // New: formatted insights text
  insights?: {
    overview: string;
    key_findings: string[];
    patterns: string[];
    statistics: Record<string, any>;
    recommendations: string[];
    follow_up_questions?: string[];  // New: clickable follow-up questions
  };
  sql?: string;
  explanation?: string;
  confidence?: string;
  columns?: string[];
  rows?: Record<string, any>[];
  row_count: number;
  error?: string;
  timestamp: string;
}

export interface ExampleCategory {
  [category: string]: string[];
}
