import { TimeSeriesData, SentimentReport } from '../types';

const API_BASE_URL = 'http://127.0.0.1:8000/api';

export async function getUserTweets(username: string) {
  const response = await fetch(`${API_BASE_URL}/user-tweets`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ username }),
  });

  if (!response.ok) {
    throw new Error('Failed to fetch user tweets');
  }

  return response.json();
}

export async function getWeeklyAnalysis(username: string): Promise<{ data: TimeSeriesData[] }> {
  const response = await fetch(`${API_BASE_URL}/user-tweets/weekly_or_monthly_analysis/${username}`);

  if (!response.ok) {
    throw new Error('Failed to fetch weekly analysis');
  }

  return response.json();
}

export async function getSentimentReports(username: string): Promise<SentimentReport[]> {
  const response = await fetch(`${API_BASE_URL}/reports/${username}`);

  if (!response.ok) {
    throw new Error('Failed to fetch sentiment reports');
  }

  return response.json();
}

export async function analyzeTweets(username: string) {
  const response = await fetch(`${API_BASE_URL}/analyze`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      query: username,
      max_tweets: 15
    }),
  });

  if (!response.ok) {
    throw new Error('Failed to analyze tweets');
  }

  return response.json();
}