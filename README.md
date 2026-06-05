# Travel Planner API

![Python](https://img.shields.io/badge/python-3.12-blue.svg)
![Django](https://img.shields.io/badge/django-5-green.svg)
![DRF](https://img.shields.io/badge/DRF-red.svg)
![PostgreSQL](https://img.shields.io/badge/postgresql-blue.svg)
![Docker](https://img.shields.io/badge/docker-blue.svg)

A RESTful API service for managing travel projects and collecting places travelers want to visit. The application integrates with the Art Institute of Chicago API to validate and import artwork destinations.

---

## ✨ Features

### Core Functionality
* **Travel Projects:** Create, list, retrieve, update, and delete travel projects.
* **Smart Completion:** A project is automatically considered completed when all associated places are marked as visited (calculated dynamically at the database level).
* **Places Management:** Add places to a project, update personal notes, and mark places as visited.
* **Third-Party Integration:** Seamlessly imports and validates artwork metadata from the Art Institute of Chicago API.

### Business Rules & Constraints
* A project can contain a maximum of **10 places**.
* Duplicate places are **not allowed** within the same project.
* Projects containing visited places **cannot be deleted**.
* A visited place **cannot be reverted** back to unvisited.

### Bonus Features Implemented
* **Dockerized Environment:** One-command setup using Docker and Docker Compose.
* **Basic Authentication:** API endpoints are secured. Only authorized users can manage projects.
* **Pagination & Filtering:** Built-in DRF pagination and query parameter filtering (e.g., by completion status and name).
* **Caching:** External API responses are cached to reduce latency and rate-limiting issues.

---

## 🛠️ Technology Stack
* **Language:** Python 3.12+
* **Framework:** Django 5, Django REST Framework (DRF)
* **Database:** PostgreSQL
* **Infrastructure:** Docker, Docker Compose, Gunicorn
* **External HTTP:** HTTPX
* **Caching:** Django Cache Framework

---

## 🚀 Quick Start & Setup

**1. Configure Environment:**
Create a `.env` file in the project root to allow the database to start correctly:

```env
DB_NAME=travel_planner
DB_USER=travel_user
DB_PASSWORD=travel_password

DJANGO_SECRET_KEY=dev-secret-key-do-not-use-in-production
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0
```

**2. Build and start the containers:**
The database migrations will be applied automatically on startup:

```bash
    docker-compose up --build -d
```

**3. Create a user for authentication:**
Since the API is secured, you need to create a user to authenticate your requests:

```bash
    docker-compose exec web python manage.py createsuperuser
```

**4. Access the API & Testing:**
* **Browsable API:** `http://localhost:8000/api/v1/projects/`
* **Postman:** Download the [Postman Collection](./Travel_Planner.postman_collection.json) included in the repository to test all endpoints. *(Make sure to enter your superuser credentials in the Basic Auth tab).*

---

## 📖 API Documentation

### Endpoints Overview

#### Projects
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/v1/projects/` | List projects (Paginated) |
| `POST` | `/api/v1/projects/` | Create a new project |
| `GET` | `/api/v1/projects/{id}/` | Retrieve project details |
| `PATCH` | `/api/v1/projects/{id}/` | Partial project update |
| `DELETE` | `/api/v1/projects/{id}/` | Delete project |

**Filtering Projects:**
* `GET /api/v1/projects/?is_completed=true` (Completed only)
* `GET /api/v1/projects/?is_completed=false` (Active only)
* `GET /api/v1/projects/?name=chicago` (Search by name)

#### Places
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/v1/projects/{project_id}/places/` | List places within a project |
| `POST` | `/api/v1/projects/{project_id}/places/` | Add a validated place to a project |
| `GET` | `/api/v1/projects/{project_id}/places/{place_id}/` | Retrieve place details |
| `PATCH` | `/api/v1/projects/{project_id}/places/{place_id}/` | Update notes or mark as visited |

----
