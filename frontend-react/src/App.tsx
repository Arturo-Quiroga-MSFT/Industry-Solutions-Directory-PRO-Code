import { useState, useRef, useEffect, useCallback } from 'react';
import { Send, Loader2, Download, Trash2, Database, Shield, MessageSquare } from 'lucide-react';
import Message from './components/Message';
import type { ChatMessage, ExampleCategory, QueryResult } from './types';
import { executeQueryStream, getExampleQuestions, exportConversation } from './api';
import './App.css';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

function App() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [streamingStatus, setStreamingStatus] = useState<string>('');
  const [examples, setExamples] = useState<ExampleCategory>({});
  const [selectedCategory, setSelectedCategory] = useState<string>('');
  const [appMode, setAppMode] = useState<string>('seller');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Load example questions
    getExampleQuestions().then(setExamples).catch(console.error);
    
    // Check URL query param first (?mode=seller or ?mode=customer), then fall back to backend
    const urlParams = new URLSearchParams(window.location.search);
    const urlMode = urlParams.get('mode');
    if (urlMode === 'seller' || urlMode === 'customer') {
      setAppMode(urlMode);
    } else {
      fetch(`${API_BASE_URL}/api/health`)
        .then(res => res.json())
        .then(data => setAppMode(data.mode || 'seller'))
        .catch(console.error);
    }
  }, []);

  useEffect(() => {
    // Auto-scroll to bottom when new messages arrive
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSubmit = useCallback(async (question: string) => {
    if (!question.trim() || isLoading) return;

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: question,
      timestamp: new Date().toISOString(),
    };

    const assistantId = (Date.now() + 1).toString();

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);
    setStreamingStatus('Connecting...');

    // Create the initial assistant message placeholder
    const initialAssistantMessage: ChatMessage = {
      id: assistantId,
      role: 'assistant',
      content: '',
      timestamp: new Date().toISOString(),
      isStreaming: true,
    };
    setMessages(prev => [...prev, initialAssistantMessage]);

    // Accumulate narrative text for final data
    let narrativeAccumulator = '';
    let metadataResult: Partial<QueryResult> = {};

    try {
      await executeQueryStream(question, {
        onStatus: (phase, message) => {
          setStreamingStatus(message);
          // Update assistant message with phase info
          setMessages(prev => prev.map(m =>
            m.id === assistantId ? { ...m, content: message, streamingPhase: phase } : m
          ));
        },
        onMetadata: (event) => {
          if (!event.success) {
            setMessages(prev => prev.map(m =>
              m.id === assistantId ? {
                ...m,
                content: `Error: ${event.error}`,
                isStreaming: false,
                data: {
                  success: false,
                  question,
                  error: event.error as string,
                  row_count: 0,
                  timestamp: new Date().toISOString(),
                },
              } : m
            ));
            setIsLoading(false);
            setStreamingStatus('');
            return;
          }
          // Store metadata and show table/data immediately
          metadataResult = {
            success: true,
            question,
            intent: event.intent,
            sql: event.sql as string | undefined,
            explanation: event.explanation as string | undefined,
            confidence: event.confidence as string | undefined,
            insights: event.insights as QueryResult['insights'],
            columns: event.data?.columns,
            rows: event.data?.rows,
            row_count: event.row_count ?? event.data?.rows?.length ?? 0,
            needs_clarification: event.needs_clarification,
            clarification_question: event.clarification_question,
            suggested_refinements: event.suggested_refinements,
            timestamp: event.timestamp || new Date().toISOString(),
          };
          setStreamingStatus('Writing response...');
          const rowCount = metadataResult.row_count ?? 0;
          setMessages(prev => prev.map(m =>
            m.id === assistantId ? {
              ...m,
              content: metadataResult.needs_clarification
                ? 'I need clarification to provide the best results'
                : `Found ${rowCount} results`,
              data: metadataResult as QueryResult,
              isStreaming: true,
              streamingPhase: 'writing',
            } : m
          ));
        },
        onDelta: (content) => {
          narrativeAccumulator += content;
          setMessages(prev => prev.map(m =>
            m.id === assistantId ? {
              ...m,
              data: {
                ...m.data!,
                narrative: narrativeAccumulator,
              },
            } : m
          ));
        },
        onDone: (doneData) => {
          setMessages(prev => prev.map(m =>
            m.id === assistantId ? {
              ...m,
              isStreaming: false,
              streamingPhase: undefined,
              data: {
                ...m.data!,
                narrative: narrativeAccumulator,
                web_sources: doneData.web_sources,
                usage_stats: doneData.usage_stats,
                elapsed_time: doneData.elapsed_time,
              },
            } : m
          ));
          setIsLoading(false);
          setStreamingStatus('');
        },
        onError: (error) => {
          setMessages(prev => prev.map(m =>
            m.id === assistantId ? {
              ...m,
              content: `Error: ${error}`,
              isStreaming: false,
              data: {
                success: false,
                question,
                error,
                row_count: 0,
                timestamp: new Date().toISOString(),
              },
            } : m
          ));
          setIsLoading(false);
          setStreamingStatus('');
        },
      });

      // If stream ended without a done event, finalize
      setIsLoading(false);
      setStreamingStatus('');
      setMessages(prev => prev.map(m =>
        m.id === assistantId && m.isStreaming ? { ...m, isStreaming: false } : m
      ));
    } catch (error) {
      setMessages(prev => prev.map(m =>
        m.id === assistantId ? {
          ...m,
          content: `Error: ${error instanceof Error ? error.message : 'Unknown error'}`,
          isStreaming: false,
          data: {
            success: false,
            question,
            error: error instanceof Error ? error.message : 'Unknown error',
            row_count: 0,
            timestamp: new Date().toISOString(),
          },
        } : m
      ));
      setIsLoading(false);
      setStreamingStatus('');
    }
  }, [isLoading]);

  const handleExampleClick = (question: string) => {
    handleSubmit(question);
  };

  const handleExportJSON = async () => {
    try {
      const exportData = await exportConversation(messages, appMode);
      const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `conversation_${appMode}_${new Date().toISOString()}.json`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Export failed:', error);
    }
  };

  const handleExportMarkdown = () => {
    const modeLabel = appMode === 'seller' ? 'Seller' : 'Customer';
    let markdown = `# Microsoft Solutions Directory — AI Explorer (${modeLabel} Mode)\n\n`;
    markdown += `**Date**: ${new Date().toLocaleString()}\n`;
    markdown += `**Mode**: ${modeLabel}\n`;
    markdown += `**Total Queries**: ${messages.filter(m => m.role === 'user').length}\n\n---\n\n`;

    messages.forEach((msg, idx) => {
      if (msg.role === 'user') {
        markdown += `## Query ${Math.floor(idx / 2) + 1}\n\n`;
        markdown += `**Question**: ${msg.content}\n\n`;
      } else {
        markdown += `**Result**: ${msg.content}\n\n`;
        
        // Add Insights section
        if (msg.data?.narrative) {
          markdown += `### 💡 Insights\n\n`;
          markdown += `${msg.data.narrative}\n\n`;
        }
        
        // Add Follow-up Questions
        if (msg.data?.insights?.follow_up_questions && msg.data.insights.follow_up_questions.length > 0) {
          markdown += `**Suggested Follow-up Questions:**\n\n`;
          msg.data.insights.follow_up_questions.forEach((q) => {
            markdown += `- ${q}\n`;
          });
          markdown += `\n`;
        }
        
        // Add Table Data
        if (msg.data?.rows && msg.data?.columns && msg.data.rows.length > 0) {
          markdown += `### 📊 Results Table\n\n`;
          markdown += `**Total Results**: ${msg.data.rows.length}\n\n`;
          
          // Prioritize important columns including seller-focused fields
          const priorityColumns = [
            'solutionName', 
            'orgName', 
            'industryName', 
            'solutionAreaName',
            'marketPlaceLink',
            'solutionOrgWebsite',
            'geoName',
            'solutionPlayName'
          ];
          const selectedColumns: string[] = [];
          
          // Add priority columns that exist
          priorityColumns.forEach(col => {
            if (msg.data?.columns?.includes(col)) {
              selectedColumns.push(col);
            }
          });
          
          // Add other columns (excluding description) until we have space
          msg.data?.columns?.forEach((col: string) => {
            if (!selectedColumns.includes(col) && 
                col !== 'solutionDescription' && 
                selectedColumns.length < 10) {
              selectedColumns.push(col);
            }
          });
          
          // Always add solutionDescription last if it exists
          if (msg.data.columns.includes('solutionDescription')) {
            selectedColumns.push('solutionDescription');
          }
          
          // Use all selected columns (increased from 5 to accommodate seller fields)
          const cols = selectedColumns;
          
          markdown += `| ${cols.join(' | ')} |\n`;
          markdown += `| ${cols.map(() => '---').join(' | ')} |\n`;
          
          // Add rows (limit to first 20 for export)
          const rowsToExport = msg.data.rows.slice(0, 20);
          rowsToExport.forEach((row: any) => {
            const rowData = cols.map(col => {
              const value = row[col];
              if (value === null || value === undefined) return '';
              // Strip HTML and truncate
              const strValue = String(value).replace(/<[^>]*>/g, '').substring(0, 100);
              return strValue.replace(/\|/g, '\\|').replace(/\n/g, ' ');
            });
            markdown += `| ${rowData.join(' | ')} |\n`;
          });
          
          if (msg.data.rows.length > 20) {
            markdown += `\n*... and ${msg.data.rows.length - 20} more results*\n`;
          }
          markdown += `\n`;
        }
        
        if (msg.data?.sql) {
          markdown += `**SQL**:\n\`\`\`sql\n${msg.data.sql}\n\`\`\`\n\n`;
        }
        if (msg.data?.explanation) {
          markdown += `**Explanation**: ${msg.data.explanation}\n\n`;
        }
        markdown += `---\n\n`;
      }
    });

    const blob = new Blob([markdown], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `conversation_${appMode}_${new Date().toISOString()}.md`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleExportHTML = () => {
    let html = `<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>ISD Conversation Export</title>
  <style>
    body { font-family: system-ui, -apple-system, sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; background: #0f172a; color: #e2e8f0; }
    h1 { color: #3b82f6; }
    .message { margin: 20px 0; padding: 15px; border-radius: 8px; }
    .user { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
    .assistant { background: #1e293b; border-left: 4px solid #3b82f6; }
    .sql { background: #1e1e1e; padding: 10px; border-radius: 4px; overflow-x: auto; }
    .meta { font-size: 0.9em; color: #94a3b8; margin-top: 10px; }
    table { border-collapse: collapse; width: 100%; margin: 10px 0; }
    th, td { border: 1px solid #475569; padding: 8px; text-align: left; }
    th { background: #334155; }
  </style>
</head>
<body>
  <h1>🔍 Microsoft Solutions Directory — AI Explorer (${appMode === 'seller' ? 'Seller' : 'Customer'} Mode)</h1>
  <p><strong>Date:</strong> ${new Date().toLocaleString()}</p>
  <p><strong>Mode:</strong> ${appMode === 'seller' ? 'Seller' : 'Customer'}</p>
  <p><strong>Total Queries:</strong> ${messages.filter(m => m.role === 'user').length}</p>
  <hr>
`;

    messages.forEach((msg) => {
      if (msg.role === 'user') {
        html += `<div class="message user"><strong>You:</strong> ${msg.content}</div>\n`;
      } else {
        html += `<div class="message assistant">
          <strong>Assistant:</strong> ${msg.content}<br>`;
        
        // Add Insights section
        if (msg.data?.narrative) {
          html += `<div style="margin-top: 15px; padding: 15px; background: #0f172a; border-left: 4px solid #3b82f6; border-radius: 4px;">
            <h3 style="color: #3b82f6; margin-top: 0;">💡 Insights</h3>
            <div style="color: #e2e8f0;">${msg.data.narrative.replace(/\n/g, '<br>')}</div>
          </div>`;
        }
        
        // Add Follow-up Questions
        if (msg.data?.insights?.follow_up_questions && msg.data.insights.follow_up_questions.length > 0) {
          html += `<div style="margin-top: 15px;">
            <p style="color: #94a3b8; font-size: 0.9em;"><strong>Suggested Follow-up Questions:</strong></p>
            <ul style="color: #cbd5e1;">`;
          msg.data.insights.follow_up_questions.forEach((q) => {
            html += `<li>${q}</li>`;
          });
          html += `</ul></div>`;
        }
        
        // Add Table Data
        if (msg.data?.rows && msg.data?.columns && msg.data.rows.length > 0) {
          html += `<div style="margin-top: 15px;">
            <h3 style="color: #3b82f6;">📊 Results Table</h3>
            <p style="color: #94a3b8; font-size: 0.9em;">Total Results: ${msg.data.rows.length}</p>
            <table>
              <thead>
                <tr>`;
          
          // Prioritize important columns including seller-focused fields
          const priorityColumns = [
            'solutionName', 
            'orgName', 
            'industryName', 
            'solutionAreaName',
            'marketPlaceLink',
            'solutionOrgWebsite',
            'geoName',
            'solutionPlayName'
          ];
          const selectedColumns: string[] = [];
          
          // Add priority columns that exist
          priorityColumns.forEach(col => {
            if (msg.data?.columns?.includes(col)) {
              selectedColumns.push(col);
            }
          });
          
          // Add other columns (excluding description) until we have space
          msg.data?.columns?.forEach((col: string) => {
            if (!selectedColumns.includes(col) && 
                col !== 'solutionDescription' && 
                selectedColumns.length < 10) {
              selectedColumns.push(col);
            }
          });
          
          // Always add solutionDescription last if it exists
          if (msg.data.columns.includes('solutionDescription')) {
            selectedColumns.push('solutionDescription');
          }
          
          // Use all selected columns (increased to accommodate seller fields)
          const cols = selectedColumns;
          
          cols.forEach((col: string) => {
            html += `<th>${col}</th>`;
          });
          html += `</tr></thead><tbody>`;
          
          // Add rows (limit to first 20)
          const rowsToExport = msg.data.rows.slice(0, 20);
          rowsToExport.forEach((row: any) => {
            html += `<tr>`;
            cols.forEach((col: string) => {
              const value = row[col];
              if (value === null || value === undefined) {
                html += `<td></td>`;
              } else {
                // For link columns, create clickable links
                const isLink = col.toLowerCase().includes('link') || col.toLowerCase().includes('website');
                if (isLink && String(value).startsWith('http')) {
                  const linkText = col.includes('marketplace') ? '🔗 View' :
                                  col.includes('website') ? '🌐 Visit' :
                                  col.includes('offer') ? '💰 Offer' : '🔗 Link';
                  html += `<td><a href="${value}" target="_blank" style="color: #3b82f6;">${linkText}</a></td>`;
                } else {
                  // Strip HTML and truncate
                  const strValue = String(value).replace(/<[^>]*>/g, '').substring(0, 100);
                  html += `<td>${strValue}</td>`;
                }
              }
            });
            html += `</tr>`;
          });
          
          html += `</tbody></table>`;
          
          if (msg.data.rows.length > 20) {
            html += `<p style="color: #94a3b8; font-size: 0.9em; font-style: italic;">... and ${msg.data.rows.length - 20} more results</p>`;
          }
          html += `</div>`;
        }
        
        if (msg.data?.sql) {
          html += `<div class="sql"><pre>${msg.data.sql}</pre></div>`;
        }
        if (msg.data?.explanation) {
          html += `<p><strong>Explanation:</strong> ${msg.data.explanation}</p>`;
        }
        html += `<div class="meta">${new Date(msg.timestamp).toLocaleString()}</div>
        </div>\n`;
      }
    });

    html += `</body></html>`;

    const blob = new Blob([html], { type: 'text/html' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `conversation_${appMode}_${new Date().toISOString()}.html`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleClear = () => {
    if (confirm('Clear all messages?')) {
      setMessages([]);
    }
  };

  return (
    <div className="h-screen flex flex-col bg-slate-900">
      {/* Header */}
      <header className="relative bg-gradient-to-r from-blue-600 to-cyan-600 text-white shadow-lg overflow-hidden">
        {/* Background Images */}
        <div className="absolute inset-0 opacity-20 flex">
          <div className="w-1/2 bg-cover bg-center" style={{backgroundImage: 'url(https://solutions.microsoftindustryinsights.com/assets/images/ISD_Homepage_1005x395.jpg)'}}></div>
          <div className="w-1/2 bg-cover bg-center" style={{backgroundImage: 'url(https://solutions.microsoftindustryinsights.com/assets/images/technology_banner.jpg)'}}></div>
        </div>
        
        {/* Content */}
        <div className="relative z-10 max-w-7xl mx-auto p-6">
          <div className="flex items-center justify-between mb-2">
            <h1 className="text-3xl font-bold">🔍 Microsoft Solutions Directory — AI Explorer</h1>
            {appMode === 'customer' && (
              <div className="bg-green-500/20 text-green-200 px-4 py-2 rounded-lg flex items-center gap-2 border border-green-500/30">
                <Shield size={16} />
                <span className="font-semibold">FOR CUSTOMERS & PARTNERS</span>
              </div>
            )}
            {appMode === 'seller' && (
              <div className="bg-blue-500/20 text-blue-200 px-4 py-2 rounded-lg flex items-center gap-2 border border-blue-500/30">
                <Database size={16} />
                <span className="font-semibold">FOR MICROSOFT SELLERS</span>
              </div>
            )}
          </div>
          <p className="text-blue-100">
            {appMode === 'seller'
              ? 'Discover partner solutions, customer stories, and industry insights using natural language'
              : 'Find technology solutions from Microsoft partners tailored to your industry and business needs'}
          </p>
          <div className="flex gap-4 mt-4 text-sm">
            <div className="flex items-center gap-2">
              <Shield size={16} />
              <span>🔒 Read-Only</span>
            </div>
            <div className="flex items-center gap-2">
              <MessageSquare size={16} />
              <span>💬 Ask in natural language</span>
            </div>
          </div>
        </div>
      </header>

      <div className="flex-1 flex overflow-hidden">
        {/* Sidebar */}
        <aside className="w-80 bg-slate-800 border-r border-slate-700 overflow-y-auto">
          <div className="p-4">
            <h2 className="text-white font-semibold mb-4">💡 Example Questions</h2>

            {Object.keys(examples).length > 0 && (
              <select
                value={selectedCategory}
                onChange={(e) => setSelectedCategory(e.target.value)}
                className="w-full bg-slate-700 text-white rounded px-3 py-2 mb-4 border border-slate-600 focus:outline-none focus:border-blue-500"
              >
                <option value="">Select Category</option>
                {Object.keys(examples).map((category) => (
                  <option key={category} value={category}>
                    {category}
                  </option>
                ))}
              </select>
            )}

            {selectedCategory && examples[selectedCategory] && (
              <div className="space-y-2">
                {examples[selectedCategory].map((question, idx) => (
                  <button
                    key={idx}
                    onClick={() => handleExampleClick(question)}
                    disabled={isLoading}
                    className="w-full text-left text-sm text-gray-300 hover:text-white hover:bg-slate-700 p-3 rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {question}
                  </button>
                ))}
              </div>
            )}

            {messages.length > 0 && (
              <>
                <div className="mt-6 pt-6 border-t border-slate-700">
                  <h3 className="text-white font-semibold mb-3">Export</h3>
                  <div className="space-y-2">
                    <button
                      onClick={handleExportJSON}
                      className="w-full flex items-center gap-2 text-sm text-gray-300 hover:text-white hover:bg-slate-700 p-3 rounded transition-colors"
                    >
                      <Download size={16} />
                      Export as JSON
                    </button>
                    <button
                      onClick={handleExportMarkdown}
                      className="w-full flex items-center gap-2 text-sm text-gray-300 hover:text-white hover:bg-slate-700 p-3 rounded transition-colors"
                    >
                      <Download size={16} />
                      Export as Markdown
                    </button>
                    <button
                      onClick={handleExportHTML}
                      className="w-full flex items-center gap-2 text-sm text-gray-300 hover:text-white hover:bg-slate-700 p-3 rounded transition-colors"
                    >
                      <Download size={16} />
                      Export as HTML
                    </button>
                  </div>
                  <div className="mt-4 pt-4 border-t border-slate-700">
                    <button
                      onClick={handleClear}
                      className="w-full flex items-center gap-2 text-sm text-red-400 hover:text-red-300 hover:bg-red-900/20 p-3 rounded transition-colors"
                    >
                      <Trash2 size={16} />
                      Clear Messages
                    </button>
                  </div>
                </div>
              </>
            )}
          </div>
        </aside>

        {/* Main Chat Area */}
        <main className="flex-1 flex flex-col overflow-hidden">
          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-6">
            <div className="max-w-7xl mx-auto space-y-6">
              {messages.length === 0 ? (
                <div className="text-center text-gray-400 mt-12">
                  <Database size={64} className="mx-auto mb-4 opacity-50" />
                  <h2 className="text-2xl font-semibold mb-2">Start a Conversation</h2>
                  <p>Ask a question about Industry Solutions or select an example from the sidebar</p>
                </div>
              ) : (
                messages.map((message) => (
                  <Message 
                    key={message.id} 
                    message={message}
                    onFollowUpClick={(question) => handleSubmit(question)}
                  />
                ))
              )}
              <div ref={messagesEndRef} />
            </div>
          </div>

          {/* Input Area */}
          <div className="border-t border-slate-700 bg-slate-800 p-4">
            <div className="max-w-7xl mx-auto">
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  handleSubmit(input);
                }}
                className="flex gap-3"
              >
                <input
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  placeholder="Ask a question about Industry Solutions..."
                  disabled={isLoading}
                  className="flex-1 bg-slate-700 text-white rounded-lg px-4 py-3 border border-slate-600 focus:outline-none focus:border-blue-500 disabled:opacity-50"
                />
                <button
                  type="submit"
                  disabled={isLoading || !input.trim()}
                  className="bg-blue-600 hover:bg-blue-700 disabled:bg-slate-600 disabled:cursor-not-allowed text-white rounded-lg px-6 py-3 flex items-center gap-2 transition-colors"
                >
                  {isLoading ? (
                    <>
                      <Loader2 size={20} className="animate-spin" />
                      {streamingStatus || 'Processing...'}
                    </>
                  ) : (
                    <>
                      <Send size={20} />
                      Send
                    </>
                  )}
                </button>
              </form>
            </div>
          </div>
        </main>

      </div>
    </div>
  );
}

export default App;

