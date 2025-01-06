
# Trail Service Microservice

A RESTful microservice for managing hiking trails, part of a well-being trail application. This service provides trail management functionality with secure authentication and authorization.

## Features

- User authentication via Plymouth's authentication service
- JWT token-based authorization
- CRUD operations for trails
- User-trail associations
- Audit logging
- OpenAPI/Swagger documentation

## Tech Stack

- Python 3.8+
- FastAPI
- SQL Server
- JWT for token management
- PyODBC for database connectivity

## Prerequisites

- Python 3.8 or higher
- SQL Server
- ODBC Driver 17 for SQL Server
- pip (Python package manager)

## Installation

1. Clone the repository:
```bash
git clone [your-repository-url]
cd trail-service
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up your database:
- Run the SQL scripts provided in `/sql/setup.sql`
- Configure your connection string in `config.py`

5. Configure environment variables:
```bash
# Create .env file
SECRET_KEY=your-secret-key
DATABASE_URL=your-database-url
```

## Project Structure

```
trail-service/
├── app/
│   ├── main.py            # FastAPI application
│   ├── auth_utils.py      # Authentication utilities
│   ├── user_service.py    # User management
│   └── config.py          # Configuration
├── sql/
│   ├── setup.sql          # Database setup
├── tests/
│   └── test_api.py        # API tests
├── requirements.txt
└── README.md
```

## API Endpoints

### Authentication
- `POST /token` - Obtain JWT token

### Trails
- `GET /api/trails` - List all trails
- `GET /api/trails/{trail_id}` - Get specific trail
- `POST /api/trails` - Create new trail
- `PUT /api/trails/{trail_id}` - Update trail
- `DELETE /api/trails/{trail_id}` - Delete trail

### User Trails
- `GET /api/users/{user_id}/trails` - Get user's trails

## Running the Application

1. Start the server:
```bash
uvicorn app.main:app --reload --port 3000
```

2. Access the API documentation:
```
http://localhost:3000/docs
```

## Authentication

This service uses Plymouth's authentication service for user verification. To authenticate:

1. Make a POST request to `/token` with email and password
2. Use the returned JWT token in the Authorization header:
```
Authorization: Bearer <your-token>
```

## Example Usage

### Login
```bash
curl -X POST "http://localhost:3000/token" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "username=user@plymouth.ac.uk&password=password"
```

### Create Trail
```bash
curl -X POST "http://localhost:3000/api/trails" \
     -H "Authorization: Bearer <your-token>" \
     -H "Content-Type: application/json" \
     -d '{"TrailName": "Coastal Path", "Description": "Scenic coastal walk"}'
```

## Testing

Run the tests using pytest:
```bash
pytest
```

## Database Schema

### CW1.User
- UserID (PK)
- Name
- Email (Unique)
- Password

### CW1.Trail
- TrailID (PK)
- TrailName
- Description
- DateCreated
- CreatedBy (FK to User)

### CW1.UserTrail
- UserTrailID (PK)
- UserID (FK)
- TrailID (FK)

## Security Considerations

- SQL injection prevention through parameterized queries
- JWT token authentication
- Input validation using Pydantic models
- CORS configuration
- Error handling to prevent information leakage

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request
