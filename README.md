## Academic Peer Review System (Django)

Minimal, modular Django 5 project prepared for an academic peer review workflow, using PostgreSQL and Bootstrap 5.

### Features

- **Authentication foundation**: Django login/logout with a clean Bootstrap UI.
- **Role-based user model**: `accounts.User` extends Django’s `AbstractUser` with a `role` field (Admin / Instructor / Student).
- **Role-based dashboards**: separate dashboards for each role, protected by access control.
- **Core academic structure**: courses, enrollments, and assignments (no submissions/reviews yet).
- **PostgreSQL-ready** configuration via `.env` using `python-dotenv`.

### Requirements

- Python 3.11+ (recommended)
- PostgreSQL (local instance)

### Setup (Windows / local)

1. **Create & activate virtual environment**

   ```powershell
   cd d:\Peer-Review-Evaluation-System
   python -m venv .venv
   .\.venv\Scripts\activate
   ```

2. **Install dependencies**

   ```powershell
   pip install -r requirements.txt
   ```

3. **Configure PostgreSQL**

   Ensure you have a local PostgreSQL database and user, then set environment variables (or adjust `config/settings.py` directly for local-only use):

   ```powershell
   setx DJANGO_DB_NAME "peer_review_db"
   setx DJANGO_DB_USER "postgres"
   setx DJANGO_DB_PASSWORD "your-password"
   setx DJANGO_DB_HOST "localhost"
   setx DJANGO_DB_PORT "5432"
   ```

   The `DATABASES` setting in `config/settings.py` uses these values, falling back to the above defaults.

4. **Run migrations**

   ```powershell
   python manage.py makemigrations
   python manage.py migrate
   ```

5. **Create a superuser**

   ```powershell
   python manage.py createsuperuser
   ```

6. **Assign roles (sample setup)**

   - Log in to Django admin at `/admin/`.
   - Go to **Users** and edit your superuser (or create new users).
   - Set the **role** field to one of:
     - `ADMIN`
     - `INSTRUCTOR`
     - `STUDENT`

   Dashboards are role-protected:
   - `/accounts/dashboard/admin/`
   - `/accounts/dashboard/instructor/`
   - `/accounts/dashboard/student/`

7. **Instructor / Student flows (current scope)**

   - **Instructor**
     - Course list: `/courses/instructor/`
     - Create course: `/courses/create/`
     - Course detail: `/courses/<id>/`
     - Enroll student: `/courses/<id>/enroll/`
     - Course assignments: `/assignments/course/<course_id>/`
     - Create assignment: `/assignments/course/<course_id>/create/`

   - **Student**
     - Enrolled courses: `/courses/student/`
     - Course detail: `/courses/<id>/`
     - Course assignments: `/assignments/course/<course_id>/`

6. **Run the development server**

   ```powershell
   python manage.py runserver
   ```

   - Homepage: `http://127.0.0.1:8000/`
   - Login: `http://127.0.0.1:8000/accounts/login/`
   - Dashboard (auto-redirect by role): `http://127.0.0.1:8000/accounts/dashboard/`
   - Admin: `http://127.0.0.1:8000/admin/`

### Project structure (high level)

- **config**: Django project configuration (`settings.py`, `urls.py`, `wsgi.py`, `asgi.py`).
- **accounts**: Custom `User` model with `role`, login/logout, profile, dashboards, URL routing.
- **courses**: `Course` + `Enrollment` models, instructor/student course views and enrollment UI.
- **assignments**: `Assignment` model and course-scoped assignment list/create views.
- **templates**: Global templates including `base.html`, `home.html`, and app templates.
- **static**: Global static assets (`css/main.css`) with a light Bootstrap-based theme.

### Next steps / extension points

- **Role-based permissions**: use `User.role` in custom decorators/mixins to gate views (e.g., instructors only).
- **Business logic**: add courses/assignments/submissions/reviews/grading workflows (intentionally not implemented yet).
- **Testing**: add unit and integration tests per app (`tests.py` or test packages).
- **Production hardening**: separate `settings` modules for dev/prod, secret key management, proper logging, etc.

