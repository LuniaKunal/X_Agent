-- Table to store sentiment analysis runs
CREATE TABLE analyses (
    analysis_id SERIAL PRIMARY KEY,  -- Unique ID for each analysis run (auto-incrementing integer)
    username VARCHAR(255) NOT NULL, -- Username that was analyzed
    analysis_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, -- Timestamp of when the analysis was performed
    positive_sentiment_percentage NUMERIC, -- Percentage of positive sentiment in the analysis
    neutral_sentiment_percentage NUMERIC,  -- Percentage of neutral sentiment
    negative_sentiment_percentage NUMERIC, -- Percentage of negative sentiment
    tweet_count INTEGER,             -- Total number of tweets (including replies) analyzed
    query_parameters JSONB          -- Store query parameters as JSON (e.g., count, date range) - Optional, for flexibility
);

-- Table to store individual tweets and replies analyzed
CREATE TABLE tweets (
    tweet_id BIGINT PRIMARY KEY,    -- Unique ID of the tweet (from Twitter API)
    analysis_id INTEGER REFERENCES analyses(analysis_id), -- Foreign key linking to the analysis run
    type VARCHAR(50),               -- Type of content: 'post' or 'reply'
    username VARCHAR(255),          -- Username of the tweet author
    text TEXT,                      -- Full text of the tweet
    created_at TIMESTAMP WITH TIME ZONE, -- Tweet creation timestamp
    sentiment VARCHAR(50),          -- Sentiment label: 'positive', 'neutral', 'negative'
    sentiment_score NUMERIC         -- Sentiment score (e.g., from the model)
);

-- Table to store graph data for sentiment analysis over time
CREATE TABLE graph_data (
    graph_id SERIAL PRIMARY KEY,
    analysis_id INTEGER REFERENCES analyses(analysis_id),
    date DATE NOT NULL,
    positive NUMERIC NOT NULL,
    neutral NUMERIC NOT NULL,
    negative NUMERIC NOT NULL,
    username VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);



CREATE TABLE sentiment_timeseries (
    timeseries_id SERIAL PRIMARY KEY,
    period_type VARCHAR(10) NOT NULL CHECK (period_type IN ('day', 'week', 'month')),
    period_start TIMESTAMPTZ NOT NULL,
    period_end TIMESTAMPTZ NOT NULL,
    positive_score NUMERIC NOT NULL,
    neutral_score NUMERIC NOT NULL,
    negative_score NUMERIC NOT NULL,
    tweet_count INT4 NOT NULL,
    analysis_id INT4 REFERENCES analyses(analysis_id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Additional constraints for data integrity
    CHECK (period_start < period_end),
    CHECK (positive_score >= 0),
    CHECK (neutral_score >= 0),
    CHECK (negative_score >= 0)
);

-- Create indexes for efficient querying
CREATE INDEX idx_sentiment_timeseries_period ON sentiment_timeseries(period_type, period_start);
CREATE INDEX idx_sentiment_timeseries_analysis ON sentiment_timeseries(analysis_id);

-- Indexes for performance (optional, but recommended for larger datasets)
CREATE INDEX idx_analyses_username ON analyses (username);
CREATE INDEX idx_tweets_analysis_id ON tweets (analysis_id);
CREATE INDEX idx_tweets_sentiment ON tweets (sentiment);

-- Create indexes for performance
CREATE INDEX idx_graph_data_analysis_id ON graph_data (analysis_id);
CREATE INDEX idx_graph_data_username ON graph_data (username);
CREATE INDEX idx_graph_data_date ON graph_data (date);