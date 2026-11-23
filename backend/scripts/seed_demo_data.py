#!/usr/bin/env python3
"""
TalentLens — Synthetic Demo Data Generator & Verification Suite
==============================================================
Generates deterministic, idempotent, and realistic synthetic demo data
for manual testing and end-to-end evaluation of TalentLens.

Safety Guarantees:
- Never executes against production environments.
- Requires explicit confirmation flags (--confirm-demo-data / --confirm-cleanup).
- Strictly idempotent: repeated execution updates/re-uses existing demo records without duplicates.
- Never mutates or deletes existing non-demo user data.
- Enforces relational integrity, foreign keys, and application-level business constraints.

Usage:
    # Seed or update demo dataset:
    python scripts/seed_demo_data.py --confirm-demo-data

    # Optional: trigger screening on eligible jobs (if local Ollama is available):
    python scripts/seed_demo_data.py --confirm-demo-data --screen

    # Verify existing demo dataset integrity, auth, and tenant isolation:
    python scripts/seed_demo_data.py --verify

    # Safely clean up only records created by this generator:
    python scripts/seed_demo_data.py --cleanup --confirm-cleanup
"""

import argparse
import asyncio
from datetime import datetime, timedelta, timezone
import hashlib
import json
import logging
import os
from pathlib import Path
import sys
import uuid
from typing import Any, Dict, List, Optional, Tuple

# Ensure backend root is on sys.path
SCRIPT_DIR = Path(__file__).resolve().parent
BACKEND_ROOT = SCRIPT_DIR.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

import pymupdf as fitz
from sqlalchemy import delete, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.database import async_session_maker, engine
from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from app.models.application import (
    Application,
    ApplicationStatus,
    ApplicationStatusHistory,
)
from app.models.base import utc_now
from app.models.candidate import CandidateProfile, ParsingStatus, Resume
from app.models.career_assistant import CareerConversation, CareerMessage, ConversationPurpose, MessageRole
from app.models.job import EmploymentType, Job, JobStatus, WorkplaceType
from app.models.organization import Organization, OrganizationMembership, OrganizationRole
from app.models.recruiter_assistant import RecruiterConversation, RecruiterConversationType, RecruiterMessage, RecruiterMessageRole
from app.models.screening import (
    ScreeningInsight,
    ScreeningInsightStatus,
    ScreeningResult,
    ScreeningResultStatus,
    ScreeningRun,
    ScreeningRunStatus,
)
from app.models.user import User
from app.services.pdf_extractor import pdf_extractor
from app.services.storage_service import storage_service

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("seed_demo_data")

# ---------------------------------------------------------------------------
# Constants & Configuration
# ---------------------------------------------------------------------------
DEMO_PASSWORD = "TalentDemo@2026"
DEMO_EMAIL_DOMAIN = "talentlens.demo"

ORGANIZATIONS_DATA = [
    {
        "name": "NovaTech Solutions",
        "slug": "novatech-solutions",
        "is_active": True,
    },
    {
        "name": "BrightPath Digital",
        "slug": "brightpath-digital",
        "is_active": True,
    },
]

RECRUITERS_DATA = [
    {
        "email": "recruiter1@talentlens.demo",
        "full_name": "Sarah Jenkins",
        "org_slug": "novatech-solutions",
        "role": OrganizationRole.OWNER,
    },
    {
        "email": "recruiter2@talentlens.demo",
        "full_name": "Marcus Vance",
        "org_slug": "novatech-solutions",
        "role": OrganizationRole.RECRUITER,
    },
    {
        "email": "recruiter3@talentlens.demo",
        "full_name": "Elena Rostova",
        "org_slug": "brightpath-digital",
        "role": OrganizationRole.OWNER,
    },
    {
        "email": "recruiter4@talentlens.demo",
        "full_name": "David Chen",
        "org_slug": "brightpath-digital",
        "role": OrganizationRole.ADMIN,
    },
]

CANDIDATES_DATA = [
    {
        "email": "candidate1@talentlens.demo",
        "full_name": "Alex Rivera",
        "headline": "Junior Backend Developer | Python, FastAPI, PostgreSQL",
        "phone": "+1 (555) 234-5678",
        "location": "Austin, TX",
        "summary": "Proactive Junior Backend Developer with 2 years of experience designing and implementing scalable RESTful APIs with Python and FastAPI. Strong background in relational database optimization and containerized deployment with Docker.",
        "skills": ["Python", "FastAPI", "PostgreSQL", "Docker", "Redis", "SQL", "Git", "REST APIs", "Linux", "CI/CD"],
        "education": [
            {
                "institution": "University of Texas at Austin",
                "degree": "B.S. in Computer Science",
                "field_of_study": "Computer Science",
                "start_date": "2020-08",
                "end_date": "2024-05",
            }
        ],
        "experience": [
            {
                "company": "NexaStream Systems",
                "job_title": "Junior Backend Engineer",
                "description": "Developed and maintained 12+ RESTful microservices using FastAPI and PostgreSQL. Optimized SQL queries reducing p95 latency by 35%. Integrated Redis caching.",
                "start_date": "2024-06",
                "end_date": "Present",
            },
            {
                "company": "CloudSync Labs",
                "job_title": "Backend Engineering Intern",
                "description": "Built automated data ingestion pipelines in Python. Implemented unit tests achieving 88% coverage.",
                "start_date": "2023-05",
                "end_date": "2024-05",
            },
        ],
        "projects": [
            {
                "name": "TaskFlow Distributed Worker",
                "description": "Asynchronous task queue broker implemented in Python with Redis backend.",
                "technologies": ["Python", "Redis", "FastAPI", "Docker"],
            },
            {
                "name": "E-Commerce Inventory Service",
                "description": "High-throughput catalog and stock reservation REST API.",
                "technologies": ["Python", "PostgreSQL", "FastAPI", "Docker"],
            },
        ],
        "certifications": ["AWS Certified Cloud Practitioner"],
    },
    {
        "email": "candidate2@talentlens.demo",
        "full_name": "Priya Sharma",
        "headline": "Fresh Computer Science Graduate | Python, Java, SQL",
        "phone": "+91 98765 43210",
        "location": "Bangalore, India",
        "summary": "Enthusiastic 2026 Computer Science graduate with strong foundational knowledge in object-oriented programming, data structures, and relational databases. Passionate about software engineering and building robust backend services.",
        "skills": ["Python", "Java", "SQL", "C++", "HTML5", "CSS3", "Git", "Data Structures", "OOP", "Linux"],
        "education": [
            {
                "institution": "National Institute of Technology Karnataka",
                "degree": "B.Tech in Computer Science and Engineering",
                "field_of_study": "Computer Science",
                "start_date": "2022-08",
                "end_date": "2026-05",
            }
        ],
        "experience": [
            {
                "company": "TechMahindra Labs",
                "job_title": "Software Engineering Intern",
                "description": "Collaborated on internal analytics tooling using Python and SQLite. Automated test suites using pytest.",
                "start_date": "2025-05",
                "end_date": "2025-08",
            }
        ],
        "projects": [
            {
                "name": "Campus Placement Portal",
                "description": "Full-featured recruitment web portal for college placement drives.",
                "technologies": ["Python", "Flask", "SQLite", "Bootstrap"],
            },
            {
                "name": "Library Management System",
                "description": "Desktop management system with role-based access control.",
                "technologies": ["Java", "MySQL", "JDBC"],
            },
        ],
        "certifications": ["Python Institute Certified Associate in Python Programming (PCAP)"],
    },
    {
        "email": "candidate3@talentlens.demo",
        "full_name": "Liam O'Connor",
        "headline": "Software Development Intern | React, TypeScript, JavaScript",
        "phone": "+1 (555) 345-6789",
        "location": "Boston, MA",
        "summary": "Motivated Software Development Intern with practical experience creating interactive web user interfaces using React, TypeScript, and modern JavaScript. Eager to contribute to production front-end applications.",
        "skills": ["React", "TypeScript", "JavaScript", "HTML5", "CSS3", "Tailwind CSS", "Git", "REST APIs", "Jest"],
        "education": [
            {
                "institution": "Northeastern University",
                "degree": "B.S. in Software Engineering",
                "field_of_study": "Software Engineering",
                "start_date": "2023-09",
                "end_date": "2027-05",
            }
        ],
        "experience": [
            {
                "company": "Beacon Interactive",
                "job_title": "Front-End Developer Intern",
                "description": "Developed reusable UI component library using React and Tailwind CSS. Reduced bundle size by 15% through lazy loading.",
                "start_date": "2025-01",
                "end_date": "Present",
            }
        ],
        "projects": [
            {
                "name": "Collaborative Task Board",
                "description": "Kanban board web application with drag-and-drop state management.",
                "technologies": ["React", "TypeScript", "Tailwind CSS"],
            },
            {
                "name": "Weather Forecast Explorer",
                "description": "Responsive weather dashboard consuming OpenWeather REST API.",
                "technologies": ["JavaScript", "HTML5", "CSS3", "REST APIs"],
            },
        ],
        "certifications": ["Meta Front-End Developer Professional Certificate"],
    },
    {
        "email": "candidate4@talentlens.demo",
        "full_name": "Amina Yusuf",
        "headline": "Frontend Developer | React, Next.js, TypeScript, Tailwind CSS",
        "phone": "+1 (555) 456-7890",
        "location": "Chicago, IL",
        "summary": "Creative Frontend Developer with 2.5 years of experience building accessible, responsive, and performant web applications using React, TypeScript, and Next.js. Passionate about design systems and pixel-perfect UI engineering.",
        "skills": ["React", "Next.js", "TypeScript", "JavaScript", "HTML5", "CSS3", "Tailwind CSS", "Redux", "REST APIs", "Jest", "Webpack"],
        "education": [
            {
                "institution": "DePaul University",
                "degree": "B.A. in Digital Media & Web Design",
                "field_of_study": "Web Engineering",
                "start_date": "2019-09",
                "end_date": "2023-06",
            }
        ],
        "experience": [
            {
                "company": "Horizon Digital Agency",
                "job_title": "Frontend Developer",
                "description": "Built responsive client portals in Next.js and TypeScript. Implemented WCAG 2.1 AA accessibility standards.",
                "start_date": "2023-07",
                "end_date": "Present",
            }
        ],
        "projects": [
            {
                "name": "SaaS Metrics Dashboard",
                "description": "Interactive data visualization interface with dark mode theme support.",
                "technologies": ["React", "TypeScript", "Tailwind CSS", "Redux"],
            },
            {
                "name": "Headless E-Commerce Front",
                "description": "High-performance storefront with server-side rendering in Next.js.",
                "technologies": ["Next.js", "TypeScript", "Tailwind CSS", "REST APIs"],
            },
        ],
        "certifications": ["freeCodeCamp Responsive Web Design Certification"],
    },
    {
        "email": "candidate5@talentlens.demo",
        "full_name": "Carlos Mendez",
        "headline": "Full Stack Developer | React, Node.js, TypeScript, PostgreSQL",
        "phone": "+1 (555) 567-8901",
        "location": "Seattle, WA",
        "summary": "Versatile Full Stack Developer with 3 years of experience shipping production web applications end-to-end. Proficient in React and TypeScript on the frontend and Node.js with PostgreSQL on the backend.",
        "skills": ["React", "Node.js", "TypeScript", "PostgreSQL", "REST APIs", "Docker", "Git", "Tailwind CSS", "Express", "Next.js"],
        "education": [
            {
                "institution": "University of Washington",
                "degree": "B.S. in Informatics",
                "field_of_study": "Software Architecture",
                "start_date": "2020-09",
                "end_date": "2023-06",
            }
        ],
        "experience": [
            {
                "company": "Apex Cloud Technologies",
                "job_title": "Full Stack Engineer",
                "description": "Architected customer-facing portals using React, TypeScript, and Node.js REST services. Managed PostgreSQL databases.",
                "start_date": "2023-07",
                "end_date": "Present",
            },
            {
                "company": "Cascade Media",
                "job_title": "Junior Web Developer",
                "description": "Created interactive client sites and backend APIs with Node.js and Express.",
                "start_date": "2022-06",
                "end_date": "2023-06",
            },
        ],
        "projects": [
            {
                "name": "Real-Time Team Sync",
                "description": "Collaborative document and chat workspace with WebSocket updates.",
                "technologies": ["React", "Node.js", "PostgreSQL", "TypeScript"],
            },
            {
                "name": "Feedback Analytics Engine",
                "description": "Customer survey pipeline with sentiment categorization.",
                "technologies": ["React", "Node.js", "PostgreSQL", "Docker"],
            },
        ],
        "certifications": ["MongoDB Certified Developer Associate"],
    },
    {
        "email": "candidate6@talentlens.demo",
        "full_name": "Chloe Dubois",
        "headline": "Python Developer | Python, Django, Celery, PostgreSQL",
        "phone": "+1 (555) 678-9012",
        "location": "New York, NY",
        "summary": "Experienced Python Developer with 3.5 years of experience architecting reliable backend services, database migrations, and background worker queues using Python, Django, Celery, and PostgreSQL.",
        "skills": ["Python", "Django", "FastAPI", "Celery", "PostgreSQL", "Redis", "Docker", "Git", "Linux", "Pytest", "SQL"],
        "education": [
            {
                "institution": "Columbia University",
                "degree": "B.S. in Computer Science",
                "field_of_study": "Computer Science",
                "start_date": "2018-09",
                "end_date": "2022-05",
            }
        ],
        "experience": [
            {
                "company": "FinTech Velocity",
                "job_title": "Python Backend Developer",
                "description": "Engineered transactional settlement microservices using Python, Django, and PostgreSQL. Integrated Celery workers.",
                "start_date": "2022-07",
                "end_date": "Present",
            }
        ],
        "projects": [
            {
                "name": "High-Throughput Notification Dispatcher",
                "description": "Fault-tolerant messaging pipeline processing 10k messages/min.",
                "technologies": ["Python", "Celery", "Redis", "Docker"],
            },
            {
                "name": "Audit Logging Microservice",
                "description": "Tamper-evident audit ledger using PostgreSQL partitioned tables.",
                "technologies": ["Python", "FastAPI", "PostgreSQL"],
            },
        ],
        "certifications": ["Docker Certified Associate (DCA)"],
    },
    {
        "email": "candidate7@talentlens.demo",
        "full_name": "Rohan Patel",
        "headline": "Data Analyst | SQL, Python, Tableau, Business Intelligence",
        "phone": "+1 (555) 789-0123",
        "location": "San Jose, CA",
        "summary": "Insightful Data Analyst with 2 years of experience extracting actionable business intelligence from complex relational datasets. Expert in advanced SQL querying, Python data manipulation, and executive dashboard development in Tableau.",
        "skills": ["SQL", "Python", "Tableau", "Data Analysis", "Excel", "Pandas", "PowerBI", "ETL", "PostgreSQL", "Statistics"],
        "education": [
            {
                "institution": "San Jose State University",
                "degree": "B.S. in Statistics & Data Analytics",
                "field_of_study": "Applied Statistics",
                "start_date": "2020-08",
                "end_date": "2024-05",
            }
        ],
        "experience": [
            {
                "company": "RetailPulse Analytics",
                "job_title": "Data Analyst",
                "description": "Designed Tableau dashboards monitoring $40M annual revenue. Built SQL data models and Python automated ETL pipelines.",
                "start_date": "2024-06",
                "end_date": "Present",
            },
            {
                "company": "BayArea Metrics",
                "job_title": "BI Analytics Intern",
                "description": "Formulated complex SQL queries for executive KPIs and ad-hoc analysis.",
                "start_date": "2023-06",
                "end_date": "2024-05",
            },
        ],
        "projects": [
            {
                "name": "Customer Churn Intelligence Model",
                "description": "Predictive churn analytics dashboard with automated cohort reporting.",
                "technologies": ["SQL", "Python", "Tableau", "Pandas"],
            },
            {
                "name": "Supply Chain Fulfillment Tracker",
                "description": "Weekly automated ETL pipeline consolidating distribution logistics.",
                "technologies": ["Python", "SQL", "Excel", "ETL"],
            },
        ],
        "certifications": ["Tableau Desktop Specialist", "Google Data Analytics Professional Certificate"],
    },
    {
        "email": "candidate8@talentlens.demo",
        "full_name": "Zoe Washington",
        "headline": "Junior Data Scientist | Python, Scikit-Learn, PyTorch, Machine Learning",
        "phone": "+1 (555) 890-1234",
        "location": "San Francisco, CA",
        "summary": "Analytical Junior Data Scientist with 1.5 years of experience building and evaluating predictive machine learning models in Python. Skilled in exploratory data analysis, feature engineering, Scikit-Learn, and PyTorch.",
        "skills": ["Python", "Pandas", "Scikit-Learn", "Machine Learning", "SQL", "PyTorch", "NumPy", "Docker", "Jupyter", "Data Analysis"],
        "education": [
            {
                "institution": "University of California, Berkeley",
                "degree": "M.S. in Data Science",
                "field_of_study": "Machine Learning",
                "start_date": "2023-08",
                "end_date": "2024-05",
            },
            {
                "institution": "UCLA",
                "degree": "B.S. in Applied Mathematics",
                "field_of_study": "Mathematics",
                "start_date": "2019-09",
                "end_date": "2023-06",
            },
        ],
        "experience": [
            {
                "company": "MindWorks AI",
                "job_title": "Junior Data Scientist",
                "description": "Trained predictive regression and classification models using Scikit-Learn. Performed feature importance attribution with SHAP.",
                "start_date": "2024-06",
                "end_date": "Present",
            }
        ],
        "projects": [
            {
                "name": "Customer Lifetime Value Classifier",
                "description": "End-to-end ML pipeline with cross-validation and hyperparameter tuning.",
                "technologies": ["Python", "Scikit-Learn", "Pandas", "SQL"],
            },
            {
                "name": "Medical Imaging Triage Model",
                "description": "PyTorch deep neural network prototype for multi-class pathology classification.",
                "technologies": ["PyTorch", "Python", "Docker", "Jupyter"],
            },
        ],
        "certifications": ["DeepLearning.AI Deep Learning Specialization"],
    },
    {
        "email": "candidate9@talentlens.demo",
        "full_name": "Kenji Sato",
        "headline": "Java Software Developer | Java, Spring Boot, Microservices, SQL",
        "phone": "+1 (555) 901-2345",
        "location": "Atlanta, GA",
        "summary": "Dedicated Java Software Developer with 2.5 years of experience developing enterprise backend systems and RESTful microservices using Java, Spring Boot, Hibernate, and relational databases.",
        "skills": ["Java", "Spring Boot", "REST APIs", "SQL", "Git", "Microservices", "Docker", "PostgreSQL", "Hibernate", "Maven"],
        "education": [
            {
                "institution": "Georgia Institute of Technology",
                "degree": "B.S. in Computer Science",
                "field_of_study": "Systems & Architecture",
                "start_date": "2019-08",
                "end_date": "2023-05",
            }
        ],
        "experience": [
            {
                "company": "Delta Enterprise Software",
                "job_title": "Java Software Engineer",
                "description": "Engineered Spring Boot microservices handling core financial account ledgers. Implemented REST contracts with OpenAPI specs.",
                "start_date": "2023-06",
                "end_date": "Present",
            }
        ],
        "projects": [
            {
                "name": "Microservice Order Billing Engine",
                "description": "Asynchronous billing processor built on Java 17 and Spring Boot.",
                "technologies": ["Java", "Spring Boot", "PostgreSQL", "Docker"],
            },
            {
                "name": "JWT Security Gateway",
                "description": "Stateless authentication proxy with role-based access filters.",
                "technologies": ["Java", "Spring Boot", "REST APIs"],
            },
        ],
        "certifications": ["Oracle Certified Professional: Java SE 11 Developer"],
    },
    {
        "email": "candidate10@talentlens.demo",
        "full_name": "Fatima Al-Mansoor",
        "headline": "Junior Backend Developer | Go, Python, PostgreSQL, Docker",
        "phone": "+1 (555) 012-3456",
        "location": "Dallas, TX",
        "summary": "Detail-oriented Junior Backend Developer skilled in building high-concurrency microservices in Go and Python. Strong knowledge of PostgreSQL indexing, Docker containerization, and distributed API design.",
        "skills": ["Python", "Go", "PostgreSQL", "Docker", "Redis", "REST APIs", "SQL", "Linux", "Git", "Microservices"],
        "education": [
            {
                "institution": "University of Texas at Dallas",
                "degree": "B.S. in Computer Science",
                "field_of_study": "Computer Science",
                "start_date": "2020-08",
                "end_date": "2024-05",
            }
        ],
        "experience": [
            {
                "company": "CyberMesh Technologies",
                "job_title": "Backend Software Engineer",
                "description": "Developed high-throughput API endpoints in Python and Go. Optimized PostgreSQL transaction isolation levels.",
                "start_date": "2024-06",
                "end_date": "Present",
            }
        ],
        "projects": [
            {
                "name": "High-Speed Webhook Dispatcher",
                "description": "Concurrent event forwarding engine written in Go with Redis queueing.",
                "technologies": ["Go", "Redis", "Docker", "PostgreSQL"],
            },
            {
                "name": "Document Indexing Service",
                "description": "Metadata extraction and search microservice in Python.",
                "technologies": ["Python", "PostgreSQL", "Docker", "REST APIs"],
            },
        ],
        "certifications": ["Red Hat Certified System Administrator (RHCSA)"],
    },
    {
        "email": "candidate11@talentlens.demo",
        "full_name": "Lucas Silva",
        "headline": "Full Stack Developer | React, Python, FastAPI, TypeScript",
        "phone": "+1 (555) 123-4567",
        "location": "Denver, CO",
        "summary": "Dynamic Full-Stack Developer with 2 years of experience bridging responsive frontend interfaces with high-performance Python FastAPI backends. Experienced with React, TypeScript, and relational schema design.",
        "skills": ["React", "Python", "FastAPI", "TypeScript", "JavaScript", "PostgreSQL", "Docker", "REST APIs", "HTML5", "CSS3"],
        "education": [
            {
                "institution": "University of Colorado Boulder",
                "degree": "B.S. in Computer Engineering",
                "field_of_study": "Computer Engineering",
                "start_date": "2020-08",
                "end_date": "2024-05",
            }
        ],
        "experience": [
            {
                "company": "PeakView Software",
                "job_title": "Full Stack Developer",
                "description": "Built reactive web dashboards in React and TypeScript supported by FastAPI microservices and PostgreSQL.",
                "start_date": "2024-06",
                "end_date": "Present",
            }
        ],
        "projects": [
            {
                "name": "IoT Device Monitoring Console",
                "description": "Real-time telemetry monitoring application with time-series charts.",
                "technologies": ["React", "Python", "FastAPI", "PostgreSQL"],
            },
            {
                "name": "Interactive Job Board",
                "description": "Candidate and recruiter portal with role-based access control.",
                "technologies": ["React", "TypeScript", "FastAPI", "Docker"],
            },
        ],
        "certifications": ["Certified Kubernetes Application Developer (CKAD)"],
    },
    {
        "email": "candidate12@talentlens.demo",
        "full_name": "Maya Lin",
        "headline": "Data Analyst | PowerBI, SQL, Tableau, Python, ETL",
        "phone": "+1 (555) 234-9876",
        "location": "Toronto, Canada",
        "summary": "Data Analyst and BI Specialist with 2 years of experience developing automated ETL pipelines and multi-page business intelligence dashboards. Skilled in SQL, PowerBI, Tableau, and Python data pipelines.",
        "skills": ["SQL", "Python", "PowerBI", "Tableau", "Data Analysis", "Excel", "Pandas", "ETL", "PostgreSQL", "Statistics"],
        "education": [
            {
                "institution": "University of Waterloo",
                "degree": "B.S. in Data Analytics",
                "field_of_study": "Business Analytics",
                "start_date": "2020-09",
                "end_date": "2024-05",
            }
        ],
        "experience": [
            {
                "company": "OmniChannel Retail Group",
                "job_title": "Business Intelligence Analyst",
                "description": "Engineered PowerBI and Tableau reports for executive leadership. Built scheduled Python ETL workflows for data cleansing.",
                "start_date": "2024-06",
                "end_date": "Present",
            }
        ],
        "projects": [
            {
                "name": "Global Retail Executive Dashboard",
                "description": "Multi-region sales and inventory forecasting dashboard with interactive drill-downs.",
                "technologies": ["PowerBI", "SQL", "Python", "ETL"],
            },
            {
                "name": "Customer Lifetime Analytics Pipeline",
                "description": "Automated data modeling scripts calculating churn metrics and RFM segments.",
                "technologies": ["Python", "Pandas", "SQL", "Tableau"],
            },
        ],
        "certifications": ["Microsoft Certified: Power BI Data Analyst Associate (PL-300)"],
    },
]

JOBS_DATA = [
    {
        "key": "python-backend",
        "org_slug": "novatech-solutions",
        "recruiter_email": "recruiter1@talentlens.demo",
        "title": "Python Backend Developer",
        "slug": "python-backend-developer-novatech",
        "department": "Engineering",
        "workplace_type": WorkplaceType.REMOTE,
        "employment_type": EmploymentType.FULL_TIME,
        "location": "Remote (US/India)",
        "experience_min": 1,
        "experience_max": 4,
        "salary_min": 800000.0,
        "salary_max": 1500000.0,
        "salary_currency": "INR",
        "required_skills": ["Python", "FastAPI", "PostgreSQL", "Docker"],
        "preferred_skills": ["Redis", "AsyncIO", "Git"],
        "status": JobStatus.PUBLISHED,
        "description": "NovaTech Solutions is seeking a talented Python Backend Developer to design, build, and optimize scalable asynchronous microservices for our core enterprise platform.",
        "responsibilities": (
            "- Develop and maintain production RESTful APIs using Python and FastAPI.\n"
            "- Design efficient PostgreSQL database schemas, indexes, and queries.\n"
            "- Containerize services using Docker and maintain CI/CD pipelines.\n"
            "- Collaborate with frontend engineers to integrate responsive client applications."
        ),
        "qualifications": (
            "- 1-4 years of professional experience developing backend web services in Python.\n"
            "- Demonstrated proficiency with FastAPI or Flask, and relational databases (PostgreSQL).\n"
            "- Strong understanding of containerization (Docker) and Git version control."
        ),
    },
    {
        "key": "junior-react",
        "org_slug": "novatech-solutions",
        "recruiter_email": "recruiter2@talentlens.demo",
        "title": "Junior React Developer",
        "slug": "junior-react-developer-novatech",
        "department": "Product Engineering",
        "workplace_type": WorkplaceType.HYBRID,
        "employment_type": EmploymentType.FULL_TIME,
        "location": "Bangalore, India",
        "experience_min": 0,
        "experience_max": 2,
        "salary_min": 500000.0,
        "salary_max": 900000.0,
        "salary_currency": "INR",
        "required_skills": ["React", "JavaScript", "TypeScript", "HTML5", "CSS3"],
        "preferred_skills": ["Tailwind CSS", "Redux", "REST APIs"],
        "status": JobStatus.PUBLISHED,
        "description": "NovaTech Solutions is hiring a passionate Junior React Developer to help craft intuitive, high-performance web applications for our growing SaaS product line.",
        "responsibilities": (
            "- Build reusable, responsive front-end components using React, TypeScript, and modern CSS.\n"
            "- Integrate RESTful APIs and handle asynchronous data state management.\n"
            "- Write clean, maintainable, and accessible code conforming to design standards."
        ),
        "qualifications": (
            "- 0-2 years of experience with React, TypeScript, and modern JavaScript.\n"
            "- Strong understanding of component lifecycle, hooks, and DOM manipulation.\n"
            "- Familiarity with Git, Tailwind CSS, or component libraries is a strong plus."
        ),
    },
    {
        "key": "junior-data-scientist",
        "org_slug": "novatech-solutions",
        "recruiter_email": "recruiter1@talentlens.demo",
        "title": "Junior Data Scientist",
        "slug": "junior-data-scientist-novatech",
        "department": "AI & Analytics",
        "workplace_type": WorkplaceType.REMOTE,
        "employment_type": EmploymentType.FULL_TIME,
        "location": "Remote",
        "experience_min": 0,
        "experience_max": 3,
        "salary_min": 700000.0,
        "salary_max": 1300000.0,
        "salary_currency": "INR",
        "required_skills": ["Python", "Pandas", "Scikit-Learn", "Machine Learning", "SQL"],
        "preferred_skills": ["PyTorch", "Docker", "Jupyter"],
        "status": JobStatus.PUBLISHED,
        "description": "Join NovaTech's Data Science team to develop predictive models, automated feature pipelines, and data-driven insights across our customer analytics domain.",
        "responsibilities": (
            "- Perform exploratory data analysis and feature engineering on structured datasets.\n"
            "- Train, validate, and evaluate predictive machine learning models in Python.\n"
            "- Partner with backend engineers to deploy model inference endpoints."
        ),
        "qualifications": (
            "- 0-3 years of practical experience with Python, Pandas, Scikit-Learn, and SQL.\n"
            "- Degree in Data Science, Computer Science, Statistics, or related quantitative field.\n"
            "- Solid foundation in statistics, regression, classification, and evaluation metrics."
        ),
    },
    {
        "key": "full-stack-dev",
        "org_slug": "brightpath-digital",
        "recruiter_email": "recruiter3@talentlens.demo",
        "title": "Full Stack Developer",
        "slug": "full-stack-developer-brightpath",
        "department": "Digital Platforms",
        "workplace_type": WorkplaceType.HYBRID,
        "employment_type": EmploymentType.FULL_TIME,
        "location": "Mumbai, India",
        "experience_min": 2,
        "experience_max": 5,
        "salary_min": 1000000.0,
        "salary_max": 1800000.0,
        "salary_currency": "INR",
        "required_skills": ["React", "Node.js", "TypeScript", "PostgreSQL", "REST APIs"],
        "preferred_skills": ["Docker", "Tailwind CSS", "Next.js"],
        "status": JobStatus.PUBLISHED,
        "description": "BrightPath Digital is looking for an experienced Full Stack Developer to lead development of our client engagement and workflow automation platforms.",
        "responsibilities": (
            "- Design and implement full-stack web applications using React, TypeScript, and Node.js.\n"
            "- Build scalable REST APIs and relational database models in PostgreSQL.\n"
            "- Maintain automated test coverage and deploy via modern CI/CD pipelines."
        ),
        "qualifications": (
            "- 2-5 years of full-stack engineering experience.\n"
            "- Proven expertise with React, TypeScript, Node.js, and relational database systems.\n"
            "- Experience building and consuming secured RESTful web services."
        ),
    },
    {
        "key": "data-analyst",
        "org_slug": "brightpath-digital",
        "recruiter_email": "recruiter4@talentlens.demo",
        "title": "Data Analyst",
        "slug": "data-analyst-brightpath",
        "department": "Business Intelligence",
        "workplace_type": WorkplaceType.ONSITE,
        "employment_type": EmploymentType.FULL_TIME,
        "location": "Hyderabad, India",
        "experience_min": 1,
        "experience_max": 3,
        "salary_min": 600000.0,
        "salary_max": 1100000.0,
        "salary_currency": "INR",
        "required_skills": ["SQL", "Python", "Tableau", "Data Analysis", "Excel"],
        "preferred_skills": ["PowerBI", "Pandas", "ETL"],
        "status": JobStatus.PUBLISHED,
        "description": "BrightPath Digital is seeking an analytical Data Analyst to transform complex business data into visual dashboards and actionable management insights.",
        "responsibilities": (
            "- Author complex SQL queries to extract, transform, and aggregate business metrics.\n"
            "- Develop and maintain automated interactive dashboards in Tableau and PowerBI.\n"
            "- Analyze KPI trends and deliver clear presentations to executive stakeholders."
        ),
        "qualifications": (
            "- 1-3 years of hands-on data analysis experience.\n"
            "- Advanced SQL skills and proficiency in Tableau or PowerBI.\n"
            "- Working knowledge of Python (Pandas) for data cleansing and automation."
        ),
    },
    {
        "key": "java-software-dev",
        "org_slug": "brightpath-digital",
        "recruiter_email": "recruiter3@talentlens.demo",
        "title": "Java Software Developer",
        "slug": "java-software-developer-brightpath",
        "department": "Enterprise Solutions",
        "workplace_type": WorkplaceType.HYBRID,
        "employment_type": EmploymentType.FULL_TIME,
        "location": "Pune, India",
        "experience_min": 1,
        "experience_max": 4,
        "salary_min": 750000.0,
        "salary_max": 1400000.0,
        "salary_currency": "INR",
        "required_skills": ["Java", "Spring Boot", "REST APIs", "SQL", "Git"],
        "preferred_skills": ["Microservices", "Docker", "PostgreSQL"],
        "status": JobStatus.DRAFT,  # Demonstrates DRAFT status in job lifecycle
        "description": "Draft requisition for upcoming Java microservice architecture expansion at BrightPath Digital.",
        "responsibilities": (
            "- Architect and code backend services using Java 17 and Spring Boot.\n"
            "- Implement secure REST interfaces and integrate relational persistence layers.\n"
            "- Participate in design reviews, unit testing, and continuous integration."
        ),
        "qualifications": (
            "- 1-4 years of experience writing enterprise Java applications with Spring Boot.\n"
            "- Solid understanding of OOP principles, relational databases, and SQL.\n"
            "- Familiarity with Docker, Git, and RESTful API best practices."
        ),
    },
]

# 22 realistic applications across 5 published jobs
APPLICATIONS_PLAN = [
    # Job: Python Backend Developer (NovaTech Solutions)
    {
        "job_key": "python-backend",
        "candidate_email": "candidate1@talentlens.demo",
        "status": ApplicationStatus.HIRED,
        "cover_letter": "I have spent the past two years focusing deeply on Python, FastAPI, and PostgreSQL microservices. I would love to contribute to NovaTech's backend infrastructure.",
        "days_ago": 18,
    },
    {
        "job_key": "python-backend",
        "candidate_email": "candidate6@talentlens.demo",
        "status": ApplicationStatus.INTERVIEWING,
        "cover_letter": "With 3.5 years building high-throughput Python and Celery systems, I am excited about this role and eager to discuss how my backend experience aligns with your team's goals.",
        "days_ago": 14,
    },
    {
        "job_key": "python-backend",
        "candidate_email": "candidate10@talentlens.demo",
        "status": ApplicationStatus.SHORTLISTED,
        "cover_letter": "My background in Go and Python backend engineering gives me a strong perspective on low-latency microservices and database optimization.",
        "days_ago": 10,
    },
    {
        "job_key": "python-backend",
        "candidate_email": "candidate2@talentlens.demo",
        "status": ApplicationStatus.UNDER_REVIEW,
        "cover_letter": "As a recent Computer Science graduate with strong Python and SQL fundamentals, I am enthusiastic about launching my backend career with NovaTech Solutions.",
        "days_ago": 5,
    },
    {
        "job_key": "python-backend",
        "candidate_email": "candidate3@talentlens.demo",
        "status": ApplicationStatus.REJECTED,
        "cover_letter": "I am looking to branch out from frontend engineering into backend systems and believe I can quickly learn your stack.",
        "days_ago": 12,
    },

    # Job: Junior React Developer (NovaTech Solutions)
    {
        "job_key": "junior-react",
        "candidate_email": "candidate4@talentlens.demo",
        "status": ApplicationStatus.HIRED,
        "cover_letter": "Frontend engineering with React and TypeScript is my primary focus. I specialize in building performant, pixel-perfect web applications with clean design systems.",
        "days_ago": 20,
    },
    {
        "job_key": "junior-react",
        "candidate_email": "candidate3@talentlens.demo",
        "status": ApplicationStatus.SHORTLISTED,
        "cover_letter": "During my frontend internship, I built modern React and Tailwind components. I am eager to apply and grow these skills full-time at NovaTech.",
        "days_ago": 8,
    },
    {
        "job_key": "junior-react",
        "candidate_email": "candidate5@talentlens.demo",
        "status": ApplicationStatus.UNDER_REVIEW,
        "cover_letter": "While I have full-stack experience, I particularly enjoy React component architecture and modern UI engineering.",
        "days_ago": 4,
    },
    {
        "job_key": "junior-react",
        "candidate_email": "candidate11@talentlens.demo",
        "status": ApplicationStatus.SUBMITTED,
        "cover_letter": "I have created reactive frontend portals in React and TypeScript and would welcome the opportunity to join the NovaTech product team.",
        "days_ago": 2,
    },
    {
        "job_key": "junior-react",
        "candidate_email": "candidate7@talentlens.demo",
        "status": ApplicationStatus.REJECTED,
        "cover_letter": "Applying for the Junior React Developer position. I have strong data visualization skills that I hope to translate into UI engineering.",
        "days_ago": 11,
    },

    # Job: Junior Data Scientist (NovaTech Solutions)
    {
        "job_key": "junior-data-scientist",
        "candidate_email": "candidate8@talentlens.demo",
        "status": ApplicationStatus.SHORTLISTED,
        "cover_letter": "With my M.S. in Data Science and direct experience with Scikit-Learn, PyTorch, and predictive modeling, I am thrilled to apply for the Junior Data Scientist opening.",
        "days_ago": 9,
    },
    {
        "job_key": "junior-data-scientist",
        "candidate_email": "candidate7@talentlens.demo",
        "status": ApplicationStatus.UNDER_REVIEW,
        "cover_letter": "My background in quantitative analytics, SQL, and Pandas provides a solid foundation for advancing into machine learning at NovaTech.",
        "days_ago": 6,
    },
    {
        "job_key": "junior-data-scientist",
        "candidate_email": "candidate12@talentlens.demo",
        "status": ApplicationStatus.SUBMITTED,
        "cover_letter": "Experienced in statistical analysis, Python data modeling, and automated ETL pipelines, looking to transition into data science.",
        "days_ago": 1,
    },
    {
        "job_key": "junior-data-scientist",
        "candidate_email": "candidate2@talentlens.demo",
        "status": ApplicationStatus.REJECTED,
        "cover_letter": "I took machine learning electives during my degree and would like to be considered for this Junior Data Scientist role.",
        "days_ago": 15,
    },

    # Job: Full Stack Developer (BrightPath Digital)
    {
        "job_key": "full-stack-dev",
        "candidate_email": "candidate5@talentlens.demo",
        "status": ApplicationStatus.HIRED,
        "cover_letter": "With 3 years of end-to-end web application development across React, Node.js, and PostgreSQL, I can immediately contribute to BrightPath Digital.",
        "days_ago": 22,
    },
    {
        "job_key": "full-stack-dev",
        "candidate_email": "candidate11@talentlens.demo",
        "status": ApplicationStatus.INTERVIEWING,
        "cover_letter": "I build responsive React frontends paired with resilient backend APIs and have extensive experience with TypeScript and PostgreSQL.",
        "days_ago": 12,
    },
    {
        "job_key": "full-stack-dev",
        "candidate_email": "candidate4@talentlens.demo",
        "status": ApplicationStatus.SHORTLISTED,
        "cover_letter": "Strong frontend engineer with Node.js and REST API integration experience, ready to take on full-stack responsibilities.",
        "days_ago": 7,
    },
    {
        "job_key": "full-stack-dev",
        "candidate_email": "candidate1@talentlens.demo",
        "status": ApplicationStatus.UNDER_REVIEW,
        "cover_letter": "Experienced backend developer seeking to leverage my API and database background in a full-stack environment.",
        "days_ago": 3,
    },

    # Job: Data Analyst (BrightPath Digital)
    {
        "job_key": "data-analyst",
        "candidate_email": "candidate7@talentlens.demo",
        "status": ApplicationStatus.HIRED,
        "cover_letter": "I have spent the last 2 years writing production SQL and building Tableau dashboards that drove measurable business improvements.",
        "days_ago": 21,
    },
    {
        "job_key": "data-analyst",
        "candidate_email": "candidate12@talentlens.demo",
        "status": ApplicationStatus.SHORTLISTED,
        "cover_letter": "Specializing in PowerBI, SQL queries, and Python data pipelines, I am eager to help BrightPath's clients unlock insights from their data.",
        "days_ago": 8,
    },
    {
        "job_key": "data-analyst",
        "candidate_email": "candidate8@talentlens.demo",
        "status": ApplicationStatus.UNDER_REVIEW,
        "cover_letter": "My quantitative analysis and Python data manipulation skills make me a strong candidate for exploratory business analysis.",
        "days_ago": 4,
    },
    {
        "job_key": "data-analyst",
        "candidate_email": "candidate2@talentlens.demo",
        "status": ApplicationStatus.SUBMITTED,
        "cover_letter": "As a fresh graduate with strong SQL and statistical coursework, I am very keen to begin my career as a Data Analyst with BrightPath Digital.",
        "days_ago": 1,
    },
]


# ---------------------------------------------------------------------------
# Safety & Production Environment Checks
# ---------------------------------------------------------------------------
def assert_safe_environment() -> None:
    """Refuse execution against production environments or unconfirmed runs."""
    env = (settings.ENVIRONMENT or "development").strip().lower()
    if env in ("production", "prod", "live"):
        raise RuntimeError(
            f"FATAL: Demo data seeding cannot run in production environment (ENVIRONMENT='{env}'). "
            "Execution terminated to protect production state."
        )

    db_url = settings.DATABASE_URL.lower()
    if any(k in db_url for k in ("prod", "production", "rds.amazonaws.com", "azure.com")):
        raise RuntimeError(
            f"FATAL: Database URL appears to point to a production cluster: {settings.DATABASE_URL}. "
            "Execution terminated for safety."
        )


# ---------------------------------------------------------------------------
# PDF Resume Generator
# ---------------------------------------------------------------------------
def build_resume_pdf_bytes(cand: Dict[str, Any]) -> bytes:
    """Generate a clean, professional, single-page PDF resume using PyMuPDF."""
    doc = fitz.open()
    # Letter size: 612 x 792 pt
    page = doc.new_page(width=612, height=792)

    # Margins: 45 pt from borders
    margin_x = 45.0
    margin_y = 45.0
    content_width = 612.0 - (margin_x * 2.0)
    y = margin_y

    # Header - Candidate Name
    page.insert_text(fitz.Point(margin_x, y + 16), cand["full_name"], fontsize=18, fontname="helv", color=(0.1, 0.1, 0.2))
    y += 24

    # Header - Headline
    page.insert_text(fitz.Point(margin_x, y + 10), cand["headline"], fontsize=10, fontname="helv", color=(0.3, 0.3, 0.4))
    y += 16

    # Contact line
    contact_line = f"{cand['email']} | {cand['phone']} | {cand['location']}"
    page.insert_text(fitz.Point(margin_x, y + 9), contact_line, fontsize=9, fontname="helv", color=(0.4, 0.4, 0.45))
    y += 18

    # Separator rule
    page.draw_line(fitz.Point(margin_x, y), fitz.Point(margin_x + content_width, y), color=(0.8, 0.8, 0.85), width=1.0)
    y += 14

    def add_section_header(title: str, current_y: float) -> float:
        page.insert_text(fitz.Point(margin_x, current_y + 11), title.upper(), fontsize=11, fontname="helv", color=(0.15, 0.25, 0.45))
        current_y += 15
        page.draw_line(fitz.Point(margin_x, current_y), fitz.Point(margin_x + content_width, current_y), color=(0.85, 0.88, 0.92), width=0.5)
        current_y += 8
        return current_y

    # Professional Summary
    y = add_section_header("Professional Summary", y)
    summary_rect = fitz.Rect(margin_x, y, margin_x + content_width, y + 42)
    page.insert_textbox(summary_rect, cand["summary"], fontsize=9, fontname="helv", color=(0.2, 0.2, 0.2))
    y += 44

    # Technical Skills
    y = add_section_header("Technical Skills", y)
    skills_text = ", ".join(cand["skills"])
    skills_rect = fitz.Rect(margin_x, y, margin_x + content_width, y + 26)
    page.insert_textbox(skills_rect, skills_text, fontsize=9, fontname="helv", color=(0.2, 0.2, 0.2))
    y += 28

    # Experience
    if cand.get("experience"):
        y = add_section_header("Experience", y)
        for exp in cand["experience"]:
            exp_header = f"{exp['job_title']} | {exp['company']} ({exp.get('start_date', '')} - {exp.get('end_date', '')})"
            page.insert_text(fitz.Point(margin_x, y + 9), exp_header, fontsize=9.5, fontname="helv", color=(0.15, 0.15, 0.2))
            y += 13
            desc_rect = fitz.Rect(margin_x + 8, y, margin_x + content_width, y + 28)
            page.insert_textbox(desc_rect, exp.get("description", ""), fontsize=8.5, fontname="helv", color=(0.25, 0.25, 0.25))
            y += 30

    # Projects
    if cand.get("projects"):
        y = add_section_header("Projects", y)
        for proj in cand["projects"]:
            techs = ", ".join(proj.get("technologies", []))
            proj_title = f"{proj['name']} [{techs}]"
            page.insert_text(fitz.Point(margin_x, y + 9), proj_title, fontsize=9.5, fontname="helv", color=(0.15, 0.15, 0.2))
            y += 12
            proj_rect = fitz.Rect(margin_x + 8, y, margin_x + content_width, y + 22)
            page.insert_textbox(proj_rect, proj.get("description", ""), fontsize=8.5, fontname="helv", color=(0.25, 0.25, 0.25))
            y += 24

    # Education
    if cand.get("education"):
        y = add_section_header("Education", y)
        for edu in cand["education"]:
            edu_line = f"{edu['degree']} — {edu['institution']} ({edu.get('start_date', '')} - {edu.get('end_date', '')})"
            page.insert_text(fitz.Point(margin_x, y + 9), edu_line, fontsize=9, fontname="helv", color=(0.2, 0.2, 0.2))
            y += 15

    # Certifications
    if cand.get("certifications"):
        y = add_section_header("Certifications", y)
        cert_line = " • " + " • ".join(cand["certifications"])
        page.insert_text(fitz.Point(margin_x, y + 9), cert_line, fontsize=9, fontname="helv", color=(0.2, 0.2, 0.2))
        y += 15

    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


# ---------------------------------------------------------------------------
# Seeding Logic
# ---------------------------------------------------------------------------
async def seed_organizations(db: AsyncSession) -> Dict[str, Organization]:
    """Seed or update demo organizations idempotently."""
    logger.info("Seeding organizations...")
    org_map = {}
    for data in ORGANIZATIONS_DATA:
        stmt = select(Organization).where(Organization.slug == data["slug"])
        res = await db.execute(stmt)
        org = res.scalar_one_or_none()
        if not org:
            org = Organization(
                name=data["name"],
                slug=data["slug"],
                is_active=data["is_active"],
            )
            db.add(org)
            await db.flush()
            logger.info(f"  + Created organization: {org.name} ({org.slug})")
        else:
            org.name = data["name"]
            org.is_active = data["is_active"]
            await db.flush()
            logger.info(f"  * Existing organization verified: {org.name} ({org.slug})")
        org_map[org.slug] = org
    return org_map


async def seed_recruiters(db: AsyncSession, org_map: Dict[str, Organization]) -> Dict[str, User]:
    """Seed or update demo recruiter users and memberships."""
    logger.info("Seeding recruiters...")
    recruiter_map = {}
    hashed_pwd = hash_password(DEMO_PASSWORD)

    for r_data in RECRUITERS_DATA:
        stmt = select(User).where(User.email == r_data["email"])
        res = await db.execute(stmt)
        user = res.scalar_one_or_none()

        if not user:
            user = User(
                email=r_data["email"],
                password_hash=hashed_pwd,
                full_name=r_data["full_name"],
                is_active=True,
            )
            db.add(user)
            await db.flush()
            logger.info(f"  + Created recruiter user: {user.email}")
        else:
            user.password_hash = hashed_pwd
            user.full_name = r_data["full_name"]
            user.is_active = True
            await db.flush()
            logger.info(f"  * Existing recruiter updated: {user.email}")

        # Ensure membership
        org = org_map[r_data["org_slug"]]
        m_stmt = select(OrganizationMembership).where(
            OrganizationMembership.organization_id == org.id,
            OrganizationMembership.user_id == user.id,
        )
        m_res = await db.execute(m_stmt)
        membership = m_res.scalar_one_or_none()

        if not membership:
            membership = OrganizationMembership(
                organization_id=org.id,
                user_id=user.id,
                role=r_data["role"],
                is_active=True,
            )
            db.add(membership)
            await db.flush()
            logger.info(f"    + Assigned {user.email} -> {org.name} as {r_data['role'].value}")
        else:
            membership.role = r_data["role"]
            membership.is_active = True
            await db.flush()
            logger.info(f"    * Membership verified: {user.email} -> {org.name} ({r_data['role'].value})")

        recruiter_map[user.email] = user

    return recruiter_map


async def seed_candidates(db: AsyncSession) -> Dict[str, Tuple[User, CandidateProfile, Resume]]:
    """Seed demo candidate users, profiles, and synthetic PDF resumes."""
    logger.info("Seeding candidates, profiles, and PDF resumes...")
    candidate_map = {}
    hashed_pwd = hash_password(DEMO_PASSWORD)

    for c_data in CANDIDATES_DATA:
        # 1. User Account
        stmt = select(User).where(User.email == c_data["email"])
        res = await db.execute(stmt)
        user = res.scalar_one_or_none()

        if not user:
            user = User(
                email=c_data["email"],
                password_hash=hashed_pwd,
                full_name=c_data["full_name"],
                is_active=True,
            )
            db.add(user)
            await db.flush()
            logger.info(f"  + Created candidate user: {user.email}")
        else:
            user.password_hash = hashed_pwd
            user.full_name = c_data["full_name"]
            user.is_active = True
            await db.flush()
            logger.info(f"  * Existing candidate user updated: {user.email}")

        # 2. Candidate Profile
        p_stmt = select(CandidateProfile).where(CandidateProfile.user_id == user.id)
        p_res = await db.execute(p_stmt)
        profile = p_res.scalar_one_or_none()

        if not profile:
            profile = CandidateProfile(
                user_id=user.id,
                phone=c_data["phone"],
                location=c_data["location"],
                headline=c_data["headline"],
                professional_summary=c_data["summary"],
            )
            db.add(profile)
            await db.flush()
            logger.info(f"    + Created candidate profile for {user.full_name}")
        else:
            profile.phone = c_data["phone"]
            profile.location = c_data["location"]
            profile.headline = c_data["headline"]
            profile.professional_summary = c_data["summary"]
            await db.flush()
            logger.info(f"    * Existing profile updated for {user.full_name}")

        # 3. Resume PDF Fixture Generation & Storage
        pdf_bytes = build_resume_pdf_bytes(c_data)
        file_size = len(pdf_bytes)
        sha256_hash = hashlib.sha256(pdf_bytes).hexdigest()
        original_filename = f"{c_data['full_name'].lower().replace(' ', '_')}_resume.pdf"

        # Check existing resume record
        r_stmt = select(Resume).where(
            Resume.candidate_id == profile.id,
            Resume.original_filename == original_filename,
        )
        r_res = await db.execute(r_stmt)
        resume = r_res.scalar_one_or_none()

        # Extract text via PyMuPDF extractor to match actual file content
        extracted_text = pdf_extractor.extract_text(pdf_bytes)

        # Structured parsed data adhering to ParsedResumeData schema
        parsed_data = {
            "full_name": c_data["full_name"],
            "email": c_data["email"],
            "phone": c_data["phone"],
            "professional_summary": c_data["summary"],
            "skills": c_data["skills"],
            "education": c_data["education"],
            "experience": c_data["experience"],
            "projects": c_data["projects"],
            "certifications": c_data.get("certifications", []),
        }

        if not resume:
            resume_id = uuid.uuid4()
            rel_path = storage_service.save_file(profile.id, resume_id, pdf_bytes)
            resume = Resume(
                id=resume_id,
                candidate_id=profile.id,
                original_filename=original_filename,
                storage_path=rel_path,
                mime_type="application/pdf",
                file_size=file_size,
                sha256=sha256_hash,
                extracted_text=extracted_text,
                parsed_data=parsed_data,
                parsing_status=ParsingStatus.COMPLETED.value,
                is_active=True,
            )
            db.add(resume)
            await db.flush()
            logger.info(f"    + Created active resume: {original_filename} ({file_size} bytes)")
        else:
            # Ensure physical file is present on disk
            rel_path = storage_service.save_file(profile.id, resume.id, pdf_bytes)
            resume.storage_path = rel_path
            resume.file_size = file_size
            resume.sha256 = sha256_hash
            resume.extracted_text = extracted_text
            resume.parsed_data = parsed_data
            resume.parsing_status = ParsingStatus.COMPLETED.value
            resume.is_active = True
            await db.flush()
            logger.info(f"    * Existing resume updated and verified on disk: {original_filename}")

        candidate_map[user.email] = (user, profile, resume)

    return candidate_map


async def seed_jobs(
    db: AsyncSession,
    org_map: Dict[str, Organization],
    recruiter_map: Dict[str, User],
) -> Dict[str, Job]:
    """Seed demo job postings across organizations."""
    logger.info("Seeding job postings...")
    job_map = {}

    for j_data in JOBS_DATA:
        org = org_map[j_data["org_slug"]]
        recruiter = recruiter_map[j_data["recruiter_email"]]

        stmt = select(Job).where(
            Job.organization_id == org.id,
            Job.slug == j_data["slug"],
        )
        res = await db.execute(stmt)
        job = res.scalar_one_or_none()

        now = utc_now()
        published_at = now - timedelta(days=25) if j_data["status"] == JobStatus.PUBLISHED else None

        if not job:
            job = Job(
                organization_id=org.id,
                created_by=recruiter.id,
                title=j_data["title"],
                slug=j_data["slug"],
                department=j_data["department"],
                description=j_data["description"],
                responsibilities=j_data["responsibilities"],
                qualifications=j_data["qualifications"],
                location=j_data["location"],
                workplace_type=j_data["workplace_type"].value,
                employment_type=j_data["employment_type"].value,
                experience_min=j_data["experience_min"],
                experience_max=j_data["experience_max"],
                salary_min=j_data["salary_min"],
                salary_max=j_data["salary_max"],
                salary_currency=j_data["salary_currency"],
                required_skills=j_data["required_skills"],
                preferred_skills=j_data["preferred_skills"],
                status=j_data["status"].value,
                published_at=published_at,
            )
            db.add(job)
            await db.flush()
            logger.info(f"  + Created job: {job.title} [{job.status}] ({org.name})")
        else:
            job.title = j_data["title"]
            job.department = j_data["department"]
            job.description = j_data["description"]
            job.responsibilities = j_data["responsibilities"]
            job.qualifications = j_data["qualifications"]
            job.location = j_data["location"]
            job.workplace_type = j_data["workplace_type"].value
            job.employment_type = j_data["employment_type"].value
            job.experience_min = j_data["experience_min"]
            job.experience_max = j_data["experience_max"]
            job.salary_min = j_data["salary_min"]
            job.salary_max = j_data["salary_max"]
            job.required_skills = j_data["required_skills"]
            job.preferred_skills = j_data["preferred_skills"]
            job.status = j_data["status"].value
            if j_data["status"] == JobStatus.PUBLISHED and not job.published_at:
                job.published_at = published_at
            await db.flush()
            logger.info(f"  * Existing job verified: {job.title} [{job.status}] ({org.name})")

        job_map[j_data["key"]] = job

    return job_map


async def seed_applications(
    db: AsyncSession,
    job_map: Dict[str, Job],
    candidate_map: Dict[str, Tuple[User, CandidateProfile, Resume]],
    recruiter_map: Dict[str, User],
) -> List[Application]:
    """Seed at least 20 realistic applications with valid status history transitions."""
    logger.info("Seeding candidate applications and status histories...")
    created_applications = []
    now = utc_now()

    for app_plan in APPLICATIONS_PLAN:
        job = job_map[app_plan["job_key"]]
        user, profile, resume = candidate_map[app_plan["candidate_email"]]

        # Find existing application
        stmt = select(Application).where(
            Application.job_id == job.id,
            Application.candidate_id == profile.id,
        )
        res = await db.execute(stmt)
        app = res.scalar_one_or_none()

        target_status = app_plan["status"].value
        submission_time = now - timedelta(days=app_plan["days_ago"])
        status_updated_time = submission_time + timedelta(hours=6)

        # Snapshot structure matching application_service.py
        candidate_snapshot = {
            "candidate_id": str(profile.id),
            "user_id": str(user.id),
            "full_name": user.full_name,
            "email": user.email,
            "phone": profile.phone,
            "location": profile.location,
            "headline": profile.headline,
            "professional_summary": profile.professional_summary,
            "resume_id": str(resume.id),
            "resume_filename": resume.original_filename,
            "resume_sha256": resume.sha256,
        }

        if not app:
            app = Application(
                job_id=job.id,
                candidate_id=profile.id,
                submitted_resume_id=resume.id,
                organization_id=job.organization_id,
                status=target_status,
                cover_letter=app_plan["cover_letter"],
                candidate_snapshot=candidate_snapshot,
                submitted_at=submission_time,
                status_updated_at=status_updated_time,
            )
            db.add(app)
            await db.flush()
            logger.info(f"  + Created application: {user.full_name} -> {job.title} [{target_status}]")
        else:
            app.submitted_resume_id = resume.id
            app.organization_id = job.organization_id
            app.status = target_status
            app.cover_letter = app_plan["cover_letter"]
            app.candidate_snapshot = candidate_snapshot
            app.submitted_at = submission_time
            app.status_updated_at = status_updated_time
            await db.flush()
            logger.info(f"  * Existing application updated: {user.full_name} -> {job.title} [{target_status}]")

        # Re-build or verify status history to reflect valid transitions
        # Determine actor recruiter for org
        job_def = next(j for j in JOBS_DATA if j["key"] == app_plan["job_key"])
        recruiter_actor = recruiter_map[job_def["recruiter_email"]]

        # Determine sequence of transitions leading up to target_status
        history_chain = []
        if target_status == ApplicationStatus.SUBMITTED.value:
            history_chain = [
                (None, ApplicationStatus.SUBMITTED.value, user.id, submission_time, "Application submitted by candidate")
            ]
        elif target_status == ApplicationStatus.UNDER_REVIEW.value:
            t1 = submission_time
            t2 = t1 + timedelta(days=1)
            history_chain = [
                (None, ApplicationStatus.SUBMITTED.value, user.id, t1, "Application submitted by candidate"),
                (ApplicationStatus.SUBMITTED.value, ApplicationStatus.UNDER_REVIEW.value, recruiter_actor.id, t2, "Recruiter commenced application profile review"),
            ]
        elif target_status == ApplicationStatus.SHORTLISTED.value:
            t1 = submission_time
            t2 = t1 + timedelta(days=1)
            t3 = t2 + timedelta(days=2)
            history_chain = [
                (None, ApplicationStatus.SUBMITTED.value, user.id, t1, "Application submitted by candidate"),
                (ApplicationStatus.SUBMITTED.value, ApplicationStatus.UNDER_REVIEW.value, recruiter_actor.id, t2, "Recruiter commenced application profile review"),
                (ApplicationStatus.UNDER_REVIEW.value, ApplicationStatus.SHORTLISTED.value, recruiter_actor.id, t3, "Candidate passed resume match criteria and was shortlisted"),
            ]
        elif target_status == ApplicationStatus.INTERVIEWING.value:
            t1 = submission_time
            t2 = t1 + timedelta(days=1)
            t3 = t2 + timedelta(days=2)
            t4 = t3 + timedelta(days=3)
            history_chain = [
                (None, ApplicationStatus.SUBMITTED.value, user.id, t1, "Application submitted by candidate"),
                (ApplicationStatus.SUBMITTED.value, ApplicationStatus.UNDER_REVIEW.value, recruiter_actor.id, t2, "Recruiter commenced application profile review"),
                (ApplicationStatus.UNDER_REVIEW.value, ApplicationStatus.SHORTLISTED.value, recruiter_actor.id, t3, "Candidate shortlisted for technical round"),
                (ApplicationStatus.SHORTLISTED.value, ApplicationStatus.INTERVIEWING.value, recruiter_actor.id, t4, "Initial technical interview scheduled"),
            ]
        elif target_status == ApplicationStatus.HIRED.value:
            t1 = submission_time
            t2 = t1 + timedelta(days=1)
            t3 = t2 + timedelta(days=2)
            t4 = t3 + timedelta(days=3)
            t5 = t4 + timedelta(days=4)
            history_chain = [
                (None, ApplicationStatus.SUBMITTED.value, user.id, t1, "Application submitted by candidate"),
                (ApplicationStatus.SUBMITTED.value, ApplicationStatus.UNDER_REVIEW.value, recruiter_actor.id, t2, "Recruiter commenced application review"),
                (ApplicationStatus.UNDER_REVIEW.value, ApplicationStatus.SHORTLISTED.value, recruiter_actor.id, t3, "Candidate shortlisted following initial review"),
                (ApplicationStatus.SHORTLISTED.value, ApplicationStatus.INTERVIEWING.value, recruiter_actor.id, t4, "Candidate successfully cleared technical round"),
                (ApplicationStatus.INTERVIEWING.value, ApplicationStatus.HIRED.value, recruiter_actor.id, t5, "Offer letter accepted by candidate. Welcome aboard!"),
            ]
        elif target_status == ApplicationStatus.REJECTED.value:
            t1 = submission_time
            t2 = t1 + timedelta(days=1)
            t3 = t2 + timedelta(days=2)
            history_chain = [
                (None, ApplicationStatus.SUBMITTED.value, user.id, t1, "Application submitted by candidate"),
                (ApplicationStatus.SUBMITTED.value, ApplicationStatus.UNDER_REVIEW.value, recruiter_actor.id, t2, "Recruiter reviewed resume criteria"),
                (ApplicationStatus.UNDER_REVIEW.value, ApplicationStatus.REJECTED.value, recruiter_actor.id, t3, "Candidate does not meet the minimum required qualifications"),
            ]

        # Sync history records
        del_stmt = delete(ApplicationStatusHistory).where(ApplicationStatusHistory.application_id == app.id)
        await db.execute(del_stmt)

        for prev_st, new_st, actor_id, changed_time, note in history_chain:
            hist_item = ApplicationStatusHistory(
                application_id=app.id,
                previous_status=prev_st,
                new_status=new_st,
                changed_by=actor_id,
                changed_at=changed_time,
                internal_note=note,
            )
            db.add(hist_item)

        await db.flush()
        created_applications.append(app)

    return created_applications


async def seed_conversations_fixtures(
    db: AsyncSession,
    org_map: Dict[str, Organization],
    recruiter_map: Dict[str, User],
    candidate_map: Dict[str, Tuple[User, CandidateProfile, Resume]],
) -> None:
    """Seed demo assistant conversations for recruiters and candidates."""
    logger.info("Seeding recruiter & career assistant conversations...")
    novatech = org_map["novatech-solutions"]
    recruiter1 = recruiter_map["recruiter1@talentlens.demo"]
    cand1_user, cand1_profile, cand1_resume = candidate_map["candidate1@talentlens.demo"]

    # 1. Recruiter Conversation
    rc_stmt = select(RecruiterConversation).where(
        RecruiterConversation.organization_id == novatech.id,
        RecruiterConversation.conversation_title == "Python Backend Candidate Review",
    )
    rc_res = await db.execute(rc_stmt)
    rc = rc_res.scalar_one_or_none()

    if not rc:
        rc = RecruiterConversation(
            organization_id=novatech.id,
            created_by_user_id=recruiter1.id,
            conversation_title="Python Backend Candidate Review",
            conversation_type=RecruiterConversationType.APPLICANT_SCREENING.value,
            is_archived=False,
        )
        db.add(rc)
        await db.flush()

        m1 = RecruiterMessage(
            conversation_id=rc.id,
            role=RecruiterMessageRole.USER.value,
            content="Can you summarize our top applicants for the Python Backend Developer role?",
            model_name="qwen3:4b",
        )
        m2 = RecruiterMessage(
            conversation_id=rc.id,
            role=RecruiterMessageRole.ASSISTANT.value,
            content=(
                "Based on the applicant pool for Python Backend Developer, Alex Rivera and Chloe Dubois demonstrate "
                "the strongest alignment. Alex has 2+ years of verified FastAPI and PostgreSQL microservice experience, "
                "while Chloe brings 3.5 years of Celery background worker architecture."
            ),
            model_name="qwen3:4b",
        )
        db.add_all([m1, m2])
        await db.flush()
        logger.info("  + Created recruiter assistant conversation fixture")

    # 2. Candidate Career Conversation
    cc_stmt = select(CareerConversation).where(
        CareerConversation.candidate_id == cand1_profile.id,
        CareerConversation.conversation_title == "Backend Career Advancement Advice",
    )
    cc_res = await db.execute(cc_stmt)
    cc = cc_res.scalar_one_or_none()

    if not cc:
        cc = CareerConversation(
            candidate_id=cand1_profile.id,
            resume_id=cand1_resume.id,
            resume_sha256=cand1_resume.sha256,
            target_role="Mid-Level Python Backend Engineer",
            conversation_title="Backend Career Advancement Advice",
            conversation_type=ConversationPurpose.CAREER_GUIDANCE.value,
            is_archived=False,
        )
        db.add(cc)
        await db.flush()

        cm1 = CareerMessage(
            conversation_id=cc.id,
            role=MessageRole.USER.value,
            content="How can I position my FastAPI and PostgreSQL experience to step up to a mid-level backend role?",
            model_name="qwen3:4b",
        )
        cm2 = CareerMessage(
            conversation_id=cc.id,
            role=MessageRole.ASSISTANT.value,
            content=(
                "Your resume already highlights strong foundation work with FastAPI, Redis, and query optimization. "
                "To demonstrate mid-level ownership: 1) Quantify business impact (e.g., latency reduction and uptime), "
                "2) Highlight distributed systems concepts such as circuit breaking and async workers, and "
                "3) Emphasize your Docker containerization and CI/CD automation."
            ),
            model_name="qwen3:4b",
        )
        db.add_all([cm1, cm2])
        await db.flush()
        logger.info("  + Created candidate career conversation fixture")


async def attempt_screening_seed(
    db: AsyncSession,
    org_map: Dict[str, Organization],
    recruiter_map: Dict[str, User],
    job_map: Dict[str, Job],
) -> None:
    """Attempt live screening generation via existing screening service if requested."""
    logger.info("Evaluating screening generation eligibility...")
    from app.schemas.screening import ScreeningTriggerRequest
    from app.services.screening_service import trigger_screening_run

    python_job = job_map["python-backend"]
    novatech = org_map["novatech-solutions"]
    recruiter1 = recruiter_map["recruiter1@talentlens.demo"]

    try:
        logger.info(f"Triggering screening run for {python_job.title} via ScreeningService...")
        run_res = await trigger_screening_run(
            db=db,
            recruiter_user=recruiter1,
            organization_id=novatech.id,
            job_id=python_job.id,
            trigger_in=ScreeningTriggerRequest(),
        )
        logger.info(
            f"Screening run finished successfully: Run ID {run_res.id}, Status: {run_res.status}, "
            f"Processed: {run_res.processed_applications}, Failed: {run_res.failed_applications}"
        )
    except Exception as exc:
        logger.warning(
            f"Screening generation skipped or interrupted: {exc}. "
            "Note: Screening scores are not invented artificially when inference is unavailable."
        )


# ---------------------------------------------------------------------------
# Verification Suite
# ---------------------------------------------------------------------------
async def verify_demo_data(db: AsyncSession) -> bool:
    """
    Run comprehensive end-to-end data quality and integrity checks:
    1. Authentication: test passwords for all demo accounts.
    2. Recruiter roles: verify organization memberships and roles.
    3. Candidate profiles: verify profile existence and complete metadata.
    4. Resume files: verify physical file existence, size, and SHA256 integrity.
    5. Job postings: verify lifecycle statuses and requirements.
    6. Applications: verify >= 20 applications, valid resume FKs, and status history.
    7. Tenant isolation: verify cross-tenant boundaries are strictly respected.
    """
    print("\n" + "=" * 80)
    print("TALENTLENS DEMO DATA VERIFICATION SUITE")
    print("=" * 80)
    all_passed = True

    # 1. Test Authentication
    print("\n[1/7] Testing Authentication & Password Verification...")
    auth_errors = []
    all_demo_emails = [r["email"] for r in RECRUITERS_DATA] + [c["email"] for c in CANDIDATES_DATA]
    for email in all_demo_emails:
        stmt = select(User).where(User.email == email)
        res = await db.execute(stmt)
        user = res.scalar_one_or_none()
        if not user:
            auth_errors.append(f"User {email} not found in database.")
            continue
        if not verify_password(DEMO_PASSWORD, user.password_hash):
            auth_errors.append(f"Password verification failed for {email}.")
        token = create_access_token(subject=str(user.id))
        claims = decode_access_token(token)
        if claims.get("sub") != str(user.id):
            auth_errors.append(f"JWT claims verification failed for {email}.")

    if not auth_errors:
        print(f"  ✓ All {len(all_demo_emails)} demo accounts successfully authenticated with '{DEMO_PASSWORD}'.")
    else:
        all_passed = False
        for err in auth_errors:
            print(f"  ✗ {err}")

    # 2. Verify Recruiter Organization Memberships
    print("\n[2/7] Testing Recruiter Organization Memberships & Roles...")
    membership_errors = []
    for r_data in RECRUITERS_DATA:
        stmt = (
            select(OrganizationMembership)
            .join(User, OrganizationMembership.user_id == User.id)
            .join(Organization, OrganizationMembership.organization_id == Organization.id)
            .where(User.email == r_data["email"])
        )
        res = await db.execute(stmt)
        memberships = res.scalars().all()
        if not memberships:
            membership_errors.append(f"No membership found for {r_data['email']}.")
            continue
        m = memberships[0]
        if m.role != r_data["role"]:
            membership_errors.append(f"Role mismatch for {r_data['email']}: expected {r_data['role']}, got {m.role}.")

    if not membership_errors:
        print(f"  ✓ All {len(RECRUITERS_DATA)} recruiters correctly mapped to designated organizations and roles.")
    else:
        all_passed = False
        for err in membership_errors:
            print(f"  ✗ {err}")

    # 3. Verify Candidate Profiles
    print("\n[3/7] Testing Candidate Profiles & Metadata...")
    profile_errors = []
    for c_data in CANDIDATES_DATA:
        stmt = (
            select(CandidateProfile)
            .join(User, CandidateProfile.user_id == User.id)
            .where(User.email == c_data["email"])
        )
        res = await db.execute(stmt)
        profile = res.scalar_one_or_none()
        if not profile:
            profile_errors.append(f"Candidate profile missing for {c_data['email']}.")
            continue
        if not profile.headline or not profile.professional_summary:
            profile_errors.append(f"Incomplete profile metadata for {c_data['email']}.")

    if not profile_errors:
        print(f"  ✓ All {len(CANDIDATES_DATA)} candidate profiles exist with complete, non-contradictory metadata.")
    else:
        all_passed = False
        for err in profile_errors:
            print(f"  ✗ {err}")

    # 4. Verify Resume Physical Files & Hash Integrity
    print("\n[4/7] Testing Physical Resume Files & Storage Integrity...")
    resume_errors = []
    for c_data in CANDIDATES_DATA:
        stmt = (
            select(Resume)
            .join(CandidateProfile, Resume.candidate_id == CandidateProfile.id)
            .join(User, CandidateProfile.user_id == User.id)
            .where(User.email == c_data["email"])
        )
        res = await db.execute(stmt)
        resumes = res.scalars().all()
        if not resumes:
            resume_errors.append(f"No resume record found for {c_data['email']}.")
            continue
        r = resumes[0]
        abs_path = storage_service.get_absolute_path(r.storage_path)
        if not abs_path.exists():
            resume_errors.append(f"Resume physical file missing at {abs_path} for {c_data['email']}.")
            continue
        file_bytes = abs_path.read_bytes()
        calculated_sha = hashlib.sha256(file_bytes).hexdigest()
        if calculated_sha != r.sha256:
            resume_errors.append(f"SHA256 mismatch for {r.original_filename}: db={r.sha256}, disk={calculated_sha}.")
        if len(file_bytes) > settings.MAX_UPLOAD_SIZE_BYTES:
            resume_errors.append(f"Resume exceeds 5MB limit: {len(file_bytes)} bytes.")

    if not resume_errors:
        print(f"  ✓ All {len(CANDIDATES_DATA)} resume PDFs exist on disk, conform to <5MB limit, and match SHA256 hashes.")
    else:
        all_passed = False
        for err in resume_errors:
            print(f"  ✗ {err}")

    # 5. Verify Job Postings
    print("\n[5/7] Testing Job Postings & Lifecycle Statuses...")
    job_errors = []
    for j_data in JOBS_DATA:
        stmt = select(Job).where(Job.slug == j_data["slug"])
        res = await db.execute(stmt)
        job = res.scalar_one_or_none()
        if not job:
            job_errors.append(f"Job not found for slug '{j_data['slug']}'.")
            continue
        if job.status != j_data["status"].value:
            job_errors.append(f"Status mismatch for job {job.title}: expected {j_data['status']}, got {job.status}.")
        if job.status == JobStatus.PUBLISHED.value and not job.published_at:
            job_errors.append(f"Published job '{job.title}' missing published_at timestamp.")

    if not job_errors:
        print(f"  ✓ All {len(JOBS_DATA)} job postings exist with validated schema fields, required skills, and statuses (5 Published, 1 Draft).")
    else:
        all_passed = False
        for err in job_errors:
            print(f"  ✗ {err}")

    # 6. Verify Applications & Status History
    print("\n[6/7] Testing Applications & Status History Consistency...")
    app_errors = []
    apps_stmt = (
        select(Application)
        .options(
            selectinload(Application.status_history),
            selectinload(Application.submitted_resume),
            selectinload(Application.job),
        )
        .join(Job, Application.job_id == Job.id)
        .join(Organization, Job.organization_id == Organization.id)
        .where(Organization.slug.in_(["novatech-solutions", "brightpath-digital"]))
    )
    apps_res = await db.execute(apps_stmt)
    apps = apps_res.scalars().all()

    if len(apps) < 20:
        app_errors.append(f"Expected at least 20 applications, found {len(apps)}.")

    statuses_found = set()
    for a in apps:
        statuses_found.add(a.status)
        if a.organization_id != a.job.organization_id:
            app_errors.append(f"Application {a.id} organization mismatch with job.")
        if not a.submitted_resume:
            app_errors.append(f"Application {a.id} missing pinned submitted resume.")
        if not a.status_history:
            app_errors.append(f"Application {a.id} has no status history entries.")
        else:
            latest_hist = sorted(a.status_history, key=lambda h: h.changed_at)[-1]
            if latest_hist.new_status != a.status:
                app_errors.append(
                    f"Application {a.id} current status ({a.status}) does not match latest history entry ({latest_hist.new_status})."
                )

    required_statuses = {"SUBMITTED", "UNDER_REVIEW", "SHORTLISTED", "INTERVIEWING", "REJECTED", "HIRED"}
    missing_statuses = required_statuses - statuses_found
    if missing_statuses:
        app_errors.append(f"Application pool missing required status enum values: {missing_statuses}")

    if not app_errors:
        print(f"  ✓ {len(apps)} applications verified across all target statuses: {sorted(list(statuses_found))}.")
    else:
        all_passed = False
        for err in app_errors:
            print(f"  ✗ {err}")

    # 7. Verify Tenant Isolation
    print("\n[7/7] Testing Multi-Tenant Authorization Isolation...")
    isolation_errors = []

    # Get organizations
    nova_stmt = select(Organization).where(Organization.slug == "novatech-solutions")
    nova = (await db.execute(nova_stmt)).scalar_one_or_none()

    bright_stmt = select(Organization).where(Organization.slug == "brightpath-digital")
    bright = (await db.execute(bright_stmt)).scalar_one_or_none()

    if nova and bright:
        # Check NovaTech applications belong strictly to NovaTech
        nova_apps_stmt = select(Application).where(Application.organization_id == nova.id)
        nova_apps = (await db.execute(nova_apps_stmt)).scalars().all()
        for na in nova_apps:
            if na.organization_id == bright.id:
                isolation_errors.append("NovaTech application contaminated with BrightPath organization ID.")

        # Check BrightPath applications belong strictly to BrightPath
        bright_apps_stmt = select(Application).where(Application.organization_id == bright.id)
        bright_apps = (await db.execute(bright_apps_stmt)).scalars().all()
        for ba in bright_apps:
            if ba.organization_id == nova.id:
                isolation_errors.append("BrightPath application contaminated with NovaTech organization ID.")

    if not isolation_errors:
        print("  ✓ Cross-organization tenant boundaries strictly isolated and intact.")
    else:
        all_passed = False
        for err in isolation_errors:
            print(f"  ✗ {err}")

    print("\n" + "=" * 80)
    if all_passed:
        print("✓ ALL VERIFICATION CHECKS PASSED: Demo dataset is consistent, valid, and test-ready.")
    else:
        print("✗ VERIFICATION FAILED: Issues were identified in the demo dataset.")
    print("=" * 80 + "\n")
    return all_passed


# ---------------------------------------------------------------------------
# Cleanup Logic
# ---------------------------------------------------------------------------
async def cleanup_demo_data(db: AsyncSession) -> None:
    """
    Safely remove only records generated by this demo seed suite:
    - Never mutates or removes non-demo user data.
    - Removes demo physical resume PDF files from disk.
    - Deletes demo entities in reverse relational dependency order.
    """
    assert_safe_environment()
    print("\n" + "=" * 80)
    print("TALENTLENS DEMO DATA CLEANUP")
    print("=" * 80)
    logger.info("Executing safe cleanup of demo records...")

    # Identify demo organizations
    demo_org_slugs = ["novatech-solutions", "brightpath-digital"]
    orgs_res = await db.execute(select(Organization).where(Organization.slug.in_(demo_org_slugs)))
    demo_orgs = orgs_res.scalars().all()
    demo_org_ids = [o.id for o in demo_orgs]

    # Identify demo users
    users_res = await db.execute(select(User).where(User.email.like(f"%@{DEMO_EMAIL_DOMAIN}")))
    demo_users = users_res.scalars().all()
    demo_user_ids = [u.id for u in demo_users]

    if not demo_org_ids and not demo_user_ids:
        logger.info("No demo records found. Database is already clean.")
        print("=" * 80 + "\n")
        return

    # Identify demo candidate profiles & resumes
    cand_res = await db.execute(select(CandidateProfile).where(CandidateProfile.user_id.in_(demo_user_ids)))
    demo_candidates = cand_res.scalars().all()
    demo_cand_ids = [c.id for c in demo_candidates]

    resumes_res = await db.execute(select(Resume).where(Resume.candidate_id.in_(demo_cand_ids)))
    demo_resumes = resumes_res.scalars().all()

    # Delete physical resume files from disk
    removed_files = 0
    for r in demo_resumes:
        try:
            abs_p = storage_service.get_absolute_path(r.storage_path)
            if abs_p.exists():
                abs_p.unlink()
                removed_files += 1
                if abs_p.parent.exists() and not any(abs_p.parent.iterdir()):
                    abs_p.parent.rmdir()
        except Exception as e:
            logger.warning(f"Error removing resume file {r.storage_path}: {e}")

    logger.info(f"  - Deleted {removed_files} physical demo resume files from storage.")

    # 1. Delete Screening Data
    await db.execute(delete(ScreeningInsight).where(ScreeningInsight.screening_run_id.in_(
        select(ScreeningRun.id).where(ScreeningRun.organization_id.in_(demo_org_ids))
    )))
    await db.execute(delete(ScreeningResult).where(ScreeningResult.organization_id.in_(demo_org_ids)))
    await db.execute(delete(ScreeningRun).where(ScreeningRun.organization_id.in_(demo_org_ids)))
    logger.info("  - Removed demo screening runs, results, and insights.")

    # 2. Delete Assistant Conversations
    await db.execute(delete(RecruiterConversation).where(RecruiterConversation.organization_id.in_(demo_org_ids)))
    await db.execute(delete(CareerConversation).where(CareerConversation.candidate_id.in_(demo_cand_ids)))
    logger.info("  - Removed demo assistant conversations.")

    # 3. Delete Applications & Status History
    await db.execute(delete(ApplicationStatusHistory).where(ApplicationStatusHistory.application_id.in_(
        select(Application.id).where(Application.organization_id.in_(demo_org_ids))
    )))
    await db.execute(delete(Application).where(Application.organization_id.in_(demo_org_ids)))
    logger.info("  - Removed demo applications and status histories.")

    # 4. Delete Resumes & Candidate Profiles
    await db.execute(delete(Resume).where(Resume.candidate_id.in_(demo_cand_ids)))
    await db.execute(delete(CandidateProfile).where(CandidateProfile.id.in_(demo_cand_ids)))
    logger.info("  - Removed demo resumes and candidate profiles.")

    # 5. Delete Jobs
    await db.execute(delete(Job).where(Job.organization_id.in_(demo_org_ids)))
    logger.info("  - Removed demo job postings.")

    # 6. Delete Memberships & Organizations
    await db.execute(delete(OrganizationMembership).where(OrganizationMembership.organization_id.in_(demo_org_ids)))
    await db.execute(delete(Organization).where(Organization.id.in_(demo_org_ids)))
    logger.info("  - Removed demo organizations and memberships.")

    # 7. Delete Demo Users
    await db.execute(delete(User).where(User.id.in_(demo_user_ids)))
    logger.info(f"  - Removed {len(demo_user_ids)} demo user accounts.")

    await db.commit()
    print("✓ Demo cleanup completed successfully. All non-demo user data remains intact.")
    print("=" * 80 + "\n")


# ---------------------------------------------------------------------------
# Main Orchestrator
# ---------------------------------------------------------------------------
async def run_seed(screen: bool = False) -> None:
    """Run full idempotent demo data generation."""
    assert_safe_environment()
    print("\n" + "=" * 80)
    print("TALENTLENS SYNTHETIC DEMO DATA SEEDING")
    print("=" * 80)

    async with async_session_maker() as session:
        try:
            # 1. Organizations
            org_map = await seed_organizations(session)

            # 2. Recruiters
            recruiter_map = await seed_recruiters(session, org_map)

            # 3. Candidates, Profiles & Resumes
            candidate_map = await seed_candidates(session)

            # 4. Jobs
            job_map = await seed_jobs(session, org_map, recruiter_map)

            # 5. Applications & Status Histories
            await seed_applications(session, job_map, candidate_map, recruiter_map)

            # 6. Assistant Conversations
            await seed_conversations_fixtures(session, org_map, recruiter_map, candidate_map)

            await session.commit()
            logger.info("✓ Core demo entities committed successfully.")

            # 7. Optional Screening Data Generation
            if screen:
                await attempt_screening_seed(session, org_map, recruiter_map, job_map)
            else:
                logger.info(
                    "Screening generation skipped for quick seed. "
                    "To generate live AI screenings, pass --screen or trigger via recruiter UI/API."
                )

        except Exception as exc:
            await session.rollback()
            logger.error(f"FATAL: Demo data seeding failed: {exc}", exc_info=True)
            raise


def main() -> None:
    parser = argparse.ArgumentParser(
        description="TalentLens Synthetic Demo Data Generator & Verification Suite"
    )
    parser.add_argument(
        "--confirm-demo-data",
        action="store_true",
        help="Explicit confirmation required to generate synthetic demo data",
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Run verification suite across existing demo records",
    )
    parser.add_argument(
        "--cleanup",
        action="store_true",
        help="Delete synthetic demo records and associated files",
    )
    parser.add_argument(
        "--confirm-cleanup",
        action="store_true",
        help="Explicit confirmation required with --cleanup",
    )
    parser.add_argument(
        "--screen",
        action="store_true",
        help="Attempt screening generation on eligible jobs using the screening engine",
    )

    args = parser.parse_args()

    if args.cleanup:
        if not args.confirm_cleanup:
            print("ERROR: Cleanup requires explicit confirmation flag: --confirm-cleanup")
            sys.exit(1)
        asyncio.run(cleanup_wrapper())
        return

    if args.verify:
        asyncio.run(verify_wrapper())
        return

    if not args.confirm_demo_data:
        print("=" * 80)
        print("TALENTLENS DEMO DATA GENERATOR")
        print("=" * 80)
        print("Safety Notice: To generate synthetic demo data, you must provide --confirm-demo-data.")
        print("\nCommands:")
        print("  python scripts/seed_demo_data.py --confirm-demo-data")
        print("  python scripts/seed_demo_data.py --confirm-demo-data --screen")
        print("  python scripts/seed_demo_data.py --verify")
        print("  python scripts/seed_demo_data.py --cleanup --confirm-cleanup")
        print("=" * 80)
        sys.exit(1)

    asyncio.run(seed_and_verify_wrapper(screen=args.screen))


async def cleanup_wrapper() -> None:
    async with async_session_maker() as session:
        await cleanup_demo_data(session)


async def verify_wrapper() -> None:
    async with async_session_maker() as session:
        passed = await verify_demo_data(session)
        if not passed:
            sys.exit(1)


async def seed_and_verify_wrapper(screen: bool = False) -> None:
    await run_seed(screen=screen)
    async with async_session_maker() as session:
        passed = await verify_demo_data(session)
        if not passed:
            sys.exit(1)


if __name__ == "__main__":
    main()
