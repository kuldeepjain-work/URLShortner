# URL Shortener

A lightweight, fast, and feature-rich URL shortening service built with FastAPI and PostgreSQL.

## Overview

This URL shortener allows you to convert long, unwieldy URLs into short, easy-to-share links. It provides a RESTful API for creating, managing, and tracking shortened URLs with analytics on usage.

The main application file is located in the `app` folder as `app.py`.

## Features

- **URL Shortening**: Convert long URLs into short, manageable links
- **Custom Short URLs**: Optionally specify your own custom short path
- **Click Tracking**: Monitor how many times each shortened URL is accessed
- **Statistics API**: View usage statistics for all shortened URLs
- **URL Deactivation**: Ability to deactivate links while preserving analytics
- **RESTful API**: Clean API design with FastAPI
- **PostgreSQL Integration**: Reliable storage for URL mappings and analytics

## Requirements

- Python 3.7+
- PostgreSQL 10+
- Required Python packages (see `requirements.txt`)

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/url-shortener.git
cd url-shortener
```

### 2. Create a Virtual Environment

```bash
# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. PostgreSQL Setup

> **Note**: PostgreSQL must be running in the background before continuing.

1. Create a database for the URL shortener:

```bash
createdb urlshortener
```

2. Create a `.env` file in the project root with your PostgreSQL connection details:

```
DB_HOST=localhost
DB_PORT=5432
DB_NAME=urlshortener
DB_USER=postgres
DB_PASSWORD=your_password
```

Replace `your_password` with your actual PostgreSQL password.

## Running the Application

Navigate to the app folder and start the application with Uvicorn:

```bash
cd app
uvicorn app:app --reload
```

The application will be available at `http://localhost:8000`.

## Using the URL Shortener

### Creating a Short URL

```http
POST /shorten/
Content-Type: application/json

{
  "url": "https://example.com/very/long/path/with/query/parameters?param1=value1&param2=value2",
  "custom_path": "example"  // Optional
}
```

Response:

```json
{
  "short_url": "example",
  "original_url": "https://example.com/very/long/path/with/query/parameters?param1=value1&param2=value2",
  "created_at": "2023-07-15T08:30:45.123456",
  "visits": 0
}
```

### Using a Short URL

Simply navigate to:

```
GET /{short_url}
```

For example: `http://localhost:8000/example`

This will redirect you to the original URL.

### Viewing Statistics

```http
GET /stats/
```

Response:

```json
{
  "urls": [
    {
      "short_url": "example",
      "original_url": "https://example.com/very/long/path/with/query/parameters?param1=value1&param2=value2",
      "created_at": "2023-07-15T08:30:45.123456",
      "visits": 5
    },
    // Additional URLs...
  ],
  "total_urls": 10,
  "total_visits": 247
}
```

### Deactivating a URL

```http
DELETE /{short_url}
```

Response:

```json
{
  "short_url": "example",
  "original_url": "https://example.com/very/long/path/with/query/parameters?param1=value1&param2=value2",
  "created_at": "2023-07-15T08:30:45.123456",
  "visits": 5,
  "is_active": false
}
```

## Testing

A test file is included to verify the functionality of the URL shortener. It tests the API against a random URL (https://example.com/example).

Run the test with:

```bash
python test_url_shortener.py
```

## How It Works

### URL Generation

When a new URL is submitted for shortening, the system:

1. Checks if a custom short path is provided
   - If yes, it verifies it's not already in use
   - If no, it generates a random 6-character alphanumeric string

2. The short code generator uses a combination of:
   - Lowercase letters (a-z)
   - Uppercase letters (A-Z)
   - Numbers (0-9)

This gives a possible 62^6 (approximately 57 billion) unique combinations for a 6-character code.

### Database Schema

The PostgreSQL database uses a table called `url_map` with the following structure:

| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL | Primary key |
| short_url | VARCHAR(255) | The short URL path (unique) |
| original_url | TEXT | The original long URL |
| created_at | TIMESTAMP | When the URL was created |
| visits | INTEGER | Number of times the short URL was accessed |
| is_active | BOOLEAN | Whether the short URL is active |

### Database Connection

The application connects to PostgreSQL using the `psycopg2` library, which provides:
- Direct SQL access for optimal performance
- Connection pooling
- Parameterized queries to prevent SQL injection
- Transaction support

## Troubleshooting

### Database Connection Issues

If you encounter database connection issues:

1. Verify PostgreSQL is running:
```bash
pg_isready
```

2. Check your `.env` file has the correct credentials

3. Ensure the database exists:
```bash
psql -l | grep urlshortener
```

### Import Errors

If you encounter import errors when running the application:

1. Make sure you've activated the virtual environment
2. Verify all dependencies are installed:
```bash
pip freeze | grep -E 'fastapi|uvicorn|psycopg2|pydantic'
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.