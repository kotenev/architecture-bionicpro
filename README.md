# BionicPRO Architecture Project

## Overview

BionicPRO is a Russian company that produces and sells bionic prosthetics. This project implements a comprehensive architecture solution for managing user authentication, data collection from prosthetic devices, and generating reports. The system addresses security vulnerabilities discovered after a previous breach and implements enhanced data privacy controls.

## Security Configuration

### Environment Variables Setup

Before running the application, you need to set up the environment variables:

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit the `.env` file to add your actual values:
   ```bash
   # Generate a new Fernet key for Airflow
   python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
   ```

3. Update the `.env` file with your generated key and other credentials.

### Important Security Notes

- The `AIRFLOW__CORE__FERNET_KEY` is used to encrypt sensitive data in Airflow, such as connection passwords.
- Never commit the `.env` file to the repository. It's already included in `.gitignore`.
- For production deployments, use a secrets management system (HashiCorp Vault, AWS Secrets Manager, etc.).

## Running the Application

### Prerequisites
- Docker and Docker Compose
- Python 3.8+

### Setup Instructions

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd architecture-bionicpro
   ```

2. Set up environment variables (see above)

3. Build and start the services:
   ```bash
   docker-compose up -d
   ```

4. Access the services:
   - Frontend: http://localhost:3000
   - Keycloak Admin: http://localhost:8080
   - Airflow UI: http://localhost:8081 (admin/admin)
   - ClickHouse HTTP: http://localhost:8123

## Architecture Components

- **Authentication Layer**: Keycloak with OAuth 2.0 and PKCE
- **Backend Services**: Flask-based authentication service
- **Database Layer**: PostgreSQL for operational data, ClickHouse for analytics
- **ETL Pipeline**: Apache Airflow for data processing
- **Frontend**: React/TypeScript application

## Data Pipeline

The system implements an ETL process that:
1. Extracts customer data from CRM PostgreSQL
2. Extracts telemetry data from Telemetry PostgreSQL
3. Transforms and joins the datasets
4. Loads the results to ClickHouse for reporting