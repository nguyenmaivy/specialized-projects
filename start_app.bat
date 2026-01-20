@echo off
echo Starting AI Sales Forecasting Dashboard...

start "Backend API" cmd /k "cd backend && python -m pip install -r requirements.txt && python -m uvicorn main:app --reload --port 8000"
start "Frontend App" cmd /k "cd frontend && npm install && npm run dev"

echo Backend running on http://localhost:8000
echo Frontend running on http://localhost:3000
