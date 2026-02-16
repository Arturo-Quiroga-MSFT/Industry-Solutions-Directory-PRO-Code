import type { ChatMessage } from '../types';
import { User, Bot, Database, CheckCircle, XCircle, BarChart3, Table2, Lightbulb, BookOpen, ExternalLink, Globe } from 'lucide-react';
import DataTable from './DataTable';
import ChartViewer from './ChartViewer';
import { useState } from 'react';
import ReactMarkdown from 'react-markdown';

// SQL formatter for better readability
function formatSQL(sql: string): string {
  if (!sql) return '';
  
  let formatted = sql;
  
  // Add line breaks before major keywords (order matters - do longer phrases first)
  formatted = formatted.replace(/\s+(ORDER BY)\s+/gi, '\n$1 ');
  formatted = formatted.replace(/\s+(GROUP BY)\s+/gi, '\n$1 ');
  formatted = formatted.replace(/\s+(LEFT JOIN)\s+/gi, '\n$1 ');
  formatted = formatted.replace(/\s+(INNER JOIN)\s+/gi, '\n$1 ');
  formatted = formatted.replace(/\s+(FROM)\s+/gi, '\n$1 ');
  formatted = formatted.replace(/\s+(WHERE)\s+/gi, '\n$1 ');
  formatted = formatted.replace(/\s+(HAVING)\s+/gi, '\n$1 ');
  
  // Add indentation for AND/OR
  formatted = formatted.replace(/\s+(AND)\s+/gi, '\n  $1 ');
  formatted = formatted.replace(/\s+(OR)\s+/gi, '\n  $1 ');
  
  return formatted.trim();
}

interface MessageProps {
  message: ChatMessage;
  onFollowUpClick?: (question: string) => void;
}

export default function Message({ message, onFollowUpClick }: MessageProps) {
  const [activeTab, setActiveTab] = useState<'insights' | 'table' | 'chart' | 'sql'>('insights');

  if (message.role === 'user') {
    return (
      <div className="flex gap-3 message-slide-in">
        <div className="flex-shrink-0">
          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center">
            <User size={18} className="text-white" />
          </div>
        </div>
        <div className="flex-1">
          <div className="bg-gradient-to-r from-purple-600 to-pink-600 rounded-lg p-4 text-white">
            <p className="font-medium">{message.content}</p>
          </div>
          <p className="text-xs text-gray-500 mt-1">
            {new Date(message.timestamp).toLocaleTimeString()}
          </p>
        </div>
      </div>
    );
  }

  // Assistant message
  const { data } = message;

  return (
    <div className="flex gap-3 message-slide-in">
      <div className="flex-shrink-0">
        <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-cyan-500 flex items-center justify-center">
          <Bot size={18} className="text-white" />
        </div>
      </div>
      <div className="flex-1">
        <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
          {data?.error ? (
            <div className="flex items-start gap-2 text-red-400">
              <XCircle size={20} className="flex-shrink-0 mt-0.5" />
              <div>
                <p className="font-medium">Error</p>
                <p className="text-sm mt-1">{data.error}</p>
              </div>
            </div>
          ) : data?.needs_clarification ? (
            <div className="flex items-start gap-2 text-yellow-400">
              <Lightbulb size={20} className="flex-shrink-0 mt-0.5" />
              <div className="flex-1">
                <p className="font-medium mb-2">Could you be more specific?</p>
                <p className="text-gray-300 text-sm mb-4">{data.clarification_question}</p>
                
                {data.suggested_refinements && data.suggested_refinements.length > 0 && (
                  <div>
                    <p className="text-sm text-gray-400 mb-2">Try asking:</p>
                    <div className="flex flex-wrap gap-2">
                      {data.suggested_refinements.map((refinement, idx) => (
                        <button
                          key={idx}
                          onClick={() => {
                            if (onFollowUpClick) {
                              onFollowUpClick(refinement);
                            }
                          }}
                          className="px-3 py-2 bg-yellow-900/30 hover:bg-yellow-800/50 text-yellow-300 rounded-lg text-sm border border-yellow-700/50 hover:border-yellow-500 transition-all"
                        >
                          {refinement}
                        </button>
                      ))}
                    </div>
                  </div>
                )}
                
                {data.explanation && (
                  <div className="mt-4 pt-4 border-t border-slate-700">
                    <p className="text-xs text-gray-400">
                      <strong>Note:</strong> {data.explanation}
                    </p>
                  </div>
                )}
              </div>
            </div>
          ) : (
            <>
              <div className="flex items-center gap-2 text-green-400 mb-3">
                <CheckCircle size={20} />
                <span className="font-medium">Found {data?.row_count || 0} results</span>
                {data?.confidence && (
                  <span className={`ml-auto px-2 py-1 rounded text-xs ${
                    data.confidence === 'high' ? 'bg-green-900 text-green-200' :
                    data.confidence === 'medium' ? 'bg-yellow-900 text-yellow-200' :
                    'bg-red-900 text-red-200'
                  }`}>
                    {data.confidence.toUpperCase()}
                  </span>
                )}
              </div>

              {data?.explanation && (
                <p className="text-gray-300 text-sm mb-4">{data.explanation}</p>
              )}

              {data && data.row_count > 0 && data.rows && data.columns && (
                <div className="mt-4">
                  {/* Tabs */}
                  <div className="flex gap-2 mb-4 border-b border-slate-700">
                    {data.narrative && (
                      <button
                        onClick={() => setActiveTab('insights')}
                        className={`flex items-center gap-2 px-4 py-2 border-b-2 transition-colors ${
                          activeTab === 'insights'
                            ? 'border-blue-500 text-blue-400'
                            : 'border-transparent text-gray-400 hover:text-gray-300'
                        }`}
                      >
                        <Lightbulb size={16} />
                        Insights
                      </button>
                    )}
                    <button
                      onClick={() => setActiveTab('table')}
                      className={`flex items-center gap-2 px-4 py-2 border-b-2 transition-colors ${
                        activeTab === 'table'
                          ? 'border-blue-500 text-blue-400'
                          : 'border-transparent text-gray-400 hover:text-gray-300'
                      }`}
                    >
                      <Table2 size={16} />
                      Table
                    </button>
                    <button
                      onClick={() => setActiveTab('chart')}
                      className={`flex items-center gap-2 px-4 py-2 border-b-2 transition-colors ${
                        activeTab === 'chart'
                          ? 'border-blue-500 text-blue-400'
                          : 'border-transparent text-gray-400 hover:text-gray-300'
                      }`}
                    >
                      <BarChart3 size={16} />
                      Charts
                    </button>
                    <button
                      onClick={() => setActiveTab('sql')}
                      className={`flex items-center gap-2 px-4 py-2 border-b-2 transition-colors ${
                        activeTab === 'sql'
                          ? 'border-blue-500 text-blue-400'
                          : 'border-transparent text-gray-400 hover:text-gray-300'
                      }`}
                    >
                      <Database size={16} />
                      SQL
                    </button>
                  </div>

                  {/* Tab Content */}
                  {activeTab === 'insights' && data.narrative && (
                    <div>
                      <div className="prose prose-invert max-w-none mb-6">
                        <ReactMarkdown>{data.narrative}</ReactMarkdown>
                      </div>
                      
                      {/* Follow-up Questions */}
                      {data.insights?.follow_up_questions && data.insights.follow_up_questions.length > 0 && (
                        <div className="mt-6 pt-4 border-t border-slate-700">
                          <p className="text-sm text-gray-400 mb-3 font-medium">💡 Explore Further:</p>
                          <div className="flex flex-wrap gap-2">
                            {data.insights.follow_up_questions.map((question, idx) => (
                              <button
                                key={idx}
                                onClick={() => {
                                  if (onFollowUpClick) {
                                    onFollowUpClick(question);
                                  }
                                }}
                                className="px-3 py-2 bg-blue-900/30 hover:bg-blue-800/50 text-blue-300 rounded-lg text-sm border border-blue-700/50 hover:border-blue-500 transition-all flex items-center gap-2"
                              >
                                <span>→</span>
                                {question}
                              </button>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Citations - Copilot Style */}
                      {data.insights?.citations && data.insights.citations.length > 0 && (
                        <div className="mt-6 pt-4 border-t border-slate-700">
                          <p className="text-sm text-gray-400 mb-3 font-medium flex items-center gap-2">
                            <BookOpen size={16} />
                            📚 Sources & References
                          </p>
                          <div className="space-y-2">
                            {data.insights.citations.map((citation, idx) => (
                              <div 
                                key={idx}
                                className="p-3 bg-slate-900/50 rounded-lg border border-slate-700/50 hover:border-slate-600 transition-colors"
                              >
                                <div className="flex items-start gap-2">
                                  <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-blue-900/30 border border-blue-700/50 rounded text-xs text-blue-300 font-mono flex-shrink-0">
                                    [{citation.id}]
                                  </span>
                                  <div className="flex-1 min-w-0">
                                    <p className="text-gray-300 text-sm">
                                      {citation.solution_name && (
                                        <strong className="text-blue-300">{citation.solution_name}</strong>
                                      )}
                                      {citation.partner_name && (
                                        <span className="text-gray-400"> by {citation.partner_name}</span>
                                      )}
                                    </p>
                                    {citation.supports && (
                                      <p className="text-xs text-gray-500 mt-1">
                                        Supports: "{citation.supports}"
                                      </p>
                                    )}
                                    <button
                                      onClick={() => {
                                        setActiveTab('table');
                                        // Optionally: implement scrolling to specific row
                                      }}
                                      className="inline-flex items-center gap-1 text-xs text-blue-400 hover:text-blue-300 mt-2 hover:underline"
                                    >
                                      <ExternalLink size={12} />
                                      View in table (Row {citation.source_row_index + 1})
                                    </button>
                                  </div>
                                </div>
                              </div>
                            ))}
                          </div>
                          <p className="text-xs text-gray-500 mt-3 italic">
                            💡 Click citation numbers or solution names to see source data in the table
                          </p>
                        </div>
                      )}

                      {/* Web Sources - from web_search enrichment */}
                      {data.web_sources && data.web_sources.length > 0 && (
                        <div className="mt-6 p-4 rounded-xl bg-gradient-to-r from-blue-950/60 to-cyan-950/40 border border-blue-500/30 shadow-lg shadow-blue-500/5">
                          <div className="flex items-center gap-2 mb-3">
                            <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-blue-500/20">
                              <Globe size={18} className="text-blue-400" />
                            </div>
                            <h4 className="text-sm font-semibold text-blue-300 tracking-wide uppercase">
                              Web Sources ({data.web_sources.length})
                            </h4>
                          </div>
                          <div className="grid gap-2 sm:grid-cols-2">
                            {data.web_sources.map((source, idx) => (
                              <a
                                key={idx}
                                href={source.url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="flex items-start gap-2.5 px-3.5 py-2.5 rounded-lg bg-slate-800/70 border border-slate-600/40 hover:border-blue-400/60 hover:bg-slate-700/70 transition-all group"
                              >
                                <ExternalLink size={14} className="text-blue-400 mt-0.5 shrink-0 group-hover:text-blue-300" />
                                <span className="text-sm text-gray-200 group-hover:text-white leading-snug line-clamp-2">{source.title}</span>
                              </a>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  )}

                  {activeTab === 'table' && (
                    <DataTable data={data.rows} columns={data.columns} />
                  )}

                  {activeTab === 'chart' && (
                    <ChartViewer data={data.rows} columns={data.columns} />
                  )}

                  {activeTab === 'sql' && data.sql && (
                    <div className="bg-slate-900 rounded-lg p-4 border border-slate-700">
                      <pre className="text-sm text-gray-300 overflow-x-auto whitespace-pre-wrap break-words">
                        <code>{formatSQL(data.sql)}</code>
                      </pre>
                    </div>
                  )}
                </div>
              )}
            </>
          )}
        </div>
        <div className="flex items-center gap-4 text-xs text-gray-500 mt-1">
          <span>{new Date(message.timestamp).toLocaleTimeString()}</span>
          {data?.usage_stats && (
            <span className="flex items-center gap-3 text-gray-400">
              <span>📊 {data.usage_stats.prompt_tokens.toLocaleString()} in</span>
              <span>📤 {data.usage_stats.completion_tokens.toLocaleString()} out</span>
              <span>∑ {data.usage_stats.total_tokens.toLocaleString()} tokens</span>
            </span>
          )}
          {data?.elapsed_time && (
            <span className="text-gray-400">⏱️ {data.elapsed_time}s</span>
          )}
        </div>
      </div>
    </div>
  );
}
