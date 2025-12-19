import { BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

interface ChartViewerProps {
  data: Record<string, any>[];
  columns: string[];
}

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8', '#82CA9D', '#FFC658', '#FF6B9D'];

export default function ChartViewer({ data, columns }: ChartViewerProps) {
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
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-slate-800 p-4 rounded-lg">
          <h4 className="text-white font-semibold mb-4">Bar Chart</h4>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis dataKey="name" stroke="#9CA3AF" angle={-45} textAnchor="end" height={100} />
              <YAxis stroke="#9CA3AF" />
              <Tooltip
                contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #475569' }}
                labelStyle={{ color: '#fff' }}
              />
              <Bar dataKey="value" fill="#3b82f6" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-slate-800 p-4 rounded-lg">
          <h4 className="text-white font-semibold mb-4">Pie Chart</h4>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={chartData.slice(0, 8)}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {chartData.slice(0, 8).map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #475569' }}
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
      <div className="bg-slate-800 p-4 rounded-lg">
        <h4 className="text-white font-semibold mb-4">Multi-Metric Comparison</h4>
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
