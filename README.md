# Movies Store

A full-stack Django web application for browsing, reviewing and purchasing movies. Users can create an account, search the catalog, leave and manage reviews, add movies to a session-based cart, and check out to create an order they can view in their order history.

**Live demo:** [ADD YOUR PYTHONANYWHERE URL HERE]

> **About this project:** Built as a semester project following *Django 5 for the Impatient, 2nd Edition* (Correa & Lim, Packt 2024), which covers the catalog, authentication, review CRUD, and the cart and order flow. I extended the book's application with a community review-moderation system of my own design — see [Extension: review moderation](#extension-review-moderation).

<!-- Add a screenshot of the movie listing page here, e.g.: -->
<!-- ![Movie catalog](docs/screenshots/catalog.png) -->

---

## Features

**Accounts**
- User signup with a custom registration form and custom error rendering
- Login / logout backed by Django's authentication framework
- Per-user order history

**Movies & reviews**
- Movie catalog with case-insensitive title search
- Movie detail pages with image, price and description
- Full review CRUD, with ownership checks so users can only edit or delete their own reviews

**Cart & orders**
- Session-based shopping cart that persists across requests without requiring login
- Add items with quantity, view a running total, clear the cart
- Authenticated checkout that converts the cart into an `Order` with line-item `Item` records

**Review moderation** *(my extension — see below)*
- Any authenticated user can report another user's review as inappropriate
- Reports are recorded as rows, deduplicated per user by a database constraint
- Reported reviews are soft-hidden rather than deleted, and reversible from the Django admin

---

## Extension: review moderation

> *As a user, I want to report inappropriate reviews so that the comment section isn't cluttered with irrelevant or offensive reviews, and the review is removed from the page moving forward.*

The book's review system is built on ownership: only the author can edit or delete a review. Reporting breaks that model, because the actor is any logged-in user *except* the author. Rather than loosening the existing delete view, I designed a separate moderation path modeled on [`django-contrib-comments`](https://github.com/django/django-contrib-comments) — Django's own comment-flagging library, which shipped inside Django core as `django.contrib.comments` through version 1.5.

**Design decisions**

| Decision | Why |
|---|---|
| Soft delete (`is_removed = True`) rather than `.delete()` | Reporting is about visibility, not destruction. A spiteful report or a misclick is reversible; the row survives for review. |
| A separate `ReviewFlag` table rather than a counter on `Review` | An integer tells you *how many*, a row per report tells you *who*. Enables abuse detection, moderator views, and a future report threshold — the count is still available via `review.flags.count()`. |
| `unique_together = [('user', 'review', 'flag')]` | Enforces one-report-per-user at the **database** level, so a bug in the view or a race between simultaneous requests still cannot create a duplicate. |
| `get_or_create` in the view | A repeat report returns the existing row instead of raising `IntegrityError` and surfacing a 500 to the user. |
| `flag` as an indexed `CharField`, not a boolean | Flag *type* is a column, so adding moderator approval or moderator deletion later is a new constant rather than a new table. |
| `@require_POST` + a form with `{% csrf_token %}` | A state-changing action must not be reachable by GET, where a prefetcher, link scanner or hostile `<img src>` could fire it without the user clicking anything. |
| Decorator order: `@login_required` above `@require_POST` | Decorators apply bottom-up, so the auth check runs outermost. An anonymous user gets redirected to login rather than a bare `405 Method Not Allowed`. |
| `get_object_or_404(Review, id=review_id, movie_id=id)` | Filtering on both means a hand-edited URL can't report a review belonging to a different movie. Using `movie_id` rather than `movie` avoids a second query for an object the view never uses. |
| `redirect` rather than `render` | Post/Redirect/Get: the browser's final URL is a GET, so a refresh re-requests the movie page instead of replaying the report. |

**Enforcement** is a single line in the movie detail view — `Review.objects.filter(movie=movie, is_removed=False)`. The row stays in the database; the query feeding the template never selects it.

**Known limitations**, deliberately left in scope:

- One report hides a review. There's no threshold, so a single user can suppress anything. The flag table makes the fix trivial — count rows against a constant — but as shipped it's one click.
- No moderator queue in the UI. Reversal happens by unchecking `is_removed` in the Django admin, and the `MODERATOR_DELETION` constant exists for a path not yet built.
- Filtering isn't centralized. Any future view listing reviews must remember `is_removed=False`; a custom `Manager` whose default queryset excludes removed rows would make forgetting impossible.
- Reports carry no reason field, and the review's author isn't notified. The upstream library emits a `comment_was_flagged` signal for this; I left it out since nothing would listen yet.

---

## Tech stack

| Layer | Technology |
|---|---|
| Language | Python |
| Framework | Django |
| Database | SQLite |
| Templates | Django Template Language |
| Styling | HTML / CSS, Bootstrap |
| Hosting | PythonAnywhere |

---

## Data model

```
Movie
  ├── name, price, description, image
  │
  ├── Review (FK: movie, user)
  │     └── comment, date, is_removed
  │           │
  │           └── ReviewFlag (FK: review, user)
  │                 └── flag, flag_date
  │                     UNIQUE (user, review, flag)
  │
  └── Item (FK: movie, order)
        └── price, quantity

Order (FK: user)
  └── total, line items
```

---

## Routes

| Method | Path | Description |
|---|---|---|
| GET | `/` | Home page |
| GET | `/movies/` | Movie catalog, with optional `?search=` filter |
| GET | `/movies/<id>/` | Movie detail page with reviews |
| POST | `/movies/<id>/review/create/` | Create a review (auth required) |
| GET, POST | `/movies/<id>/review/<review_id>/edit/` | Edit your own review (auth required) |
| POST | `/movies/<id>/review/<review_id>/delete/` | Delete your own review (auth required) |
| POST | `/movies/<id>/review/<review_id>/report/` | Report a review as inappropriate (auth required) |
| GET | `/cart/` | View cart and total |
| POST | `/cart/add/<id>/` | Add a movie to the cart |
| POST | `/cart/clear/` | Empty the cart |
| POST | `/cart/purchase/` | Check out and create an order (auth required) |
| GET | `/accounts/signup/` | Register a new account |
| GET, POST | `/accounts/login/` | Log in |
| GET | `/accounts/logout/` | Log out |
| GET | `/accounts/orders/` | Order history (auth required) |

<!-- Double-check the cart and accounts paths against your urls.py and fix any that differ. -->

---

## Running locally

```bash
# 1. Clone the repository
git clone https://github.com/cindy-muniz/moviesstore.git
cd moviesstore

# 2. Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set environment variables
cp .env.example .env             # then edit .env and set SECRET_KEY

# 5. Apply migrations
python manage.py migrate

# 6. Create an admin account
python manage.py createsuperuser

# 7. Run the development server
python manage.py runserver
```

The app runs at `http://127.0.0.1:8000/`, and the admin panel at `http://127.0.0.1:8000/admin/`.

---

## Project structure

```
moviesstore/
├── accounts/       # Signup, login, logout, order history
├── cart/           # Session cart, checkout, Order and Item models
├── home/           # Landing page
├── movies/         # Catalog, search, reviews, review moderation
├── moviesstore/    # Project settings and root URL config
├── media/          # Uploaded movie images
└── manage.py
```

---

## Roadmap

- Move review flagging to a threshold model, hiding a review after N independent reports rather than one
- Add a custom `Manager` on `Review` so removed reviews are excluded by default
- Add a pytest suite covering cart total calculation, review ownership checks and the report flow
- Add a GitHub Actions workflow running tests on every pull request
- Replace raw `request.POST[...]` access in the review and cart views with Django forms
- Migrate from SQLite to PostgreSQL for a production-ready deployment

---

## Credits

Core application built following *Django 5 for the Impatient, 2nd Edition* by Daniel Correa and Greg Lim (Packt, 2024). The review moderation system is my own, adapted from the flagging model in [`django-contrib-comments`](https://github.com/django/django-contrib-comments) (BSD licensed).
