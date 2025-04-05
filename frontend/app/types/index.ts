export interface Tweet {
  id: string;
  type: string;
  text: string;
  username: string;
  created_at: string;
  sentiment: string;
  score: number;
}

export interface TimeSeriesData {
  time_period: string;
  total_tweets: number;
  positive_ratio: number;
  neutral_ratio: number;
  negative_ratio: number;
}

export interface SentimentReport {
  tweets: Tweet[];
  summary: {
    positive: number;
    neutral: number;
    negative: number;
  };
  top_positive: Tweet[];
  top_neutral: Tweet[];
  top_negative: Tweet[];
  graph_data: any[];
}