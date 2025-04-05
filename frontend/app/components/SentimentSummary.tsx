'use client';

import { Tweet } from '../types';
import { ArrowUpCircle, ArrowDownCircle, Minus } from 'lucide-react';

interface SentimentSummaryProps {
  topPositive: Tweet[];
  topNegative: Tweet[];
  topNeutral: Tweet[];
}

export default function SentimentSummary({
  topPositive,
  topNegative,
  topNeutral,
}: SentimentSummaryProps) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
      <div className="bg-gray-900/50 rounded-lg p-6">
        <div className="flex items-center gap-2 mb-4">
          <ArrowUpCircle className="text-green-500" size={24} />
          <h2 className="text-xl font-semibold text-gray-100">Bullish Tweets</h2>
        </div>
        <div className="space-y-4">
          {topPositive.map((tweet) => (
            <div key={tweet.id} className="p-4 bg-gray-800/50 rounded-lg">
              <p className="text-gray-300">{tweet.text}</p>
              <div className="mt-2 flex justify-between items-center text-sm">
                <span className="text-gray-400">@{tweet.username}</span>
                <span className="text-green-500">Score: {tweet.score.toFixed(2)}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="bg-gray-900/50 rounded-lg p-6">
        <div className="flex items-center gap-2 mb-4">
          <ArrowDownCircle className="text-red-500" size={24} />
          <h2 className="text-xl font-semibold text-gray-100">Bearish Tweets</h2>
        </div>
        <div className="space-y-4">
          {topNegative.map((tweet) => (
            <div key={tweet.id} className="p-4 bg-gray-800/50 rounded-lg">
              <p className="text-gray-300">{tweet.text}</p>
              <div className="mt-2 flex justify-between items-center text-sm">
                <span className="text-gray-400">@{tweet.username}</span>
                <span className="text-red-500">Score: {tweet.score.toFixed(2)}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}