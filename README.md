# 🥗 Food Management App

A smart household food management system built with FastAPI and UV.

![Python](https://img.shields.io/badge/python-3.11-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109.0-green)
![UV](https://img.shields.io/badge/uv-latest-blueviolet)

## 🚀 Quick Start (3 commands)
```bash
# 1. Install dependencies
make install

# 2. Setup database and environment
make setup

# 3. Run the server
make run
```

Visit http://localhost:8000/docs for API documentation.

## 📦 Prerequisites

- Python 3.11+
- UV package manager (auto-installed by `make install`)

## 🛠 Detailed Setup

### Step 1: Clone Repository
```bash
git clone <your-repo-url>
cd food-management-app
```

### Step 2: Install UV (if not already installed)
```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
irm https://astral.sh/uv/install.ps1 | iex
```

### Step 3: Install Dependencies
```bash
uv sync
```

### Step 4: Configure Environment
```bash
# Copy example environment file
cp .env.example .env

# Generate a secure secret key
openssl rand -hex 32

# Update .env file with the generated key
```

### Step 5: Initialize Database
```bash
# Run migrations
uv run alembic upgrade head

# Create first user (optional)
uv run python -m app.scripts.create_first_user
```

### Step 6: Run Application
```bash
uv run uvicorn app.main:app --reload

# Or use make
make run
```

## 📚 API Endpoints

### Authentication

- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login and get JWT token
- `POST /api/v1/auth/refresh` - Refresh access token

### Users

- `GET /api/v1/users/me` - Get current user profile
- `PUT /api/v1/users/me` - Update current user
- `PUT /api/v1/users/me/password` - Change password

## 🔧 Development

### Common Commands
```bash
# Install new package
uv add package-name

# Install dev package
uv add --dev package-name

# Format code
make format

# Run migrations
make migrate

# Create new migration
make create-migration
```

## 📖 API Documentation

Once the server is running, visit:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🗄 Database

This project uses SQLite for local development. The database file is created as `food_management.db` in the project root.

## 📝 License

MIT License