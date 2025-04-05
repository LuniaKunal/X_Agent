'use client';

import { useState } from 'react';
import SearchBar from './components/SearchBar';
import SentimentGraph from './components/SentimentGraph';
import SentimentSummary from './components/SentimentSummary';
import { TimeSeriesData, SentimentReport } from './types';
import { BarChart3 } from 'lucide-react';
import { getWeeklyAnalysis, getSentimentReports, analyzeTweets, getUserTweets } from './services/api';

export default function Home() {
  const [timeSeriesData, setTimeSeriesData] = useState<TimeSeriesData[]>([]);
  const [sentimentReport, setSentimentReport] = useState<SentimentReport | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSearch = async (username: string) => {
    setLoading(true);
    setError(null);
    
    try {
      // Gets the Latest Tweets from Twitter
      // await analyzeTweets(username);
      
      // Then get the user post tweets and replies of the posts.
      await getUserTweets(username);
      
      // Get time series data
      const timeSeriesJson = await getWeeklyAnalysis(username);
      setTimeSeriesData(timeSeriesJson.data);

      // Get sentiment report
      const reportJson = await getSentimentReports(username);
      setSentimentReport(reportJson[0]);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen bg-gray-950 text-white p-8">
      <div className="max-w-7xl mx-auto space-y-8">
        <div className="text-center mb-12">
          <div className="flex items-center justify-center gap-3 mb-4">
            <BarChart3 size={32} className="text-blue-500" />
            <h1 className="text-4xl font-bold">Sentiment Analysis</h1>
          </div>
          <p className="text-gray-400">Analyze Twitter sentiment for any user</p>
        </div>

        <SearchBar onSearch={handleSearch} />

        {loading && (
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto"></div>
            <p className="mt-4 text-gray-400">Analyzing sentiment...</p>
          </div>
        )}

        {error && (
          <div className="bg-red-900/50 border border-red-700 text-red-100 px-4 py-3 rounded-lg text-center">
            {error}
          </div>
        )}

        {!loading && !error && timeSeriesData.length > 0 && (
          <div className="space-y-8">
            <SentimentGraph data={timeSeriesData} />
            {sentimentReport && (
              <SentimentSummary
                topPositive={sentimentReport.top_positive}
                topNegative={sentimentReport.top_negative}
                topNeutral={sentimentReport.top_neutral}
              />
            )}
          </div>
        )}
      </div>
    </main>
  );
}