export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  data?: QueryResult;
}

export interface Citation {
  id: number;
  solution_name?: string;
  partner_name?: string;
  source_row_index: number;
  supports: string;
  row_data?: Record<string, any>;
}

export interface WebSource {
  title: string;
  url: string;
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
  needs_clarification?: boolean;  // New: indicates query is ambiguous
  clarification_question?: string;  // New: question to ask user
  suggested_refinements?: string[];  // New: suggested more specific queries
  narrative?: string;  // New: formatted insights text
  insights?: {
    overview: string;
    key_findings: string[];
    patterns: string[];
    statistics: Record<string, any>;
    recommendations: string[];
    follow_up_questions?: string[];  // New: clickable follow-up questions
    citations?: Citation[];  // New: source citations for insights
  };
  sql?: string;
  explanation?: string;
  confidence?: string;
  columns?: string[];
  rows?: Record<string, any>[];
  row_count: number;
  web_sources?: WebSource[];  // Web search sources from Agent 4
  error?: string;
  usage_stats?: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
  };
  elapsed_time?: number;  // Time in seconds
  timestamp: string;
}

export interface ExampleCategory {
  [category: string]: string[];
}


