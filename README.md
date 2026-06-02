# SimpleWeb - Personal Finance Tracker

A lightweight web application for tracking personal income and expenses with user authentication.

## Features

- **User Authentication**: Register and login with secure password hashing
- **Transaction Management**: Add, edit, and view income/expense transactions
- **Dashboard**: View financial overview with total income, spending, and remaining balance
- **Merchant Tracking**: Tag transactions with merchant information
- **Profile Management**: User profile and password change functionality

## Tech Stack

- **Backend**: Flask, SQLAlchemy ORM
- **Database**: PostgreSQL
- **Frontend**: HTML templates with Flask rendering
- **Reverse Proxy**: Nginx
- **Containerization**: Docker & Docker Compose

## Installation

### Local Setup (Development)

1. Clone the repository and install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Set environment variables:
   ```bash
   export DATABASE_URL="postgresql://user:pass@localhost:5432/mydb"
   export SECRET_KEY="your-secret-key"
   ```

3. Create the PostgreSQL database and run the app:
   ```bash
   python app.py
   ```

The app will be available at `http://localhost:5000`

### Docker Setup (Recommended)

1. Build and run with Docker Compose:
   ```bash
   docker-compose up -d
   ```

2. Access the app at `http://localhost`

The setup includes:
- **Nginx**: Reverse proxy on port 80
- **Flask Web App**: On port 5000 (internal)
- **PostgreSQL**: Database with persistent volume

## Database

The app uses SQLAlchemy to manage:
- **Users**: Email, password, name
- **Transactions**: Amount, type (income/expense), date, description, merchant

## Resource Limits (Docker)

Docker containers are configured with CPU and memory limits:
- **Nginx**: 0.25 CPU, 256MB RAM (limit) / 0.1 CPU, 128MB (reserved)
- **Web**: 0.5 CPU, 512MB RAM (limit) / 0.25 CPU, 256MB (reserved)
- **Database**: 1 CPU, 1GB RAM (limit) / 0.5 CPU, 512MB (reserved)

## API Routes

- `GET /` - Home page
- `POST /register` - User registration
- `POST /login` - User login
- `GET /logout` - User logout
- `GET /dashboard` - Dashboard
- `GET /overview` - Transaction overview
- `POST /transactions/add` - Add transaction
- `POST /transactions/<id>/edit` - Edit transaction
- `GET /profile` - User profile

## Environment Variables

- `DATABASE_URL` - PostgreSQL connection string
- `SECRET_KEY` - Flask session secret key
