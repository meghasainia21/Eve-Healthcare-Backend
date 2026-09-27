# EVE Healthcare — Backend Engineering Assignment

A backend service for **diagnostic test discovery, appointment booking, and simulated payments**, developed for the **EVE Healthcare SDE Intern — Backend Engineering Assignment**.

The project focuses on clean API design, relational database modeling, JWT authentication, booking and payment workflows, webhook idempotency, validation, authorization, testing, and containerized development.

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Database Design](#database-design)
- [Authentication](#authentication)
- [Diagnostic Centres & Tests](#diagnostic-centres--tests)
- [Booking System](#booking-system)
- [Simulated Payments](#simulated-payments)
- [Payment Webhook](#payment-webhook)
- [API Endpoints](#api-endpoints)
- [Getting Started](#getting-started)
- [Running with Docker](#running-with-docker)
- [API Documentation](#api-documentation)
- [Testing](#testing)
- [Demo Credentials](#demo-credentials)
- [Example Workflow](#example-workflow)
- [Edge Cases](#edge-cases)
- [Environment Variables](#environment-variables)
- [Engineering Decisions](#engineering-decisions)
- [Assumptions](#assumptions)
- [Future Improvements](#future-improvements)
- [Assignment Coverage](#assignment-coverage)

---

# Overview

EVE Healthcare requires a backend service for diagnostic test bookings and simulated payments.

The application allows authenticated users to:

1. Create an account and log in.
2. Authenticate using JWT tokens.
3. Browse diagnostic centres.
4. View available diagnostic tests and prices.
5. Book a diagnostic test appointment.
6. Make a simulated payment.
7. Receive booking status updates based on payment results.
8. Process payment-provider webhooks safely and idempotently.

The implementation uses **FastAPI** with **PostgreSQL** and is fully containerized using **Docker Compose**.

---

# Features

### Authentication

- User signup
- User login
- JWT-based authentication
- Password hashing
- Protected endpoints
- Request validation
- Role-based authorization where applicable

### Diagnostic Services

- Diagnostic centre listing
- Diagnostic test listing
- Test pricing
- Centre/test relationships

### Booking

- Authenticated booking creation
- Appointment date/time
- Booking amount
- Booking status
- Booking retrieval
- Authorization checks

### Payments

- Simulated payment processing
- SUCCESS / FAILED payment outcomes
- Booking state updates
- Payment records

### Webhooks

- Payment-status webhook
- Duplicate event protection
- Idempotent event processing
- Safe booking state transitions

### Engineering

- PostgreSQL
- Alembic migrations
- Docker
- Docker Compose
- Swagger/OpenAPI
- Pytest
- Structured logging
- Environment-based configuration

---

# Tech Stack

| Component | Technology |
|---|---|
| Language | Python |
| Framework | FastAPI |
| Database | PostgreSQL |
| ORM | SQLAlchemy |
| Migrations | Alembic |
| Authentication | JWT |
| API Documentation | Swagger / OpenAPI |
| Testing | Pytest |
| Containerization | Docker / Docker Compose |
| API Testing | Postman / Swagger UI |

---

# Architecture

```text
                         Client
                    ┌───────────────┐
                    │ Postman /     │
                    │ Swagger UI    │
                    └───────┬───────┘
                            │
                            ▼
                  ┌───────────────────┐
                  │     FastAPI       │
                  │      :8000        │
                  └─────────┬─────────┘
                            │
             ┌──────────────┼──────────────┐
             │              │              │
             ▼              ▼              ▼
      Authentication    Bookings       Payments
             │              │              │
             └──────────────┼──────────────┘
                            │
                            ▼
                  ┌───────────────────┐
                  │    PostgreSQL     │
                  │      :5432        │
                  └───────────────────┘

```

---

# 📁 Project Structure

```text
eve-healthcare-backend/
│
├── alembic/
│   └── versions/
│
├── app/
│   ├── api/
│   │   ├── deps.py
│   │   └── routes/
│   │       ├── auth.py
│   │       ├── bookings.py
│   │       ├── diagnostic.py
│   │       └── payments.py
│   │
│   ├── core/
│   │   ├── config.py
│   │   ├── database.py
│   │   └── security.py
│   │
│   ├── models/
│   │   ├── user.py
│   │   ├── diagnostic.py
│   │   ├── booking.py
│   │   └── payment.py
│   │
│   ├── schemas/
│   │   ├── auth.py
│   │   ├── diagnostic.py
│   │   ├── booking.py
│   │   └── payment.py
│   │
│   ├── services/
│   │   ├── auth_service.py
│   │   ├── booking_service.py
│   │   └── payment_service.py
│   │
│   └── main.py
│
├── scripts/
│   └── seed.py
│
├── tests/
│   ├── conftest.py
│   ├── test_auth.py
│   ├── test_diagnostic.py
│   ├── test_bookings.py
│   └── test_payments.py
│
├── .env.example
├── .gitignore
├── alembic.ini
├── docker-compose.yml
├── Dockerfile
├── Makefile
├── pytest.ini
├── requirements.txt
└── README.md
```

The repository keeps application code, database migrations, scripts, and tests separated for maintainability.

# 🗄 Database Design

PostgreSQL is used as the primary database.

## Entity Relationship

```text
User
 │
 │ 1:N
 ▼
Booking ──────────────► DiagnosticTest
  │                          │
  │                          │
  │                          ▼
  │                   DiagnosticCentre
  │
  │ 1:N
  ▼
Payment
```

## User

Stores application users and authentication information.

```text
User
├── id
├── email
├── password_hash
├── role
└── timestamps
```

## Diagnostic Centre

Represents a diagnostic testing facility.

```text
DiagnosticCentre
├── id
├── name
├── location
└── timestamps
```

## Diagnostic Test

Represents a diagnostic test offered by a centre.

```text
DiagnosticTest
├── id
├── centre_id
├── name
├── price
└── timestamps
```

## Booking

Represents a diagnostic appointment.

```text
Booking
├── id
├── user_id
├── diagnostic_test_id
├── diagnostic_centre_id
├── appointment_datetime
├── amount
├── status
└── timestamps
```

## Payment

Represents a simulated payment associated with a booking.

```text
Payment
├── id
├── booking_id
├── amount
├── status
├── provider_event_id
└── timestamps
```

Foreign keys and database constraints are used to maintain referential integrity.

# 🔐 Authentication

The API supports:

- Signup
- Login
- JWT access tokens
- Protected endpoints
- Request validation
- Authorization checks
- Password hashing

## Login Flow

```text
Client
   │
   │ POST /auth/login
   ▼
FastAPI
   │
   │ Validate credentials
   ▼
JWT Access Token
   │
   ▼
Client
   │
   │ Authorization: Bearer <token>
   ▼
Protected API
```

# 🧪 Diagnostic Centres & Tests

The API provides endpoints for retrieving diagnostic centres and diagnostic tests.

A diagnostic centre includes:

- Name
- Location
- Available diagnostic tests

Each diagnostic test includes:

- Test name
- Associated centre
- Price

These resources are used by the booking workflow.

---

# 📅 Booking System

Authenticated users can book diagnostic tests.

A booking contains:

- Patient/user
- Diagnostic test
- Diagnostic centre
- Appointment date/time
- Amount
- Booking status

## Booking States

```text
PENDING
   │
   ├───────────────┐
   │               │
   ▼               ▼
SUCCESS          FAILED
   │
   ▼
CONFIRMED
   │
   ▼
CANCELLED
```

# 💳 Simulated Payment Service

The assignment requires a simulated payment service instead of a real payment gateway.

Payment endpoint:

```text
POST /payments/
```

The simulated payment can result in:

```text
SUCCESS
```

or:

```text
FAILED
```

The associated booking is updated based on the payment result.

# 🔁 Payment Webhook

The application exposes a payment webhook:

```text
POST /payments/webhook/
```

The webhook is designed to be **idempotent**.

If the same payment event is delivered multiple times, it should not:

- Create duplicate payments
- Create duplicate bookings
- Incorrectly modify booking state
- Corrupt existing payment state

A unique provider event identifier is used to identify already-processed events.

# 📡 API Endpoints

## Authentication

```text
POST /auth/signup
POST /auth/login
GET  /auth/me
```

## Diagnostic Centres

```text
GET /diagnostic-centers
```

## Diagnostic Tests

```text
GET /diagnostic-tests
```

# 📅 Booking System

Authenticated users can book diagnostic tests.

A booking contains:

- Patient/user
- Diagnostic test
- Diagnostic centre
- Appointment date/time
- Amount
- Booking status

## Booking States

```text
PENDING
   │
   ├───────────────┐
   │               │
   ▼               ▼
SUCCESS          FAILED
   │
   ▼
CONFIRMED
   │
   ▼
CANCELLED
```

## Diagnostic Centres

```text
GET /diagnostic-centers
```

## Diagnostic Tests

```text
GET /diagnostic-tests
```

## Bookings

```text
GET  /bookings
POST /bookings
GET  /bookings/{booking_id}
```

## Payments

```text
POST /payments/
POST /payments/webhook/
```

## Health Check

```text
GET /health
```

---

# 📝 Example Requests

## Login

```http
POST /auth/login
Content-Type: application/json
```

```json
{
  "email": "asha@example.com",
  "password": "UserPass123"
}
```

The successful response provides a JWT access token.

Use the token for protected endpoints:

```http
Authorization: Bearer <ACCESS_TOKEN>
```

# 🩺 Health Check

The API provides a simple health check endpoint.

```http
GET /health
```

Example response:

```json
{
  "status": "ok"
}
```

---

# 🐳 Running with Docker

## Prerequisites

Make sure the following are installed:

- Git
- Docker
- Docker Compose

Local PostgreSQL installation is not required because PostgreSQL runs inside Docker.

## 1. Clone the Repository

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd eve-healthcare-backend
```

## 2. Create Environment File

Copy the example environment file:

```bash
cp .env.example .env
```

Update the environment variables if required.

> Never commit your `.env` file to GitHub.

## 3. Start the Application

```bash
docker compose up --build
```

The API will be available at:

```text
http://localhost:8000
```

# 📚 API Documentation

FastAPI automatically provides interactive Swagger documentation.

Open:

```text
http://localhost:8000/docs
```

You can test the APIs directly from Swagger UI.

---

# 🧪 Testing

The project uses **Pytest** for automated testing.

Run:

```bash
pytest
```

For verbose output:

```bash
pytest -v
```

---

# 🔄 API Testing Flow

A typical API workflow is:

```text
Health Check
     │
     ▼
Signup / Login
     │
     ▼
Receive JWT Token
     │
     ▼
Get Diagnostic Centres
     │
     ▼
Get Diagnostic Tests
     │
     ▼
Create Booking
     │
     ▼
Process Payment
     │
     ▼
Update Booking Status
     │
     ▼
Process Payment Webhook
```

The APIs can be tested using:

- Swagger UI
- Postman

---

# 👤 Demo Credentials

## User

```text
Email: asha@example.com
Password: UserPass123
```

## Admin

```text
Email: admin@eve-healthcare.com
Password: AdminPass123
```

These credentials are intended for local development and testing.

# ⚠️ Edge Cases Handled

The backend considers several real-world edge cases:

- Invalid request data
- Invalid booking IDs
- Unauthorized access
- Invalid authentication
- Failed payments
- Repeated payment webhooks
- Duplicate payment events
- Resource ownership
- Invalid booking operations

---

# 🔐 Security

The application includes:

- Password hashing
- JWT-based authentication
- Protected endpoints
- Authorization checks
- Request validation
- Environment-based configuration for secrets
- Foreign-key constraints
- `.env` excluded from Git

---

# 🧠 Engineering Decisions

## FastAPI

FastAPI was selected for its:

- Automatic OpenAPI documentation
- Request validation
- Type hints
- High-performance asynchronous capabilities
- Simple API development

## PostgreSQL

PostgreSQL provides:

- Relational data modeling
- Foreign-key constraints
- Transaction support
- Data integrity

## JWT Authentication

JWT tokens are used to authenticate users and protect API endpoints.

## Idempotent Webhooks

Payment webhooks use a unique provider event identifier to prevent duplicate processing when the same event is delivered multiple times.

## Docker

Docker and Docker Compose provide a consistent development environment for the API and PostgreSQL database.

---

# 📌 Assumptions

- Payments are simulated and do not use a real payment gateway.
- Demo credentials are provided only for local/testing purposes.
- PostgreSQL is used as the primary database.
- Booking amounts are tied to the selected diagnostic test.
- Payment webhook events contain a unique event identifier.
- JWT is used for authentication.
- Docker Compose is used to run the application and database.

# 🚀 Future Improvements

With additional development time, the following could be added:

- Redis caching
- Background jobs
- Celery integration
- Rate limiting
- Pagination
- Payment retry handling
- CI/CD pipeline
- Improved observability and monitoring
- Structured logging

# 🏁 Quick Start

Clone the repository:

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd eve-healthcare-backend
```

Create the environment file:

```bash
cp .env.example .env
```

Build and start the application using Docker:

```bash
docker compose up --build
```

The API will be available at:

```text
http://localhost:8000
```

Open Swagger UI to test the APIs:

```text
http://localhost:8000/docs
```

To stop the application:

```bash
docker compose down
```

# 👩‍💻 Developed By 

**Megha Sainia**  

---

# ⭐ Star the Repository

If you find this project useful, consider giving the repository a ⭐ star!

Thank you for checking out the project! 🚀
