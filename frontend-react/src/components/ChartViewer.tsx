import { useRef } from 'react';
import { BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

interface ChartViewerProps {
  data: Record<string, any>[];
  columns: string[];
}

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8', '#82CA9D', '#FFC658', '#FF6B9D'];

function downloadChartAsPng(container: HTMLDivElement | null, filename: string) {
  if (!container) return;
  const svgElement = container.querySelector('svg');
  if (!svgElement) return;

  const cloned = svgElement.cloneNode(true) as SVGSVGElement;
  const { width, height } = svgElement.getBoundingClientRect();
  cloned.setAttribute('width', String(width));
  cloned.setAttribute('height', String(height));

  // Add dark background to the exported image
  const bgRect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
  bgRect.setAttribute('width', '100%');
  bgRect.setAttribute('height', '100%');
  bgRect.setAttribute('fill', '#1e293b');
  cloned.insertBefore(bgRect, cloned.firstChild);

  const svgData = new XMLSerializer().serializeToString(cloned);
  const svgBlob = new Blob([svgData], { type: 'image/svg+xml;charset=utf-8' });
  const url = URL.createObjectURL(svgBlob);

  const img = new Image();
  const canvas = document.createElement('canvas');
  const scale = 2; // 2x for retina clarity
  canvas.width = width * scale;
  canvas.height = height * scale;

  img.onload = () => {
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    ctx.scale(scale, scale);
    ctx.drawImage(img, 0, 0, width, height);
    canvas.toBlob((blob) => {
      if (!blob) return;
      const a = document.createElement('a');
      a.href = URL.createObjectURL(blob);
      a.download = `${filename}.png`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    }, 'image/png');
  };
  img.src = url;
}

function DownloadButton({ onClick }: { onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      title="Download chart as PNG"
      className="p-1.5 rounded-md text-gray-400 hover:text-white hover:bg-slate-700 transition-colors"
    >
      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
        <polyline points="7 10 12 15 17 10" />
        <line x1="12" y1="15" x2="12" y2="3" />
      </svg>
    </button>
  );
}

export default function ChartViewer({ data, columns }: ChartViewerProps) {
  const barRef = useRef<HTMLDivElement>(null);
  const pieRef = useRef<HTMLDivElement>(null);
  const multiRef = useRef<HTMLDivElement>(null);

  if (!data || data.length === 0) {
    return <div className="text-gray-400 text-center py-8">No data to visualize</div>;
  }

  // Detect numeric columns
  const numericCols = columns.filter(col => {
    const firstValue = data[0][col];
    return !isNaN(Number(firstValue)) && firstValue !== null && firstValue !== '(Not Set)';
  });

  const textCols = columns.filter(col => !numericCols.includes(col));

  // Simple visualization: 2 columns (category + value)
  if (columns.length === 2 && numericCols.length === 1) {
    const catCol = textCols[0];
    const valCol = numericCols[0];
    const chartData = data.slice(0, 15).map(row => ({
      name: String(row[catCol]).substring(0, 30),
      value: Number(row[valCol])
    }));

    return (
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        <div className="bg-slate-800 p-4 rounded-lg min-w-0" ref={barRef}>
          <div className="flex items-center justify-between mb-4">
            <h4 className="text-white font-semibold">Bar Chart</h4>
            <DownloadButton onClick={() => downloadChartAsPng(barRef.current, 'bar-chart')} />
          </div>
          <ResponsiveContainer width="100%" height={350}>
            <BarChart data={chartData} margin={{ left: 10, right: 10, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis dataKey="name" stroke="#9CA3AF" angle={-45} textAnchor="end" height={120} interval={0} fontSize={11} />
              <YAxis stroke="#9CA3AF" />
              <Tooltip
                contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #475569' }}
                labelStyle={{ color: '#fff' }}
              />
              <Bar dataKey="value" fill="#3b82f6" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-slate-800 p-4 rounded-lg min-w-0 overflow-hidden" ref={pieRef}>
          <div className="flex items-center justify-between mb-4">
            <h4 className="text-white font-semibold">Pie Chart</h4>
            <DownloadButton onClick={() => downloadChartAsPng(pieRef.current, 'pie-chart')} />
          </div>
          <ResponsiveContainer width="100%" height={400}>
            <PieChart>
              <Pie
                data={chartData.slice(0, 8)}
                cx="50%"
                cy="45%"
                labelLine={true}
                label={({ name, percent }) => {
                  const truncated = name.length > 18 ? name.substring(0, 18) + '…' : name;
                  return `${truncated}: ${((percent ?? 0) * 100).toFixed(0)}%`;
                }}
                outerRadius={90}
                fill="#8884d8"
                dataKey="value"
              >
                {chartData.slice(0, 8).map((_entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #475569' }}
                itemStyle={{ color: '#fff' }}
                labelStyle={{ color: '#fff' }}
              />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>
    );
  }

  // Multiple numeric columns
  if (numericCols.length >= 2) {
    const chartData = data.slice(0, 15).map((row, idx) => ({
      name: textCols.length > 0 ? String(row[textCols[0]]).substring(0, 20) : `Row ${idx + 1}`,
      ...numericCols.reduce((acc, col) => ({ ...acc, [col]: Number(row[col]) }), {})
    }));

    return (
      <div className="bg-slate-800 p-4 rounded-lg" ref={multiRef}>
        <div className="flex items-center justify-between mb-4">
          <h4 className="text-white font-semibold">Multi-Metric Comparison</h4>
          <DownloadButton onClick={() => downloadChartAsPng(multiRef.current, 'multi-metric-chart')} />
        </div>
        <ResponsiveContainer width="100%" height={400}>
          <BarChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
            <XAxis dataKey="name" stroke="#9CA3AF" angle={-45} textAnchor="end" height={100} />
            <YAxis stroke="#9CA3AF" />
            <Tooltip
              contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #475569' }}
              labelStyle={{ color: '#fff' }}
            />
            <Legend />
            {numericCols.slice(0, 5).map((col, idx) => (
              <Bar key={col} dataKey={col} fill={COLORS[idx % COLORS.length]} />
            ))}
          </BarChart>
        </ResponsiveContainer>
      </div>
    );
  }

  return (
    <div className="text-gray-400 text-center py-8">
      💡 This data is best viewed in table format. Try queries with aggregations (COUNT, SUM, AVG) for visualizations.
    </div>
  );
}
