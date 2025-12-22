import { useState, useRef, useEffect } from 'react';
import { Send, Loader2, Download, Trash2, Database, Shield } from 'lucide-react';
import Message from './components/Message';
import type { ChatMessage, ExampleCategory } from './types';
import { executeQuery, getExampleQuestions, exportConversation } from './api';
import './App.css';

function App() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [examples, setExamples] = useState<ExampleCategory>({});
  const [selectedCategory, setSelectedCategory] = useState<string>('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Load example questions
    getExampleQuestions().then(setExamples).catch(console.error);
  }, []);

  useEffect(() => {
    // Auto-scroll to bottom when new messages arrive
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSubmit = async (question: string) => {
    if (!question.trim() || isLoading) return;

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: question,
      timestamp: new Date().toISOString(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const result = await executeQuery(question);

      const assistantMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: result.needs_clarification
          ? 'I need clarification to provide the best results'
          : result.success
          ? `Found ${result.row_count} results`
          : `Error: ${result.error}`,
        timestamp: new Date().toISOString(),
        data: result,
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      const errorMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: `Error: ${error instanceof Error ? error.message : 'Unknown error'}`,
        timestamp: new Date().toISOString(),
        data: {
          success: false,
          question,
          error: error instanceof Error ? error.message : 'Unknown error',
          row_count: 0,
          timestamp: new Date().toISOString(),
        },
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleExampleClick = (question: string) => {
    handleSubmit(question);
  };

  const handleExportJSON = async () => {
    try {
      const exportData = await exportConversation(messages);
      const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `conversation_${new Date().toISOString()}.json`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Export failed:', error);
    }
  };

  const handleExportMarkdown = () => {
    let markdown = `# Industry Solutions Directory - Conversation\n\n`;
    markdown += `**Date**: ${new Date().toLocaleString()}\n`;
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
          
          // Prioritize important columns and always include solutionDescription
          const priorityColumns = ['solutionName', 'orgName', 'industryName', 'solutionAreaName'];
          const selectedColumns: string[] = [];
          
          // Add priority columns that exist
          priorityColumns.forEach(col => {
            if (msg.data.columns.includes(col)) {
              selectedColumns.push(col);
            }
          });
          
          // Add other columns until we have 4
          msg.data.columns.forEach((col: string) => {
            if (!selectedColumns.includes(col) && 
                col !== 'solutionDescription' && 
                selectedColumns.length < 4) {
              selectedColumns.push(col);
            }
          });
          
          // Always add solutionDescription last if it exists
          if (msg.data.columns.includes('solutionDescription')) {
            selectedColumns.push('solutionDescription');
          }
          
          // Limit to 5 columns max
          const cols = selectedColumns.slice(0, 5);
          
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
    a.download = `conversation_${new Date().toISOString()}.md`;
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
  <h1>🔍 Industry Solutions Directory - Conversation</h1>
  <p><strong>Date:</strong> ${new Date().toLocaleString()}</p>
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
          
          // Prioritize important columns and always include solutionDescription
          const priorityColumns = ['solutionName', 'orgName', 'industryName', 'solutionAreaName'];
          const selectedColumns: string[] = [];
          
          // Add priority columns that exist
          priorityColumns.forEach(col => {
            if (msg.data.columns.includes(col)) {
              selectedColumns.push(col);
            }
          });
          
          // Add other columns until we have 4
          msg.data.columns.forEach((col: string) => {
            if (!selectedColumns.includes(col) && 
                col !== 'solutionDescription' && 
                selectedColumns.length < 4) {
              selectedColumns.push(col);
            }
          });
          
          // Always add solutionDescription last if it exists
          if (msg.data.columns.includes('solutionDescription')) {
            selectedColumns.push('solutionDescription');
          }
          
          // Limit to 5 columns max
          const cols = selectedColumns.slice(0, 5);
          
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
                // Strip HTML and truncate
                const strValue = String(value).replace(/<[^>]*>/g, '').substring(0, 100);
                html += `<td>${strValue}</td>`;
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
    a.download = `conversation_${new Date().toISOString()}.html`;
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
      <header className="bg-gradient-to-r from-blue-600 to-cyan-600 text-white p-6 shadow-lg">
        <div className="max-w-7xl mx-auto">
          <h1 className="text-3xl font-bold mb-2">🔍 Industry Solutions Directory</h1>
          <p className="text-blue-100">Natural Language to SQL Explorer | Direct Database Access</p>
          <div className="flex gap-4 mt-4 text-sm">
            <div className="flex items-center gap-2">
              <Shield size={16} />
              <span>READ-ONLY Mode</span>
            </div>
            <div className="flex items-center gap-2">
              <Database size={16} />
              <span>5,118 rows</span>
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
            <div className="max-w-4xl mx-auto space-y-6">
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
            <div className="max-w-4xl mx-auto">
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
                      Processing...
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

