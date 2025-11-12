.PHONY: help install train run-api run-web test clean docker-build docker-up docker-down

help:
	@echo "WaterWatch - Available Commands:"
	@echo "  make install      - Install all dependencies"
	@echo "  make train        - Train the ML model"
	@echo "  make run-api      - Run the FastAPI backend"
	@echo "  make run-web      - Run the React frontend"
	@echo "  make test         - Run tests"
	@echo "  make clean        - Clean build artifacts"
	@echo "  make docker-build - Build Docker images"
	@echo "  make docker-up    - Start services with Docker"
	@echo "  make docker-down  - Stop Docker services"

install:
	@echo "Installing backend dependencies..."
	cd backend && pip install -r requirements.txt
	@echo "Installing frontend dependencies..."
	cd web && npm install

train:
	@echo "Training ML model..."
	cd backend && python app/ml/train.py

run-api:
	@echo "Starting FastAPI backend..."
	cd backend && uvicorn app.main:app --reload

run-web:
	@echo "Starting React frontend..."
	cd web && npm run dev

test:
	@echo "Running tests..."
	cd backend && pytest tests/ -v

clean:
	@echo "Cleaning build artifacts..."
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf backend/app/ml/artifacts/*.pkl
	rm -rf backend/app/ml/artifacts/*.png
	rm -rf web/dist web/build

docker-build:
	@echo "Building Docker images..."
	docker-compose build

docker-up:
	@echo "Starting services with Docker..."
	docker-compose up -d
	@echo "API: http://localhost:8000"
	@echo "Web: http://localhost:3000"

docker-down:
	@echo "Stopping Docker services..."
	docker-compose down
