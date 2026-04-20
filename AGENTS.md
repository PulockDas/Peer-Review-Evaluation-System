# Academic Peer Review System — Agent Context

## Project motive
Build a modular Django application for academic peer review workflows on a local PC.
Full lifecycle: course setup → enrollment → assignment → submission → rubric-based peer review → grade calculation → result release.

All features are **fully implemented and committed**. The system is demo-ready.

---

## Tech stack
| Item | Detail |
|------|--------|
| Django | 5.x — class-based views throughout |
| Database | PostgreSQL (`psycopg2`) |
| Frontend | Bootstrap 5 + Bootstrap Icons 1.11 (CDN) |
| Env loading | `python-dotenv` |
| JS | Vanilla Bootstrap bundle only — no React/Vue/Alpine |

---

## App map

| App | `app_name` (URL namespace) | Responsibility |
|-----|---------------------------|----------------|
| `accounts` | `accounts` | Custom User model, roles, login/logout, role dashboards with live stats |
| `courses` | `courses` | Course CRUD, enrollment management |
| `assignments` | `assignments` | Assignment CRUD scoped to courses |
| `submissions` | `submissions` | File-upload submission (one per student per assignment) |
| `rubrics` | `rubrics` | Rubric + criteria CRUD (one rubric per assignment via OneToOneField) |
| `reviews` | `reviews` | Reviewer allocation, anonymous peer review submission |
| `grading` | `grading` | Grade calculation, GPA mapping, reviewer accuracy, feedback release |

Project package: `config` (`config/settings.py`, `config/urls.py`).

---

## Auth and roles

- Custom user model: `accounts.User` (extends `AbstractUser`)
- `AUTH_USER_MODEL = "accounts.User"` — **must not change** after migrations are applied
- Role choices: `ADMIN`, `INSTRUCTOR`, `STUDENT`
- `reg_no` field: unique, null for non-students; normalised to `.strip().upper()` in `User.save()` (empty string → `None` for correct unique-index behaviour)
- Logout is POST-based — navbar uses a `<form method="post">` button
- **No self-registration** — all users are created by admins in the Django admin panel

### Role gate
`accounts/mixins.py → RoleRequiredMixin`  
Set `allowed_roles = (User.Roles.INSTRUCTOR,)` on any view that requires a specific role.
Unauthenticated → login redirect. Wrong role → `accounts:dashboard` redirect.

---

## Dashboard routing

| URL name | Redirects to | Role |
|----------|-------------|------|
| `accounts:dashboard` | role-specific dashboard | any authenticated |
| `accounts:dashboard_admin` | admin stats + quick links | ADMIN |
| `accounts:dashboard_instructor` | course/assignment stats + upcoming deadlines | INSTRUCTOR |
| `accounts:dashboard_student` | enrolled courses, pending reviews, released grades | STUDENT |

Each dashboard view has `get_context_data` with lazy imports (avoids circular deps).

---

## Ownership and visibility constraints

- **Instructors** — only their own courses, assignments under their own courses, enrollments in their own courses.
- **Students** — only enrolled courses, only assignments for enrolled courses.
- **Anonymity** — reviewers never see author identity; authors never see reviewer identity. URL access uses `anonymous_token` (UUID field on `ReviewAssignment`).

---

## Domain models

### `accounts`
```
User
  role          CharField (ADMIN / INSTRUCTOR / STUDENT)
  reg_no        CharField(50), unique, null=True — students only
```

### `courses`
```
Course
  code          CharField, unique
  title, description
  instructor    FK → User

Enrollment
  course        FK → Course
  student       FK → User
  enrolled_at   auto_now_add
  UNIQUE (course, student)
```

### `assignments`
```
Assignment
  course        FK → Course
  title, description
  due_date      DateTimeField
```

### `submissions`
```
Submission
  assignment    FK → Assignment
  student       FK → User
  file          FileField  (path: submissions/assignment_<id>/<reg_no>/<filename>)
  content       TextField (optional notes)
  status        SUBMITTED / LATE
  submitted_at  auto_now_add
  updated_at    auto_now
  UNIQUE (assignment, student)
```

### `rubrics`
```
Rubric
  assignment    OneToOneField → Assignment  (enforces one rubric per assignment)
  title, description
  created_at, updated_at

RubricCriterion
  rubric        FK → Rubric
  criterion_name, criterion_description
  max_marks     DecimalField  CHECK > 0
  weight        DecimalField  CHECK 0–100
  order         PositiveIntegerField
```

### `reviews`
```
ReviewAssignment
  submission    FK → Submission
  reviewer      FK → User
  review_status PENDING / IN_PROGRESS / COMPLETED
  anonymous_token  UUIDField, unique, editable=False
  assigned_at   auto_now_add
  UNIQUE (submission, reviewer)
  clean()  → raises ValidationError if reviewer == submission.student

Review
  review_assignment  OneToOneField → ReviewAssignment
  overall_comment    TextField
  total_score        DecimalField  (sum of criterion scores, stored on submit)
  submitted_at       auto_now_add

ReviewCriterionScore
  review        FK → Review
  criterion     FK → RubricCriterion
  score         DecimalField  CHECK ≥ 0
  comment       TextField
  UNIQUE (review, criterion)
```

### `grading`
```
FinalGrade
  submission    OneToOneField → Submission
  numeric_score_100  DecimalField (0–100)
  letter_grade       CharField(2)
  gpa                DecimalField(4,2)
  grade_status       CALCULATED / RELEASED
  calculated_at      auto_now
  released_at        DateTimeField, null=True

ReviewerAccuracy
  review        OneToOneField → Review
  reviewer      FK → User
  submission    FK → Submission
  deviation_from_average  DecimalField  (|reviewer_norm_score − final_avg|, 0–100 scale)
  accuracy_score          DecimalField  (100 − deviation, clamped [0,100])
  calculated_at  auto_now
```

---

## Grade scale (`grading/grade_scale.py`)

`GRADE_SCALE` — list of `(threshold, letter, gpa)` tuples, highest threshold first.
`get_grade(score: Decimal) → (letter, gpa)` iterates and returns first match.

| Score | Grade | GPA |
|-------|-------|-----|
| ≥ 90  | A | 4.00 |
| ≥ 80  | B | 3.00 |
| ≥ 70  | C | 2.00 |
| ≥ 60  | D | 1.00 |
| ≥ 0   | F | 0.00 |

---

## Service layers

### `reviews/services.py`
- `REVIEWS_PER_SUBMISSION = 3` — constant controlling reviewers per submission
- `allocate_reviewers(assignment)` — greedy workload-balanced allocation; raises `AllocationError` if too few eligible students
- `delete_allocations(assignment)` — removes all `ReviewAssignment` rows for the assignment

### `grading/services.py`
- `calculate_grades_for_assignment(assignment, force=False)`
  - Requires a rubric with `total_max_marks() > 0`
  - Requires ≥ `REVIEWS_PER_SUBMISSION` completed reviews per submission
  - Normalises each review: `(review.total_score / rubric_max) × 100`
  - Final score = mean of normalised scores (clamped 0–100)
  - Skips RELEASED grades unless `force=True`
  - Stores `FinalGrade` + `ReviewerAccuracy` for each eligible submission
  - Returns `(n_calculated, n_skipped)`
- `release_grades(assignment)` — bulk-updates CALCULATED → RELEASED, sets `released_at`
- `unrelease_grades(assignment)` — reverts RELEASED → CALCULATED, clears `released_at`

---

## URL map

### `accounts` namespace
```
login/                     accounts:login
logout/                    accounts:logout
profile/                   accounts:profile
dashboard/                 accounts:dashboard
dashboard/admin/           accounts:dashboard_admin
dashboard/instructor/      accounts:dashboard_instructor
dashboard/student/         accounts:dashboard_student
```

### `courses` namespace
```
/courses/                  courses:list         (role-aware redirect)
instructor/                courses:instructor_list
student/                   courses:student_list
create/                    courses:create
<id>/                      courses:detail
<id>/enroll/               courses:enroll
```

### `assignments` namespace
```
course/<course_id>/        assignments:list
course/<course_id>/create/ assignments:create
```

### `submissions` namespace
```
assignment/<id>/submit/    submissions:submit              (student)
assignment/<id>/           submissions:assignment_submissions  (instructor)
```

### `rubrics` namespace
```
assignment/<id>/           rubrics:detail
assignment/<id>/create/    rubrics:create
assignment/<id>/criterion/add/     rubrics:criterion_add
criterion/<id>/edit/       rubrics:criterion_edit
criterion/<id>/delete/     rubrics:criterion_delete
```

### `reviews` namespace
```
assignment/<id>/allocate/  reviews:allocate    (instructor — manage allocation)
assignment/<id>/monitor/   reviews:monitor     (instructor — completion monitor)
inspect/<review_id>/       reviews:review_inspect  (instructor — view one review)
my/                        reviews:my_reviews  (student — list of assigned reviews)
<uuid:token>/              reviews:review_form (student — anonymous review form)
```

### `grading` namespace
```
assignment/<id>/           grading:manage      (instructor — calculate/release)
assignment/<id>/accuracy/  grading:accuracy    (instructor — reviewer accuracy)
my/                        grading:my_grades   (student — released grade list)
submission/<id>/result/    grading:result      (student — grade + anonymous feedback)
```

---

## Template structure

```
templates/
  base.html                   — Bootstrap 5 navbar (role-aware, active links), global flash
                                messages, Bootstrap Icons, footer
  home.html                   — landing page (hero + feature cards + workflow stepper)
  accounts/
    login.html
    profile.html
    dashboard_admin.html      — stat cards (users, courses, submissions, etc.)
    dashboard_instructor.html — stat cards + upcoming deadlines table
    dashboard_student.html    — stat cards + upcoming deadlines + quick links
  courses/  assignments/  submissions/  rubrics/  reviews/  grading/
    (all app-scoped templates)
```

> **Leftover placeholders** (do not rely on these):
> - `templates/grading/dashboard.html` — old placeholder, not routed to any view
> - `templates/reviews/review_list.html` — old placeholder, not used

---

## UI conventions

- Flash messages are rendered **once** in `base.html`. Do **not** add per-template message loops.
- Active nav links detected via `request.resolver_match.app_name` / `.url_name` in `{% with %}` block.
- `static/css/main.css` provides: `.stat-card`, `.stat-number`, `.stat-label`, `.badge-pending`, `.badge-submitted`, `.badge-completed`, `.badge-calculated`, `.badge-released`, `.empty-state`, `.deadline-urgent`, `.deadline-soon`, `.page-title`, `.page-subtitle`.
- Confirm dialogs on destructive buttons use `onclick="return confirm('...')"`.

---

## Environment and settings

```
DJANGO_SECRET_KEY
DJANGO_DEBUG
DJANGO_ALLOWED_HOSTS
DJANGO_CSRF_TRUSTED_ORIGINS
DJANGO_DB_NAME, DJANGO_DB_USER, DJANGO_DB_PASSWORD, DJANGO_DB_HOST, DJANGO_DB_PORT
DJANGO_LANGUAGE_CODE, DJANGO_TIME_ZONE
```

- `MEDIA_URL = "media/"`, `MEDIA_ROOT = BASE_DIR / "media"` — served via `static()` in DEBUG
- `.env` is **git-ignored**. Use `.env.example` as template for new setups.
- `media/` is **git-ignored** — uploaded submission files must not be committed.

---

## Admin panel

| Admin class | Key features |
|-------------|-------------|
| `UserAdmin` | custom forms (hashed passwords), `reg_no` in list/search/fieldsets |
| `CourseAdmin` | enrollment count method, instructor full name |
| `EnrollmentAdmin` | student name + reg_no display, ordered by `enrolled_at` |
| `AssignmentAdmin` | submission count, rubric boolean, `date_hierarchy` |
| `SubmissionAdmin` | file link, course column, `has_file` boolean |
| `RubricAdmin` | `RubricCriterionInline` (tabular) |
| `ReviewAssignmentAdmin` | author + assignment + course display columns |
| `ReviewAdmin` | `ReviewCriterionScoreInline` |
| `ReviewCriterionScoreAdmin` | standalone review of individual scores |
| `FinalGradeAdmin` | student, assignment, course, score, grade, status, timestamps |
| `ReviewerAccuracyAdmin` | reviewer, author, accuracy, deviation |

---

## Migrations (applied, all tracked in git)

| App | Migrations |
|-----|-----------|
| `accounts` | `0001_initial`, `0002_user_reg_no` |
| `courses` | `0001_initial` |
| `assignments` | `0001_initial` |
| `submissions` | `0001_initial`, `0002_submission_file_submission_status_and_more` |
| `rubrics` | `0001_initial` |
| `reviews` | `0001_initial`, `0002_reviewassignment`, `0003_rework_review_add_reviewcriterionscore` |
| `grading` | `0001_initial` (creates `FinalGrade` + `ReviewerAccuracy`; old `Grade` model dropped) |

---

## Development guardrails

1. Keep code modular — no cross-app business logic in views; use `services.py`.
2. Apply `RoleRequiredMixin` with `allowed_roles` on every non-public view.
3. **Never** expose reviewer identity to students or author identity to reviewers.
4. Add a migration for every model change; keep migration files tracked in git.
5. Use class-based views; keep views thin — logic belongs in services or models.
6. `reg_no` normalisation is in `User.save()` — never bypass it with `.update()`.
7. Do **not** add flash messages in individual templates — `base.html` handles them globally.
8. `media/` and `.env` are git-ignored — never force-add them.
9. When adding new features, integrate through the course → enrollment boundary and respect the role/ownership checks already in place.
