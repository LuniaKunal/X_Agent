# Real Time Sentimental Analysis using X

A powerful application for analyzing sentiment from X (formerly Twitter) data in real-time.

## Project Demo

[![Project Demo](https://cdn.loom.com/sessions/thumbnails/cd4105230c3546d1be84f03d7c5b1ae4-with-play.gif)](https://www.loom.com/share/cd4105230c3546d1be84f03d7c5b1ae4?sid=480955d9-8160-491b-baad-5edd645375c6)

## Technologies

- **Backend**: FastAPI
- **Frontend**: NextJS with TypeScript and TailwindCSS

## Setup Instructions

### Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment, activate it
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start the server
python -m uvicorn app.main:app --reload
```

### Frontend Setup

```bash
# Install dependencies
npm install

# Start development server
npm run dev
```

## Features

- Real-time sentiment analysis of X posts and replies
- Interactive visualization dashboard
- Historical data tracking

