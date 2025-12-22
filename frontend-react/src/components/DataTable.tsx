import { useState } from 'react';

interface DataTableProps {
  data: Record<string, any>[];
  columns: string[];
}

interface ExpandedState {
  [key: string]: boolean; // rowIdx-colName: isExpanded
}

export default function DataTable({ data, columns }: DataTableProps) {
  const [expanded, setExpanded] = useState<ExpandedState>({});

  if (!data || data.length === 0 || !columns || columns.length === 0) {
    return <div className="text-gray-400 text-center py-8">No data available</div>;
  }

  // Identify description columns that need text wrapping
  const isDescriptionColumn = (col: string) => {
    const colLower = col.toLowerCase();
    return colLower.includes('description') || colLower.includes('desc');
  };

  // Identify link columns that should be rendered as clickable links
  const isLinkColumn = (col: string) => {
    const colLower = col.toLowerCase();
    return colLower.includes('link') || colLower.includes('url') || colLower.includes('website');
  };

  const toggleExpand = (rowIdx: number, col: string) => {
    const key = `${rowIdx}-${col}`;
    setExpanded(prev => ({ ...prev, [key]: !prev[key] }));
  };

  const renderCell = (value: any, rowIdx: number, col: string) => {
    if (value === null || value === undefined || value === '(Not Set)') {
      return <span className="text-gray-500 italic">(Not Set)</span>;
    }

    const stringValue = String(value);
    
    // Render links as clickable elements
    if (isLinkColumn(col) && stringValue.startsWith('http')) {
      const displayText = col.includes('marketplace') ? '🔗 Marketplace' :
                         col.includes('website') ? '🌐 Website' :
                         col.includes('offer') ? '💰 Special Offer' :
                         col.includes('resource') ? '📄 Resource' :
                         '🔗 Link';
      return (
        <a
          href={stringValue}
          target="_blank"
          rel="noopener noreferrer"
          className="text-blue-400 hover:text-blue-300 underline flex items-center gap-1"
        >
          {displayText}
        </a>
      );
    }

    const isDesc = isDescriptionColumn(col);
    const truncateLength = 200;
    const key = `${rowIdx}-${col}`;
    const isExpanded = expanded[key];
    const isTruncated = isDesc && stringValue.length > truncateLength;

    if (!isDesc || !isTruncated) {
      return stringValue;
    }

    return (
      <div>
        <span>
          {isExpanded ? stringValue : `${stringValue.substring(0, truncateLength)}...`}
        </span>
        <button
          onClick={() => toggleExpand(rowIdx, col)}
          className="ml-2 text-blue-400 hover:text-blue-300 text-xs font-medium underline"
        >
          {isExpanded ? 'Show less' : 'Read more'}
        </button>
      </div>
    );
  };

  return (
    <div className="overflow-auto max-h-96 rounded-lg border border-slate-600">
      <table className="min-w-full divide-y divide-slate-600">
        <thead className="bg-slate-800 sticky top-0 z-10">
          <tr>
            {columns.map((col) => (
              <th
                key={col}
                className={`px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider ${
                  isDescriptionColumn(col) ? 'min-w-[400px]' : ''
                }`}
              >
                {col}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="bg-slate-900 divide-y divide-slate-700">
          {data.map((row, idx) => (
            <tr key={idx} className="hover:bg-slate-800 transition-colors">
              {columns.map((col) => (
                <td 
                  key={col} 
                  className={`px-4 py-3 text-sm text-gray-300 ${
                    isDescriptionColumn(col) 
                      ? 'max-w-[500px] whitespace-normal' 
                      : 'whitespace-nowrap'
                  }`}
                >
                  {renderCell(row[col], idx, col)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
