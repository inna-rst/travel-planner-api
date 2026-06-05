# Travel Planner API

A RESTful REST API service for managing travel projects and places, integrated with the Art Institute of Chicago API.

## Features
* **Project Management:** Create, list, update, and delete travel projects.
* **Third-party API Integration:** Fetch and validate artwork/places data from the Art Institute of Chicago API.
* **Business Logic:** * A project can contain a maximum of 10 unique places.
  * Projects containing visited places cannot be deleted.
  * Places cannot be "unmarked" once visited.
  * Auto-calculated `is_completed` status at the database level for optimized performance.
* **Optimized Architecture:** Eliminated N+1 queries using `prefetch_related` and complex database annotations. Network calls are processed outside of database transactions to prevent locking.
* **Basic Authentication & Pagination.**

## Technology Stack
* Python 3.13
* Django & Django REST Framework
* PostgreSQL
* Docker & Docker Compose
* httpx (for async-friendly API requests)
* django-environ

## Quick Start (Docker)

1. **Clone the repository and build the container:**
   ```bash
   docker-compose up --build -d
   
2. **Create a user for Basic Authentication:**
   ```bash
   docker-compose exec web python manage.py createsuperuser
   
2. **Access the API:**
   * Browsable API: http://127.0.0.1:8000/api/v1/projects/
   * To test endpoints, use the provided Postman collection.