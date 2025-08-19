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

NB: ```bash
    We have (3) settings env 
    - settings/settings_base.py
    - settings/settings_dev.py
    - settings/settings_prod.py
    Depending on the environment you are reunning on you can add it 
    e.g python3 manage.py runserver --settings=speakWise.settings.settings_dev

    or 

    export DJANGO_SETTINGS_MOULDE=speakWise.settings.settings_dev
    so you don't have to be running the settings command all the time
    
```
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
