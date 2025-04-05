'use client';

import { TimeSeriesData } from '../types';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';

interface SentimentGraphProps {
  data: TimeSeriesData[];
}

export default function SentimentGraph({ data }: SentimentGraphProps) {
  return (
    <div className="w-full h-[400px] bg-gray-900/50 rounded-lg p-4">
      <h2 className="text-xl font-semibold mb-4 text-gray-100">Sentiment Analysis Over Time</h2>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
          <XAxis
            dataKey="time_period"
            stroke="#9CA3AF"
            tick={{ fill: '#9CA3AF' }}
          />
          <YAxis stroke="#9CA3AF" tick={{ fill: '#9CA3AF' }} />
          <Tooltip
            contentStyle={{
              backgroundColor: '#1F2937',
              border: '1px solid #374151',
              borderRadius: '0.5rem',
            }}
          />
          <Legend />
          <Line
            type="monotone"
            dataKey="positive_ratio"
            stroke="#10B981"
            name="Positive"
            strokeWidth={2}
          />
          <Line
            type="monotone"
            dataKey="neutral_ratio"
            stroke="#6B7280"
            name="Neutral"
            strokeWidth={2}
          />
          <Line
            type="monotone"
            dataKey="negative_ratio"
            stroke="#EF4444"
            name="Negative"
            strokeWidth={2}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}