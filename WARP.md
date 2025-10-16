# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

Project overview
- Stack: Django 4.2 (Python >= 3.12) with PostgreSQL, Tailwind CSS via PostCSS. Live reload is enabled with django-browser-reload. Tailwind assets are managed in theme/static_src and emitted to theme/static/css/dist/.
- Apps and routing:
  - daycare: project config (settings/urls/wsgi/asgi). URLs include: / (nursery), /daycare/ (daycare_ambassadeurs), /blog/ (blog), __reload__/ (browser reload), and a reference to /primaire/.
  - blog: blog app with models/migrations, templates/blog/*, static assets, and two custom management commands (create_admin, migrate_article_styles).
  - daycare_ambassadeurs: site pages, templates/daycare_ambassadeurs/*, static assets.
  - nursery: default landing routes at root.
  - theme: Tailwind integration (templates/base.html, components/_footer.html) and the asset pipeline under static_src (postcss/tailwind configs).
- Notable caveat: settings and urls reference a primaire app that is not present in the repository; those routes will 404 until that app is added or the references are removed.

Common commands
Note: Use a virtual environment for Python and install dependencies from pyproject.toml. The examples assume you’re at the repo root (/home/zecustomizer/projects/ambassadors/daycare).

Python setup and dependencies
- Create venv and activate (bash):
  - python -m venv .venv && source .venv/bin/activate
- Install Python deps defined in pyproject.toml:
  - pip install -e .

Database and migrations
- Apply migrations:
  - python manage.py migrate
- Create an admin user (either standard or via app command):
  - python manage.py createsuperuser
  - python manage.py create_admin

Run the app (development)
- Start Django dev server:
  - python manage.py runserver
- Live reload is wired via django-browser-reload at path __reload__/; no extra command is required beyond running the server and your asset watcher.

Frontend assets (Tailwind/PostCSS)
- Install Node deps for the theme (no cd needed):
  - npm --prefix ./theme/static_src ci
- Development watch (writes CSS to theme/static/css/dist/styles.css):
  - npm --prefix ./theme/static_src run dev
- Production build:
  - npm --prefix ./theme/static_src run build

Static files
- Collect static for deployment:
  - python manage.py collectstatic

Tests
- Run all tests via Django’s test runner:
  - python manage.py test
- Run tests for a single app:
  - python manage.py test blog
- Run a single test case or test method (dotted path):
  - python manage.py test blog.tests.TestClass
  - python manage.py test blog.tests.TestClass.test_method

Linting
- No Python linter is configured in this repository (no ruff/flake8 in pyproject). No Node linter is configured under theme/static_src.

Architecture notes and key files
- Django project configuration: daycare/settings.py
  - INSTALLED_APPS includes: theme, daycare_ambassadeurs, blog, nursery, django_browser_reload, tailwind.
  - TEMPLATES loads app templates and additional dirs: daycare_ambassadeurs/templates, primaire/templates (missing), nursery/templates.
  - STATICFILES_DIRS aggregates static from daycare_ambassadeurs, theme, blog, and primaire (missing). STATIC_ROOT is staticfiles at repo root.
  - DATABASES is configured for PostgreSQL. Adjust locally as needed.
- URL routing: daycare/urls.py includes per-app routers, mounts __reload__/ for browser reload, and serves static in development.
- Tailwind/PostCSS pipeline (theme/static_src):
  - postcss.config.js enables @tailwindcss/postcss with simple vars and nested.
  - tailwind.config.js scans theme/templates, theme/static, daycare_ambassadeurs/templates, blog/templates.
  - Scripts: dev (watch), build (clean + minified build). Output: theme/static/css/dist/styles.css.
- Blog management commands (blog/management/commands/*):
  - create_admin: creates an admin user. Usage: python manage.py create_admin
  - migrate_article_styles: migrates article style data. Usage: python manage.py migrate_article_styles

CI/CD and rules
- No README.md, CLAUDE.md, Cursor rules, or Copilot instructions were found at the repo root. No CI workflows detected under .github/workflows/.
