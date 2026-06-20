# SimpleWeb

SimpleWeb is a lightweight Flask application for user authentication, account access, and profile management. The current version focuses on signing in, viewing a dashboard, and managing account details rather than budgeting or transaction tracking.

## Features

- **Landing page** with a branded home view and a navigation bar.
- **User registration and login** with password validation and session-based authentication.
- **Protected dashboard** for logged-in users.
- **Profile pages** for viewing account details.
- **Password change flow** that verifies the current password before updating it.
- **Flash messages** for success and error feedback.
- **Docker-ready deployment** with Nginx and PostgreSQL.

## Installation

### Local Development

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd SimpleWeb
   ```

2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create a local environment file (optional but recommended):
   ```bash
   copy .env.example .env
   ```

4. Set the required environment variables before running the app:
   ```bash
   set DATABASE_URL=postgresql://user:pass@localhost:5432/mydb
   set SECRET_KEY=your-secret-key
   ```

5. Start the application:
   ```bash
   python app.py
   ```

The app will be available at http://localhost:5000.

### Docker Setup

1. Build and start the containers:
   ```bash
   docker-compose up --build
   ```

2. Access the application through the reverse proxy:
   - Web UI: http://localhost
   - Flask app (internal): http://localhost:5000

3. To stop the containers:
   ```bash
   docker-compose down
   ```

## Tech Stack

- **Backend**: Flask
- **ORM**: Flask-SQLAlchemy
- **Database**: PostgreSQL
- **Frontend**: Jinja2 templates and static CSS
- **Reverse Proxy**: Nginx
- **Containerization**: Docker and Docker Compose
- **Password Security**: Werkzeug password hashing

## Resource Limits

The Docker Compose setup includes resource limits for each service:

- **Nginx**
  - CPU limit: 0.25
  - Memory limit: 256MB
  - CPU reservation: 0.1
  - Memory reservation: 128MB

- **Web (Flask app)**
  - CPU limit: 0.5
  - Memory limit: 512MB
  - CPU reservation: 0.25
  - Memory reservation: 256MB

- **Database (PostgreSQL)**
  - CPU limit: 1.0
  - Memory limit: 1GB
  - CPU reservation: 0.5
  - Memory reservation: 512MB

## API Routes

The app uses simple Flask routes for authentication and profile management:

- `GET /` - Home page
- `GET /auth` - Authentication page
- `POST /register` - Register a new user
- `POST /login` - Log in a user
- `GET /logout` - Log out the current user
- `GET /dashboard` - Authenticated dashboard page
- `GET /profile` - User profile page
- `GET /profile2` - Alternate profile page
- `POST /profile/change-password` - Change the logged-in user's password

## Environment Variables

The application expects the following variables:

- `DATABASE_URL` - PostgreSQL connection string used by SQLAlchemy
- `SECRET_KEY` - Secret key used to secure Flask session data

Optional note:
- A `.env` file is used by Docker Compose to supply runtime environment values.
- If `SECRET_KEY` is not set, the app falls back to a development default value.

