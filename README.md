# SpeakWise-Backend

SpeakWise-Backend is a Django-based backend for the SpeakWise application, designed to provide robust APIs and backend services.

## Features

- Django 5.x project structure
- Environment-based settings (development, production)
- Code formatting and linting scripts (`black.sh`, `flake8.sh`)
- Modular settings and scripts

## Getting Started

### Prerequisites

- Python 3.10+
- pip
- Virtualenv (recommended)

### Setup

1. Clone the repository:
	```bash
	git clone https://github.com/yourusername/SpeakWise-Backend.git
	cd SpeakWise-Backend
	```

2. Create and activate a virtual environment:
	```bash
	python3 -m venv env
	source env/bin/activate
	```

3. Install dependencies:
	```bash
	pip install -r requirements.txt
	```

4. Run migrations:
	```bash
	python manage.py migrate
	```

5. Start the development server:
	```bash
	python manage.py runserver
	```

> **Note:**
> SpeakWise uses three settings environments:
> - `settings/base.py`
> - `settings/local.py`
> - `settings/prod.py`
>
> To specify which settings to use, you can run:
>
> ```bash
> python3 manage.py runserver --settings=speakwise.settings.local
> ```
>
> Or set the environment variable so you don't have to specify it every time:
>
> ```bash
> export DJANGO_SETTINGS_MODULE=speakwise.settings.local
> ```
## Project Structure

- `speakWise/` - Main Django project
- `settings/` - Environment-specific settings
- `scripts/` - Formatting and linting scripts
- `env/` - Virtual environment (not tracked in git)

## Contributing

We welcome contributions! Please follow these steps:

1. Fork the repository.
2. Create a new branch:
	```bash
	git checkout -b feature/your-feature-name
	```
3. Make your changes and commit:
	```bash
	git add .
	git commit -m "Describe your changes"
	```
4. Run formatting and linting:
	```bash
	bash scripts/black.sh
	bash scripts/flake8.sh
	```
5. Push to your fork:
	```bash
	git push origin feature/your-feature-name
	```
6. Open a Pull Request on GitHub.

### Code Style

- Use [Black](https://black.readthedocs.io/) for formatting.
- Use [Flake8](https://flake8.pycqa.org/) for linting.

## License

[MIT](LICENSE)
