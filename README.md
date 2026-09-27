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
