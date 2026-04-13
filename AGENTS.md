# Academic Peer Review System — Project Context

## Project motive
Build a modular Django application for academic peer review workflows on a local PC. The system supports the full lifecycle: course setup → enrollment → assignment → submission → rubric-based peer review → grade calculation → result release.

## Tech stack
- **Django 5** (class-based views throughout)
- **PostgreSQL** (via `psycopg2`)
- **Bootstrap 5** + **Bootstrap Icons 1.11**
- **python-dotenv** for environment loading
- No additional JS frameworks; vanilla Bootstrap JS bundle

---

## Active apps

| App | Responsibility |
|-----|----------------|
| `accounts` | Custom user model, roles, login/logout, role-based dashboards with live statistics |
| `courses` | Course CRUD, enrollment management |
| `assignments` | Assignment CRUD scoped to courses |
| `submissions` | File-upload submission per student per assignment |
| `rubrics` | Rubric and criteria management (one rubric per assignment) |
| `reviews` | Reviewer allocation, anonymous peer review submission |
| `grading` | Final grade calculation, GPA mapping, reviewer accuracy, feedback release |

---

## Auth and roles

- Custom user model: `accounts.User` (extends `AbstractUser`)
- Role field values: `ADMIN`, `INSTRUCTOR`, `STUDENT`
- `reg_no` field on `User`: mandatory for students, null for instructors/admins, normalised to uppercase + stripped on `save()`
- Django auth used for login/logout. Logout is POST-based (no GET) to avoid 405.
- All user creation is done by admins via Django admin panel (no self-registration).

### Role gate mixin
`accounts/mixins.py → RoleRequiredMixin` — used on every protected view.

---

## Dashboard routing

| URL | Role | Redirects to |
|-----|------|--------------|
| `/accounts/dashboard/` | any | role-specific dashboard |
| `/accounts/dashboard/admin/` | ADMIN | admin stats + quick links |
| `/accounts/dashboard/instructor/` | INSTRUCTOR | course/assignment stats + upcoming deadlines |
| `/accounts/dashboard/student/` | STUDENT | enrolled courses, pending reviews, released grades + upcoming deadlines |

Each dashboard view queries live statistics in `get_context_data` (lazy imports to avoid circular deps).

---

## Ownership and visibility constraints

- **Instructors** can only view/manage their own courses, create assignments under their own courses, and enroll students in their own courses.
- **Students** see only courses they are enrolled in, and only assignments for those courses.
- **Review anonymity**: reviewers never see author identity; students never see reviewer identity. Token-based URL (`anonymous_token` UUID) for review access.

---

## Domain models (current state)

### `accounts`
- `User` — `role`, `reg_no` (unique, null for non-students)

### `courses`
- `Course` — `code` (unique), `title`, `description`, `instructor`
- `Enrollment` — `course`, `student`, `enrolled_at`; unique on `(course, student)`

### `assignments`
- `Assignment` — `course`, `title`, `description`, `due_date`

### `submissions`
- `Submission` — `assignment`, `student`, `file` (upload to `submissions/assignment_<id>/<reg_no>/`), `content`, `status` (SUBMITTED / LATE), `submitted_at`, `updated_at`; unique on `(assignment, student)`

### `rubrics`
- `Rubric` — OneToOne → `Assignment`; `title`, `description`
- `RubricCriterion` — FK → `Rubric`; `criterion_name`, `criterion_description`, `max_marks`, `weight`, `order`

### `reviews`
- `ReviewAssignment` — FK `submission`, FK `reviewer`; `review_status` (PENDING/IN_PROGRESS/COMPLETED), `anonymous_token` (UUID, unique); unique on `(submission, reviewer)`; `clean()` prevents self-review
- `Review` — OneToOne → `ReviewAssignment`; `overall_comment`, `total_score` (sum of criterion scores), `submitted_at`
- `ReviewCriterionScore` — FK `review`, FK `RubricCriterion`; `score` (≥ 0), `comment`; unique on `(review, criterion)`

### `grading`
- `FinalGrade` — OneToOne → `Submission`; `numeric_score_100`, `letter_grade`, `gpa`, `grade_status` (CALCULATED/RELEASED), `calculated_at` (auto_now), `released_at`
- `ReviewerAccuracy` — OneToOne → `Review`; FK `reviewer`, FK `submission`; `deviation_from_average`, `accuracy_score` (100 − deviation, clamped to [0,100])

---

## Grade scale (`grading/grade_scale.py`)

Configurable list of `(threshold, letter, gpa)` tuples checked highest-first:

| Score | Grade | GPA |
|-------|-------|-----|
| ≥ 90  | A     | 4.00 |
| ≥ 80  | B     | 3.00 |
| ≥ 70  | C     | 2.00 |
| ≥ 60  | D     | 1.00 |
| ≥ 0   | F     | 0.00 |

Edit `GRADE_SCALE` in `grading/grade_scale.py` to change the mapping without touching business logic.

---

## Service layers

| Module | Key functions |
|--------|--------------|
| `reviews/services.py` | `allocate_reviewers(assignment)` — greedy balanced allocation (3 reviewers/submission); `delete_allocations(assignment)` |
| `grading/services.py` | `calculate_grades_for_assignment(assignment, force=False)` — normalises review totals to 0–100, averages them, maps to grade/GPA, computes reviewer accuracy; `release_grades(assignment)`; `unrelease_grades(assignment)` |

---

## URL map

### `/accounts/`
- `login/`, `logout/`, `profile/`
- `dashboard/`, `dashboard/admin/`, `dashboard/instructor/`, `dashboard/student/`

### `/courses/`
- `/` (role-aware redirect), `instructor/`, `student/`
- `create/`, `<id>/`, `<id>/enroll/`

### `/assignments/`
- `course/<course_id>/`, `course/<course_id>/create/`

### `/submissions/`
- `assignment/<assignment_id>/submit/` (student)
- `assignment/<assignment_id>/` (instructor list)

### `/rubrics/`
- `assignment/<assignment_id>/`, `assignment/<assignment_id>/create/`
- `assignment/<assignment_id>/criterion/add/`
- `criterion/<id>/edit/`, `criterion/<id>/delete/`

### `/reviews/`
- `assignment/<id>/allocate/` (instructor)
- `assignment/<id>/monitor/` (instructor)
- `inspect/<review_id>/` (instructor)
- `my/` (student review list)
- `<uuid:token>/` (student review form — anonymous)

### `/grading/`
- `assignment/<id>/` (instructor grade management)
- `assignment/<id>/accuracy/` (instructor reviewer accuracy)
- `my/` (student grade list)
- `submission/<id>/result/` (student result detail)

---

## UI conventions

- Templates are app-scoped under `templates/<app>/...`
- Global layout in `templates/base.html` (Bootstrap 5 + Bootstrap Icons CDN)
- Role-aware navbar with active-link highlighting via `request.resolver_match`
- Global flash messages rendered once in `base.html` (all per-template message blocks removed)
- Custom utilities in `static/css/main.css` (stat cards, status badges, empty states, deadline colours)
- Styling uses Bootstrap 5 + Bootstrap Icons; no extra JS frameworks

---

## Environment and settings

- `.env` loaded in `config/settings.py` via `python-dotenv`
- Key vars: `DJANGO_SECRET_KEY`, `DJANGO_DEBUG`, `DJANGO_ALLOWED_HOSTS`, `DJANGO_CSRF_TRUSTED_ORIGINS`
- DB vars: `DJANGO_DB_NAME`, `DJANGO_DB_USER`, `DJANGO_DB_PASSWORD`, `DJANGO_DB_HOST`, `DJANGO_DB_PORT`
- `AUTH_USER_MODEL = "accounts.User"` — must not change after migrations are applied
- `MEDIA_URL = "media/"`, `MEDIA_ROOT = BASE_DIR / "media"` — served via `static()` in DEBUG mode

---

## Admin panel notes

- `accounts/admin.py` — `UserAdmin` with custom forms (passwords hashed correctly); `reg_no` in all displays
- `courses/admin.py` — shows enrollment count per course, instructor full name
- `assignments/admin.py` — shows submission count, rubric boolean, date hierarchy
- `submissions/admin.py` — file download link, course display, has-file boolean
- `rubrics/admin.py` — `RubricCriterionInline` inside `RubricAdmin`
- `reviews/admin.py` — `ReviewAssignmentAdmin`, `ReviewAdmin` (with `ReviewCriterionScoreInline`), `ReviewCriterionScoreAdmin`
- `grading/admin.py` — `FinalGradeAdmin`, `ReviewerAccuracyAdmin`

---

## Development guardrails

1. Keep code modular by app responsibility — no cross-app business logic in views.
2. Preserve `RoleRequiredMixin` on every protected view; check `allowed_roles`.
3. Never expose reviewer identity to students (or author identity to reviewers).
4. Add migrations for every model change and keep migration files tracked in git.
5. Prefer class-based views for consistency.
6. All grading/allocation logic lives in `services.py` files, not in views.
7. `reg_no` normalisation happens in `User.save()` — do not bypass with `.update()`.
8. `media/` directory (uploaded files) is excluded from git via `.gitignore`.
9. `.env` is excluded from git — use `.env.example` as a template for new setups.
