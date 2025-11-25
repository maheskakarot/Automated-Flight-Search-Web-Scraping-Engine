Automated Flight Aggregation Engine

A robust web scraping API built with Django and Selenium that automates the retrieval of real-time flight itineraries from airline portals. Designed for reliability and performance, this system features intelligent caching, visual error debugging, and centralized logging.

🚀 Key Features

Automated Browser Interaction: Utilizes Selenium WebDrivers to mimic user behavior—opening browsers, inputting travel details, and navigating dynamic airline pages.

High-Performance Caching: Implements Redis to cache frequently searched flight routes, significantly reducing API latency and redundant scraping operations.

Visual Debugging: Automatically captures screenshots upon scraping failures and uploads them to Azure Blob Storage for rapid debugging.

Centralized Logging: System logs and scraper health metrics are indexed in Elasticsearch for easy analysis.

Production Ready: Deployed using Gunicorn as the application server and managed via Jenkins CI/CD pipelines.

🛠️ Tech Stack

Framework: Django (Python)

Automation: Selenium WebDriver

Database: PostgreSQL

Caching: Redis

Cloud Storage: Azure Blob Storage

Logging: Elasticsearch

CI/CD & Deployment: Jenkins, Gunicorn

⚙️ Architecture Workflow

Request: User sends a search request via the API (e.g., Origin, Destination, Date).

Cache Check: System checks Redis for existing valid data. If found, returns immediately.

Scraping: If not in cache, Selenium initializes a browser instance, navigates to the airline site, inputs criteria, and scrapes the loaded results.

Storage:

Flight data is returned to the user and cached in Redis.

Transactional data is stored in PostgreSQL.

Error Handling: If an exception occurs, a screenshot is taken, uploaded to Azure Blob, and the event is logged to Elasticsearch.

🔧 Installation & Setup

Prerequisites

Python 3.8+

PostgreSQL

Redis Server

Elasticsearch

Chrome/Gecko Driver (matching your browser version)

Steps

Clone the Repository

git clone [https://github.com/yourusername/flight-aggregation-engine.git](https://github.com/yourusername/flight-aggregation-engine.git)
cd flight-aggregation-engine


Create and Activate Virtual Environment

python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate


Install Dependencies

pip install -r requirements.txt


Set Up Environment Variables
Create a .env file in the root directory:

# Django Settings
DEBUG=True
SECRET_KEY=your_secret_key
ALLOWED_HOSTS=localhost,127.0.0.1

# Database (PostgreSQL)
DB_NAME=flight_db
DB_USER=postgres
DB_PASSWORD=yourpassword
DB_HOST=localhost
DB_PORT=5432

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# Azure Blob Storage
AZURE_CONNECTION_STRING=your_azure_connection_string
AZURE_CONTAINER_NAME=error-screenshots

# Elasticsearch
ELASTICSEARCH_HOST=http://localhost:9200


Run Migrations

python manage.py migrate


Start the Server

# For development
python manage.py runserver

# For production (using Gunicorn)
gunicorn core.wsgi:application --bind 0.0.0.0:8000


📝 Usage

Search Endpoint
GET /api/v1/search/

Parameters:

origin: IATA Code (e.g., JFK)

destination: IATA Code (e.g., LHR)

date: YYYY-MM-DD

Example Request:

curl -X GET "http://localhost:8000/api/v1/search/?origin=JFK&destination=LHR&date=2024-12-25"


🤝 Contributing

Fork the repository

Create your feature branch (git checkout -b feature/AmazingFeature)

Commit your changes (git commit -m 'Add some AmazingFeature')

Push to the branch (git push origin feature/AmazingFeature)

Open a Pull Request
