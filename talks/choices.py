"""talk choices."""

from django.db import models
from django.utils.translation import gettext_lazy as _


class TalkCategoryChoices(models.TextChoices):
    """talk category choices."""

    AI_ML = "ai and ml", _("Artificial Intelligence & Machine Learning")
    CLOUD_DEVOPS = "cloud and devops", _("Cloud Computing & DevOps")
    CYBERSECURITY = "cybersecurity", _("Cybersecurity & Privacy")
    DATA_SCIENCE = "data science", _("Data Science & Analytics")
    FRONTEND = "frontend", _("Frontend Development")
    BACKEND = "backend", _("Backend Development")
    FULLSTACK = "fullstack", _("Full-Stack Development")
    MOBILE = "mobile", _("Mobile Development")
    WEB = "web", _("Web Development")
    DEVTOOLS = "devtools", _("DevTools & Productivity")
    PROGRAMMING_LANGUAGES = "programming languages", _("Programming Languages")
    SOFTWARE_ARCHITECTURE = "software architecture", _("Software Architecture & Design")
    DATABASE = "database", _("Database Technologies")
    BLOCKCHAIN = "blockchain", _("Blockchain & Web3")
    IOT = "iot", _("Internet of Things (IoT)")
    QUANTUM_COMPUTING = "quantum computing", _("Quantum Computing")
    OPEN_SOURCE = "open source", _("Open Source & Community")
    AGILE = "agile", _("Agile & Project Management")
    EMERGING_TECHNOLOGIES = "emerging technologies", _("Emerging Technologies")
    TECH_ETHICS = "tech ethics", _("Tech Ethics & Governance")
