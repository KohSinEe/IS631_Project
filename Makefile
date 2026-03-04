.PHONY: help install setup run migrate create-user format clean

help:
	@echo "Food Management App - Available Commands"
	@echo "=========================================="
	@echo "  make install       - Install dependencies with UV"
	@echo "  make setup         - Complete initial setup"
	@echo "  make run           - Run FastAPI server"
	@echo "  make run-streamlit - Run Streamlit UI"
	@echo "  make run-all       - Run FastAPI and Streamlit together"
	@echo "  make migrate       - Run database migrations"
	@echo "  make create-user   - Create first user"
	@echo "  make format        - Format code"
	@echo "  make clean         - Clean build artifacts"

install:
	@echo "Installing dependencies..."
	@rm -f uv.lock
	@uv sync
	@echo "✅ Dependencies installed"

setup: install
	@echo "Setting up environment..."
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "✅ Created .env file"; \
		echo "⚠️  Please update SECRET_KEY in .env"; \
		echo "   Generate with: openssl rand -hex 32"; \
	fi
	@echo "Running database migrations..."
	@uv run alembic upgrade head
	@echo ""
	@echo "✅ Setup complete!"
	@echo ""
	@echo "Next steps:"
	@echo "  1. Edit .env and update SECRET_KEY"
	@echo "  2. Run: make create-user"
	@echo "  3. Run: make run"


run:
	@uv run uvicorn app.main:app --reload --port 8000

run-streamlit:
	streamlit run frontend/app.py

run-all:
	@echo "Starting FastAPI and Streamlit..."
	(uv run uvicorn app.main:app --reload --port 8000 &)
	streamlit run frontend/app.py

migrate:
	@uv run alembic upgrade head

create-migration:
	@read -p "Migration message: " msg; \
	uv run alembic revision --autogenerate -m "$$msg"

create-user:
	@uv run python -m app.scripts.create_first_user

format:
	@uv run black app/
	@uv run isort app/

st:
	@uv run streamlit run frontend/app.py
  
test:
	@uv run pytest --cov=app/api --cov-report=term

clean:
	@echo "Cleaning up..."
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@find . -type f -name "*.pyo" -delete 2>/dev/null || true
	@rm -rf .pytest_cache dist build *.egg-info uv.lock
	@echo "✅ Cleanup complete"

