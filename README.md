# 🎰 Lottery Management System

A production-ready lottery management system with Django REST API, React admin panel, React Native mobile app, and Telegram customer bot.

## Architecture

```
                    ┌──────────────────────┐
                    │   React Admin Web    │
                    └──────────┬───────────┘
                               │ REST API
                               ▼
                    ┌──────────────────────┐
                    │    Django REST API   │
                    │  Business Logic      │
                    │  Authentication      │
                    │  Lottery Management  │
                    │  Ticket Management   │
                    │  Payment Management  │
                    │  Draw Management     │
                    └──────────┬───────────┘
                               │
                 ┌─────────────┼─────────────┐
                 ▼             ▼             ▼
          PostgreSQL         Redis      Telegram Bot
                                             │
                                             ▼
                                         Customers

                    ┌──────────────────────┐
                    │ React Native Mobile  │
                    │     (Staff App)      │
                    └──────────┬───────────┘
                               │
                               ▼
                         Django REST API
```

## Technology Stack

| Component | Technology |
|-----------|-----------|
| Backend | Django, Django REST Framework, PostgreSQL, Redis, Celery |
| Auth | JWT (SimpleJWT) |
| Web Admin | React, TypeScript, Vite, Tailwind CSS, shadcn/ui |
| Mobile | React Native, Expo, TypeScript |
| Bot | Python Telegram Bot |
| Docs | Swagger / OpenAPI (drf-spectacular) |

## Requirements

- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Node.js 18+
- Docker (optional, for deployment)

---

## Backend Setup

### 1. Create and activate virtual environment

```bash
cd backend
python -m venv venv

# Windows
.\venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

```bash
# Copy the example and edit it
cp ../.env.example .env

# Edit .env with your database credentials, secret key, etc.
```

Required variables:
- `SECRET_KEY` — Django secret key
- `DATABASE_URL` — PostgreSQL connection string
- `REDIS_URL` — Redis connection string
- `TELEGRAM_BOT_TOKEN` — Your Telegram bot token

### 4. Create PostgreSQL database

```sql
CREATE DATABASE lottery_db;
CREATE USER lottery_user WITH PASSWORD 'lottery_pass';
GRANT ALL PRIVILEGES ON DATABASE lottery_db TO lottery_user;
ALTER USER lottery_user CREATEDB;  -- needed for running tests
```

### 5. Run migrations

```bash
python manage.py migrate
```

### 6. Create super admin

```bash
python manage.py create_superadmin
```

Default credentials (configurable via env vars):
- Email: `admin@lottery.com`
- Password: `admin123456`

### 7. Start the development server

```bash
python manage.py runserver
```

### 8. Access API documentation

- Swagger UI: http://localhost:8000/api/docs/
- ReDoc: http://localhost:8000/api/redoc/

---

## Running Tests

```bash
cd backend
python -m pytest apps/ -v
```

---

## User Roles

| Role | Permissions |
|------|-----------|
| Super Admin | Full access to everything |
| Lottery Manager | Create/edit lotteries, manage tickets, view reports |
| Payment Officer | Verify, approve, or reject payments |
| Draw Officer | Close sales, conduct draws, view winners |
| Viewer | Read-only access |

---

## API Endpoints (Phase 1)

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/login/` | Login with email/password |
| POST | `/api/auth/refresh/` | Refresh access token |
| POST | `/api/auth/change-password/` | Change password |

### Users
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/users/` | List users |
| POST | `/api/users/` | Create user (Super Admin) |
| GET | `/api/users/{id}/` | Get user details |
| PATCH | `/api/users/{id}/` | Update user (Super Admin) |
| DELETE | `/api/users/{id}/` | Deactivate user (Super Admin) |
| GET | `/api/users/me/` | Current user profile |
| PATCH | `/api/users/me/` | Update profile |

### Audit Logs
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/audit-logs/` | List audit logs (Super Admin) |
| GET | `/api/audit-logs/{id}/` | Get audit log details |

---

## Project Structure

```
lottery-app/
├── backend/
│   ├── config/              # Django project settings
│   │   ├── settings.py
│   │   ├── urls.py
│   │   ├── wsgi.py
│   │   ├── asgi.py
│   │   └── celery.py
│   ├── apps/
│   │   ├── accounts/        # Users & roles (Phase 1)
│   │   ├── audit_logs/      # Audit trail (Phase 1)
│   │   ├── lotteries/       # Lottery management (Phase 2)
│   │   ├── tickets/         # Ticket management (Phase 2)
│   │   ├── reservations/    # Ticket reservations (Phase 2)
│   │   ├── payments/        # Payment processing (Phase 3)
│   │   ├── draws/           # Draw system (Phase 4)
│   │   ├── winners/         # Winner management (Phase 4)
│   │   ├── notifications/   # Notifications (Phase 5)
│   │   ├── reports/         # Reporting (Phase 6)
│   │   └── telegram_bot/    # Telegram bot (Phase 5)
│   ├── requirements.txt
│   ├── manage.py
│   └── pytest.ini
├── web/                     # React admin panel (Phase 6)
├── mobile/                  # React Native staff app (Phase 7)
├── .gitignore
├── .env.example
└── README.md
```

---

## Development Phases

1. ✅ **Phase 1** — Backend Foundation (Users, Auth, Audit Logs)
2. 🔲 **Phase 2** — Lottery & Ticket System
3. 🔲 **Phase 3** — Payment System
4. 🔲 **Phase 4** — Draw System
5. 🔲 **Phase 5** — Telegram Bot
6. 🔲 **Phase 6** — Web Admin Panel
7. 🔲 **Phase 7** — Mobile App
8. 🔲 **Phase 8** — Testing & QA
9. 🔲 **Phase 9** — Deployment

---

## License

Private — All rights reserved.
