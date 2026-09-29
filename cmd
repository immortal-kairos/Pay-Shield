:: ==========================================
:: PAYSHIELD LOCAL ENVIRONMENT SETUP
:: ==========================================

:: 1. Start the PostgreSQL database in the background
docker-compose up -d

:: 2. Navigate to the backend, set up a virtual environment, and install dependencies
cd payshield
cd backend
python -m venv venv
call venv\Scripts\activate
pip install -r requirements.txt

:: 3. Run the FastAPI server
uvicorn app.main:app --reload

:: ------------------------------------------
:: ALTERNATIVE BACKEND COMMANDS
:: ------------------------------------------
:: Quick Start (If already installed):
cd payshield
cd backend
call venv\Scripts\activate
uvicorn app.main:app --reload

:: Run Backend Tests:
cd payshield
cd backend
call venv\Scripts\activate
pytest


:: ------------------------------------------
:: FRONTEND SETUP & RUN
:: ------------------------------------------

    Environment Variables:
:: Copy the example environment file and adjust if necessary.
:: Bash / DOS
copy .env.example .env.local

:: Navigate to frontend, install dependencies, and start the development server
cd payshield
cd frontend
npm install
npm run dev

:: Quick Start (If already installed):
cd payshield
cd frontend
npm run dev


:: ==========================================
:: REFERENCE LINKS & CREDENTIALS
:: ==========================================

// API DOCUMENTATION URL
http://localhost:8000/docs

// WEBSITE URL
http://localhost:3000/checker/payments

// TEST CREDENTIALS
{
  "email": "farhan.maker@example.com",
  "password": "Password123!",
  "role": "MAKER",
  "org_name": "Farhan Corp"
}