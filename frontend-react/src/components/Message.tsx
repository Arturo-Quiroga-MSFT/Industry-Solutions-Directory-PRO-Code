import type { ChatMessage } from '../types';
import { User, Bot, Database, CheckCircle, XCircle, BarChart3, Table2, Lightbulb } from 'lucide-react';
import DataTable from './DataTable';
import ChartViewer from './ChartViewer';
import { useState } from 'react';
import ReactMarkdown from 'react-markdown';

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
                      <pre className="text-sm text-gray-300 overflow-x-auto">
                        <code>{data.sql}</code>
                      </pre>
                    </div>
                  )}
                </div>
              )}
            </>
          )}
        </div>
        <p className="text-xs text-gray-500 mt-1">
          {new Date(message.timestamp).toLocaleTimeString()}
        </p>
      </div>
    </div>
  );
}
