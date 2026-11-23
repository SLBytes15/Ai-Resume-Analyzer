"""
TalentLens Synthetic Resume Generator
Generates 12 realistic, professionally formatted PDF resumes spanning:
- 4 Freshers
- 4 Internship-level candidates
- 3 Early Career (1-2 years experience)
- 1 Mid-level (~3 years experience)

Quality Profiles:
- 3 Strong (Structured, high ATS readability, quantified metrics)
- 4 Average (Standard single-column layout, clean formatting)
- 3 Basic (Minimalist, concise bullet points)
- 2 Challenging (Unusual section ordering, dense compact layout, embedded skills)
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, List

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    HRFlowable,
    Table,
    TableStyle,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY


CANDIDATES_DATA: List[Dict[str, Any]] = [
    {
        "id": "candidate01",
        "file_name": "candidate01_resume.pdf",
        "full_name": "Aarav Sharma",
        "category": "Fresher",
        "years_experience": 0.0,
        "quality": "Strong",
        "email": "aarav.sharma.demo@talentlens.fictional",
        "phone": "+91-98765-01001",
        "location": "Bengaluru, Karnataka, India",
        "professional_summary": "Disciplined Computer Science graduate with strong foundations in algorithmic problem solving, Python development, and relational database architecture. Proven track record building functional web APIs and algorithmic pipelines through intensive academic capstone projects. Eager to contribute to production engineering teams.",
        "skills": ["Python", "SQL", "PostgreSQL", "Git", "Data Structures", "Algorithms", "Linux", "Flask", "Docker"],
        "education": [
            {
                "institution": "National Institute of Technology Karnataka (NITK)",
                "degree": "Bachelor of Technology",
                "field_of_study": "Computer Science and Engineering",
                "start_date": "Aug 2020",
                "end_date": "May 2024",
                "details": "CGPA: 8.8 / 10.0 • Relevant Coursework: Data Structures & Algorithms, Database Management Systems, Operating Systems, Computer Networks"
            }
        ],
        "experience": [],
        "projects": [
            {
                "name": "Distributed Task Queue & Scheduler",
                "technologies": ["Python", "Redis", "PostgreSQL", "Docker", "Git"],
                "problem": "High computational latency when processing asynchronous batch jobs in single-threaded Python services.",
                "contribution": "Engineered worker pooling algorithm, error retry logic with exponential backoff, and PostgreSQL job state persistence.",
                "implementation": "Built asynchronous worker processes communicating over Redis pub/sub channels with transactional status updates in PostgreSQL.",
                "results": "Achieved 450 tasks/second throughput with zero message loss across synthetic test workloads."
            },
            {
                "name": "Algorithmic Market Data Ingestion Pipeline",
                "technologies": ["Python", "SQLite", "Data Structures", "Git"],
                "problem": "Unreliable data ingestion from disparate financial simulation feeds with varying JSON schemas.",
                "contribution": "Designed parsing schemas, circular buffer data structures, and optimized SQL batch insert statements.",
                "implementation": "Streamed ticker feeds into circular memory buffers and batched commits in 500-record chunks into relational storage.",
                "results": "Reduced data parsing overhead by 34% compared to baseline naive loops."
            }
        ],
        "certifications": [
            "Python Certified Associate Programmer (PCAP)",
            "HackerRank Problem Solving (Advanced)"
        ]
    },
    {
        "id": "candidate02",
        "file_name": "candidate02_resume.pdf",
        "full_name": "Priya Patel",
        "category": "Fresher",
        "years_experience": 0.0,
        "quality": "Average",
        "email": "priya.patel.demo@talentlens.fictional",
        "phone": "+91-98765-01002",
        "location": "Pune, Maharashtra, India",
        "professional_summary": "Motivated frontend-oriented graduate passionate about building clean, responsive user interfaces and interactive web applications using modern JavaScript and React. Seeking a junior frontend developer position.",
        "skills": ["React", "JavaScript", "HTML5", "CSS3", "Tailwind CSS", "Git", "Node.js"],
        "education": [
            {
                "institution": "Pune Institute of Computer Technology (PICT)",
                "degree": "Bachelor of Engineering",
                "field_of_study": "Information Technology",
                "start_date": "Aug 2020",
                "end_date": "May 2024",
                "details": "CGPA: 8.2 / 10.0"
            }
        ],
        "experience": [],
        "projects": [
            {
                "name": "Campus Event Portal",
                "technologies": ["React", "JavaScript", "Tailwind CSS", "Git"],
                "problem": "Student organizations lacked a centralized portal to register and manage attendees for university workshops.",
                "contribution": "Developed responsive UI components, user registration modals, and integrated client-side form validation.",
                "implementation": "Used React functional components, hooks (useState, useEffect), and Tailwind utility classes for mobile responsiveness.",
                "results": "Adopted by 4 university clubs for their annual symposium with 600+ registered attendees."
            },
            {
                "name": "Personal Budget Visualizer",
                "technologies": ["React", "HTML5", "CSS3", "JavaScript"],
                "problem": "Complex personal expense tracking spreadsheets that were difficult to interpret on mobile devices.",
                "contribution": "Built interactive expense breakdown graphs, categorized budget limits, and local storage data persistence.",
                "implementation": "Integrated Chart.js inside React wrapper components with browser localStorage for zero-backend persistence.",
                "results": "Provided real-time dynamic visual feedback with smooth rendering across mobile viewports."
            }
        ],
        "certifications": [
            "Meta Front-End Developer Specialization (Coursera)"
        ]
    },
    {
        "id": "candidate03",
        "file_name": "candidate03_resume.pdf",
        "full_name": "Liam O'Connor",
        "category": "Fresher",
        "years_experience": 0.0,
        "quality": "Basic",
        "email": "liam.oconnor.demo@talentlens.fictional",
        "phone": "+353-87-555-0103",
        "location": "Dublin, Ireland",
        "professional_summary": "Recent Computer Applications graduate with foundational knowledge in Java and C++ programming. Seeking an entry-level software developer position.",
        "skills": ["Java", "C++", "Object-Oriented Programming", "SQL", "Git"],
        "education": [
            {
                "institution": "Dublin City University",
                "degree": "Bachelor of Science",
                "field_of_study": "Computer Applications",
                "start_date": "Sep 2020",
                "end_date": "Jun 2024",
                "details": "Second Class Honours (2:1)"
            }
        ],
        "experience": [],
        "projects": [
            {
                "name": "Inventory Management Desktop App",
                "technologies": ["Java", "Swing", "SQLite"],
                "problem": "Local bookstore needed a desktop tool to catalogue book stock without manual paper records.",
                "contribution": "Created GUI forms and connected to local SQLite database for inventory tracking.",
                "implementation": "Java Swing table views connected via JDBC to a local SQLite schema.",
                "results": "Enabled searching books by title and ISBN without manual ledger lookups."
            },
            {
                "name": "Console Graph Path Finder",
                "technologies": ["C++", "Data Structures"],
                "problem": "Academic assignment to find shortest paths across simulated rail routes.",
                "contribution": "Implemented Dijkstra algorithm on adjacency matrices in C++.",
                "implementation": "Standard template library (STL) priority queues with adjacency list graph representations.",
                "results": "Successfully computed shortest distances across graph models up to 100 nodes."
            }
        ],
        "certifications": [
            "Oracle Certified Foundations Associate, Java"
        ]
    },
    {
        "id": "candidate04",
        "file_name": "candidate04_resume.pdf",
        "full_name": "Rohan Gupta",
        "category": "Fresher",
        "years_experience": 0.0,
        "quality": "Challenging",
        "email": "rohan.gupta.demo@talentlens.fictional",
        "phone": "+91-98765-01004",
        "location": "Noida, Uttar Pradesh, India",
        "professional_summary": "Graduate enthusiast interested in Python backend scripting, automation, and exploratory data workflows. Enjoys diving into tricky bugs and building pragmatic scripts.",
        "skills": ["Python", "SQL", "Pandas", "Git", "Linux", "Bash", "C"],
        "education": [
            {
                "institution": "Amity University Uttar Pradesh",
                "degree": "Bachelor of Technology",
                "field_of_study": "Computer Science",
                "start_date": "Aug 2020",
                "end_date": "May 2024",
                "details": "CGPA: 7.9 / 10.0"
            }
        ],
        "experience": [
            {
                "company": "Open Source Student Community",
                "job_title": "Student Volunteer & Club Mentor",
                "start_date": "Aug 2023",
                "end_date": "Apr 2024",
                "description": "Mentored 30+ junior students on programming fundamentals, conducted weekly Git workshops, and organized campus hackathons."
            }
        ],
        "projects": [
            {
                "name": "Document Text Categorizer",
                "technologies": ["Python", "Pandas", "Scikit-learn", "Git"],
                "problem": "Sorting academic research papers manually by subject was tedious.",
                "contribution": "Built Python script to parse text and cluster documents into topic categories.",
                "implementation": "TF-IDF vectorizer pipeline combined with K-Means clustering algorithm.",
                "results": "Grouped 200+ academic papers into 5 distinct categories automatically."
            },
            {
                "name": "Automated Web Scraper & Alert System",
                "technologies": ["Python", "BeautifulSoup", "SQLite"],
                "problem": "Tracking pricing fluctuations across tech hardware retailers required manual page visits.",
                "contribution": "Authored resilient scraping routines with user-agent rotation and SQLite storage.",
                "implementation": "Automated cronjob script parsing HTML DOM structures and sending email notifications.",
                "results": "Captured daily price deltas across 12 product listings."
            }
        ],
        "certifications": [
            "Coursera Applied Data Science with Python"
        ]
    },
    {
        "id": "candidate05",
        "file_name": "candidate05_resume.pdf",
        "full_name": "Ananya Iyer",
        "category": "Internship",
        "years_experience": 0.75,
        "quality": "Strong",
        "email": "ananya.iyer.demo@talentlens.fictional",
        "phone": "+91-98765-01005",
        "location": "Bengaluru, Karnataka, India",
        "professional_summary": "Proactive Software Engineering graduate with 9 months of combined frontend internship experience. Proficient in React, TypeScript, and modern CSS architecture, with a solid record of improving UI responsiveness and code maintainability.",
        "skills": ["React", "TypeScript", "JavaScript", "HTML5", "CSS3", "Tailwind CSS", "Redux Toolkit", "Jest", "Git", "REST APIs"],
        "education": [
            {
                "institution": "RV College of Engineering",
                "degree": "Bachelor of Engineering",
                "field_of_study": "Computer Science",
                "start_date": "Aug 2020",
                "end_date": "May 2024",
                "details": "CGPA: 9.1 / 10.0 • Dean's Honour List"
            }
        ],
        "experience": [
            {
                "company": "NexaHealth Tech",
                "job_title": "Frontend Engineering Intern",
                "start_date": "Jan 2024",
                "end_date": "Jun 2024",
                "description": "Developed patient appointment booking interface using React and TypeScript. Re-architected appointment calendar component, reducing render times by 42%. Authored 35+ unit tests using Jest and React Testing Library to achieve 88% component test coverage."
            },
            {
                "company": "FinEdge Solutions",
                "job_title": "Web Development Intern",
                "start_date": "Jun 2023",
                "end_date": "Aug 2023",
                "description": "Built responsive landing pages and dashboard widgets using Tailwind CSS and React. Collaborated with UX designers to align components with WCAG 2.1 AA accessibility guidelines."
            }
        ],
        "projects": [
            {
                "name": "Design System UI Kit",
                "technologies": ["React", "TypeScript", "Tailwind CSS", "Storybook"],
                "problem": "Inconsistent buttons, modals, and typography across internal web prototypes.",
                "contribution": "Authored 18 reusable accessible atomic components with strict TypeScript prop contracts and automated accessibility audits.",
                "implementation": "Configured Storybook documentation workbench with automated Axe-core accessibility linter checks.",
                "results": "Adopted across 3 university hackathon projects, saving development time by ~30%."
            },
            {
                "name": "Collaborative Whiteboard Canvas",
                "technologies": ["React", "TypeScript", "WebSocket", "HTML5 Canvas"],
                "problem": "Remote student teams needed a lightweight shared sketching canvas without heavy enterprise signups.",
                "contribution": "Implemented vector drawing engine with undo/redo history stack and live synchronization.",
                "implementation": "Custom HTML5 Canvas rendering loop synchronized via WebSocket binary payloads.",
                "results": "Maintained sub-16ms render loop handling up to 50 concurrent cursor updates."
            }
        ],
        "certifications": [
            "AWS Certified Cloud Practitioner",
            "FreeCodeCamp Responsive Web Design"
        ]
    },
    {
        "id": "candidate06",
        "file_name": "candidate06_resume.pdf",
        "full_name": "Marcus Vance",
        "category": "Internship",
        "years_experience": 0.42,
        "quality": "Average",
        "email": "marcus.vance.demo@talentlens.fictional",
        "phone": "+1-512-555-0106",
        "location": "Austin, Texas, USA",
        "professional_summary": "Backend-focused computer science graduate with 5 months internship experience creating Python microservices, relational schemas, and automated REST endpoints. Solid foundation in asynchronous programming and API design.",
        "skills": ["Python", "FastAPI", "PostgreSQL", "Git", "Docker", "REST APIs", "Linux", "SQL"],
        "education": [
            {
                "institution": "University of Texas at Dallas",
                "degree": "Bachelor of Science",
                "field_of_study": "Computer Science",
                "start_date": "Aug 2020",
                "end_date": "May 2024",
                "details": "GPA: 3.6 / 4.0"
            }
        ],
        "experience": [
            {
                "company": "CloudStart Labs",
                "job_title": "Software Engineering Intern (Backend)",
                "start_date": "Feb 2024",
                "end_date": "Jun 2024",
                "description": "Assisted senior engineers in migrating legacy Flask endpoints to FastAPI. Wrote async database queries in PostgreSQL and added request payload validation using Pydantic. Implemented integration tests covering 12 core API routes."
            }
        ],
        "projects": [
            {
                "name": "Telemetry Ingestion Service",
                "technologies": ["Python", "FastAPI", "PostgreSQL", "Docker"],
                "problem": "IoT sensor nodes were dropping packets during sudden network spikes.",
                "contribution": "Built an asynchronous ingestion gateway that buffers incoming payloads and persists batch records into PostgreSQL.",
                "implementation": "Utilized FastAPI background tasks and asyncpg connection pools to write batched metric points.",
                "results": "Successfully absorbed simulated bursts of 1,000 requests/minute without HTTP 500 errors."
            },
            {
                "name": "Developer CLI Tool",
                "technologies": ["Python", "Click", "Git"],
                "problem": "Local environment setup for new lab contributors took over 2 hours of manual configuration.",
                "contribution": "Packaged a command-line script automating git hook installation and environment variable checks.",
                "implementation": "Built Python Click CLI that validates local dependencies, Docker daemon status, and seeds database fixtures.",
                "results": "Reduced newcomer onboarding setup time to under 10 minutes."
            }
        ],
        "certifications": [
            "PostgreSQL Database Administration (Coursera)"
        ]
    },
    {
        "id": "candidate07",
        "file_name": "candidate07_resume.pdf",
        "full_name": "Elena Rostova",
        "category": "Internship",
        "years_experience": 0.33,
        "quality": "Average",
        "email": "elena.rostova.demo@talentlens.fictional",
        "phone": "+49-30-555-0107",
        "location": "Berlin, Germany",
        "professional_summary": "Systems and cloud-oriented graduate with practical internship experience in Linux systems administration, Docker containerization, and automated CI/CD pipelines.",
        "skills": ["Linux", "Docker", "AWS", "Git", "CI/CD", "Bash", "Python", "Kubernetes"],
        "education": [
            {
                "institution": "Technical University of Berlin",
                "degree": "Bachelor of Science",
                "field_of_study": "Computer Systems & Informatics",
                "start_date": "Oct 2020",
                "end_date": "May 2024",
                "details": "Grade: 1.7 (German Scale)"
            }
        ],
        "experience": [
            {
                "company": "KubeScale GmbH",
                "job_title": "DevOps & Infrastructure Intern",
                "start_date": "Mar 2024",
                "end_date": "Jul 2024",
                "description": "Maintained staging Docker container environments on AWS EC2 instances. Configured GitHub Actions workflows for automated linting, test execution, and container image builds. Wrote Bash scripts for automated log rotation and storage health checks."
            }
        ],
        "projects": [
            {
                "name": "Self-Healing Container Daemon",
                "technologies": ["Docker", "Python", "Bash", "Linux"],
                "problem": "Staging container services occasionally hung without triggering orchestrator alerts.",
                "contribution": "Developed a daemon monitor that checks HTTP health endpoints and automatically restarts unhealthy containers.",
                "implementation": "Monitored container health checks via Docker socket API with automated alert dispatches to Slack webhooks.",
                "results": "Decreased staging downtime during internal testing by 60%."
            },
            {
                "name": "Automated AWS Backup Pipeline",
                "technologies": ["AWS S3", "Bash", "PostgreSQL", "Linux Crontab"],
                "problem": "Manual database backups were prone to human error and lacked verification.",
                "contribution": "Automated daily encrypted pg_dump exports to S3 buckets with lifecycle expiration rules.",
                "implementation": "Authored hardened Bash script with GPG encryption, sha256 checksum verification, and S3 multipart upload.",
                "results": "Achieved reliable automated backup snapshots across 4 dev environments."
            }
        ],
        "certifications": [
            "AWS Certified Solutions Architect – Associate"
        ]
    },
    {
        "id": "candidate08",
        "file_name": "candidate08_resume.pdf",
        "full_name": "Devon Brooks",
        "category": "Internship",
        "years_experience": 0.25,
        "quality": "Basic",
        "email": "devon.brooks.demo@talentlens.fictional",
        "phone": "+44-161-555-0108",
        "location": "Manchester, UK",
        "professional_summary": "Analytical graduate with a 3-month data analyst internship. Proficient in SQL querying, Python scripting, and data spreadsheet modeling.",
        "skills": ["SQL", "Python", "Pandas", "PostgreSQL", "Excel", "Git"],
        "education": [
            {
                "institution": "University of Manchester",
                "degree": "Bachelor of Science",
                "field_of_study": "Data Analytics",
                "start_date": "Sep 2020",
                "end_date": "Jun 2024",
                "details": "Upper Second Class Honours (2:1)"
            }
        ],
        "experience": [
            {
                "company": "RetailMetrics Ltd",
                "job_title": "Data Analyst Intern",
                "start_date": "Jun 2023",
                "end_date": "Aug 2023",
                "description": "Wrote SQL queries to extract sales transaction records from PostgreSQL databases. Built weekly reporting spreadsheets and cleaned customer survey datasets with Python and Pandas."
            }
        ],
        "projects": [
            {
                "name": "Customer Churn Analysis",
                "technologies": ["Python", "Pandas", "SQL"],
                "problem": "Business stakeholders lacked visibility into why subscription renewals were declining.",
                "contribution": "Cleaned and normalized 10,000 customer rows and computed churn rates segmented by subscription tenure.",
                "implementation": "Aggregated demographic and billing tables with SQL window functions and exported summary matrices via Pandas.",
                "results": "Identified a 22% drop-off rate after the initial 30-day trial period."
            },
            {
                "name": "E-Commerce Sales Summary",
                "technologies": ["SQL", "PostgreSQL", "Python"],
                "problem": "Department heads needed monthly visual summaries of category revenue.",
                "contribution": "Designed aggregated SQL views summarizing daily units sold and gross revenue.",
                "implementation": "Authored relational views utilizing GROUP BY, CASE WHEN expressions, and indexing on date columns.",
                "results": "Automated monthly reporting that previously took 4 hours of manual copy-pasting."
            }
        ],
        "certifications": [
            "Google Data Analytics Professional Certificate"
        ]
    },
    {
        "id": "candidate09",
        "file_name": "candidate09_resume.pdf",
        "full_name": "Vikram Malhotra",
        "category": "1-2 Years Experience",
        "years_experience": 1.5,
        "quality": "Strong",
        "email": "vikram.malhotra.demo@talentlens.fictional",
        "phone": "+91-98765-01009",
        "location": "Bengaluru, Karnataka, India",
        "professional_summary": "Results-driven Backend Engineer with 1.5 years of professional experience designing scalable RESTful microservices, asynchronous message architectures, and relational databases. Strong advocate of type safety, automated testing, and observable systems.",
        "skills": ["Python", "FastAPI", "PostgreSQL", "Docker", "AWS", "Git", "Redis", "REST APIs", "Linux", "CI/CD"],
        "education": [
            {
                "institution": "PES University",
                "degree": "Bachelor of Technology",
                "field_of_study": "Computer Science",
                "start_date": "Aug 2018",
                "end_date": "Jul 2022",
                "details": "CGPA: 8.9 / 10.0"
            }
        ],
        "experience": [
            {
                "company": "FinVerve Technologies",
                "job_title": "Associate Software Engineer (Backend)",
                "start_date": "Nov 2022",
                "end_date": "Apr 2024",
                "description": "Architected high-throughput REST APIs using FastAPI and asyncpg, handling 3.2M requests daily. Optimized PostgreSQL query execution plans, implemented B-tree and GIN indexes, and cut p99 database query latency from 180ms to 24ms. Built containerized deployment pipelines using Docker and AWS ECS with GitHub Actions."
            }
        ],
        "projects": [
            {
                "name": "Idempotent Payment Gateway Orchestrator",
                "technologies": ["Python", "FastAPI", "PostgreSQL", "Redis", "Docker"],
                "problem": "Double-charge incidents occurred during upstream network dropouts in transactional payment flows.",
                "contribution": "Implemented distributed idempotency key locking in Redis with atomic PostgreSQL transaction commits and database audit logging.",
                "implementation": "Engineered two-phase commit wrapper around payment webhooks with redis locks expiring after 120s.",
                "results": "Eliminated duplicate charges across 250,000 synthetic load-tested transactions."
            },
            {
                "name": "Asynchronous Notification Dispatcher",
                "technologies": ["Python", "Celery", "Redis", "AWS SES", "PostgreSQL"],
                "problem": "Synchronous email/SMS dispatches were blocking main user request threads.",
                "contribution": "Decoupled notification dispatch into async task workers with dynamic rate limiting and retry backoff.",
                "implementation": "Integrated Celery distributed task workers backed by Redis broker and PostgreSQL status tracking.",
                "results": "Decreased user-facing registration API response latency from 1.4s to 85ms."
            }
        ],
        "certifications": [
            "AWS Certified Developer – Associate",
            "Docker Certified Associate (DCA)"
        ]
    },
    {
        "id": "candidate10",
        "file_name": "candidate10_resume.pdf",
        "full_name": "Chloe Nguyen",
        "category": "1-2 Years Experience",
        "years_experience": 2.0,
        "quality": "Average",
        "email": "chloe.nguyen.demo@talentlens.fictional",
        "phone": "+65-6555-0110",
        "location": "Singapore",
        "professional_summary": "Frontend Developer with 2 years of professional experience building performant, responsive web applications in React and TypeScript. Dedicated to clean component design, cross-browser consistency, and engaging user experiences.",
        "skills": ["React", "TypeScript", "JavaScript", "HTML5", "CSS3", "Tailwind CSS", "Redux", "Next.js", "Jest", "Git", "REST APIs"],
        "education": [
            {
                "institution": "National University of Singapore (NUS)",
                "degree": "Bachelor of Science",
                "field_of_study": "Information Systems",
                "start_date": "Aug 2018",
                "end_date": "May 2022",
                "details": "GPA: 4.1 / 5.0"
            }
        ],
        "experience": [
            {
                "company": "OmniCommerce Pte Ltd",
                "job_title": "Frontend Developer",
                "start_date": "May 2022",
                "end_date": "May 2024",
                "description": "Developed user-facing e-commerce storefronts using React, TypeScript, and Tailwind CSS. Implemented modular shopping cart state management with Redux Toolkit and integrated Stripe checkout flows. Optimized image loading and code-splitting, improving Google Lighthouse performance score from 68 to 94."
            }
        ],
        "projects": [
            {
                "name": "Real-time Order Tracking Interface",
                "technologies": ["React", "TypeScript", "Tailwind CSS", "WebSocket", "Jest"],
                "problem": "Delivery riders and customers experienced desynchronized delivery statuses.",
                "contribution": "Engineered real-time order status banner with live WebSocket event listeners and fallback polling.",
                "implementation": "Built custom React hook managing WebSocket reconnect lifecycles and caching status states in Redux.",
                "results": "Reduced customer support ticket inquiries regarding status updates by 28%."
            },
            {
                "name": "Vendor Analytics Portal",
                "technologies": ["Next.js", "TypeScript", "Tailwind CSS", "Chart.js"],
                "problem": "Merchant partners lacked intuitive mobile interfaces to review weekly product sales.",
                "contribution": "Built server-rendered dashboard with responsive data tables, filtering controls, and CSV export.",
                "implementation": "Leveraged Next.js Server Components and dynamic client-side filtering for fast page responses.",
                "results": "Handled daily dashboard usage across 150+ merchant partner accounts with zero reported layout regressions."
            }
        ],
        "certifications": [
            "Meta Front-End Developer Professional Certificate"
        ]
    },
    {
        "id": "candidate11",
        "file_name": "candidate11_resume.pdf",
        "full_name": "Kavita Desai",
        "category": "1-2 Years Experience",
        "years_experience": 1.75,
        "quality": "Challenging",
        "email": "kavita.desai.demo@talentlens.fictional",
        "phone": "+91-98765-01011",
        "location": "Hyderabad, Telangana, India",
        "professional_summary": "Cloud Operations Specialist & Infrastructure Engineer with 1.8 years hands-on production background managing containerized Linux clusters, AWS cloud primitives, and automated continuous delivery. Specialized in Docker, Kubernetes, Linux, AWS, CI/CD, Terraform, Bash, and Python scripting.",
        "skills": ["Docker", "Kubernetes", "AWS", "Linux", "CI/CD", "Terraform", "Bash", "Python", "Git"],
        "education": [
            {
                "institution": "JNTU Hyderabad",
                "degree": "B.Tech",
                "field_of_study": "Computer Science & Engineering",
                "start_date": "Jun 2018",
                "end_date": "May 2022",
                "details": "First Class with Distinction"
            }
        ],
        "experience": [
            {
                "company": "CyberSphere Solutions",
                "job_title": "Cloud Infrastructure & Systems Support Associate",
                "start_date": "Aug 2022",
                "end_date": "Apr 2024",
                "description": "Responsible for managing production Dockerized workloads across AWS EC2 and EKS clusters. Configured automated GitHub Actions and GitLab CI/CD pipelines for zero-downtime rolling deployments. Authored Terraform scripts to provision VPC subnets, security groups, and IAM roles. Maintained Linux system stability and automated disk cleanups via cron-triggered Bash scripts."
            }
        ],
        "projects": [
            {
                "name": "Cluster Observability & Metrics Stack",
                "technologies": ["Kubernetes", "Prometheus", "Grafana", "Docker", "AWS"],
                "problem": "Operational teams suffered blind spots during sudden traffic surges on microservices.",
                "contribution": "Deployed Prometheus operator and custom Grafana visualization boards tracking CPU and memory saturation.",
                "implementation": "Configured Prometheus scraping rules on Kubernetes pod annotations with Grafana dashboard alerts routed to PagerDuty.",
                "results": "Reduced Mean Time to Resolution (MTTR) for service outages from 45 minutes to 12 minutes."
            },
            {
                "name": "Automated Environment Provisioner",
                "technologies": ["Terraform", "AWS", "Docker", "Bash"],
                "problem": "Developers waited days for staging environment provisioning before feature testing.",
                "contribution": "Created modular Terraform templates enabling one-command provisioning of isolated staging VPCs.",
                "implementation": "Packaged parameterized Terraform HCL modules with automated S3 state-locking via DynamoDB.",
                "results": "Cut environment turn-around time from 3 business days to under 25 minutes."
            }
        ],
        "certifications": [
            "AWS Certified Solutions Architect – Associate",
            "Certified Kubernetes Administrator (CKA)"
        ]
    },
    {
        "id": "candidate12",
        "file_name": "candidate12_resume.pdf",
        "full_name": "David Miller",
        "category": "3 Years Experience",
        "years_experience": 3.17,
        "quality": "Basic",
        "email": "david.miller.demo@talentlens.fictional",
        "phone": "+1-312-555-0112",
        "location": "Chicago, Illinois, USA",
        "professional_summary": "Full Stack Software Developer with over 3 years of hands-on experience building web applications and backend APIs using React, Node.js, TypeScript, and PostgreSQL. Experienced in the complete development lifecycle from initial requirements through deployment.",
        "skills": ["React", "Node.js", "TypeScript", "PostgreSQL", "REST APIs", "Docker", "AWS", "Express", "Git"],
        "education": [
            {
                "institution": "University of Illinois Chicago",
                "degree": "Bachelor of Science",
                "field_of_study": "Computer Science",
                "start_date": "Aug 2017",
                "end_date": "May 2021",
                "details": "Major in Software Engineering"
            }
        ],
        "experience": [
            {
                "company": "Apex Digital Solutions",
                "job_title": "Full Stack Developer",
                "start_date": "Feb 2021",
                "end_date": "Apr 2024",
                "description": "Developed and maintained customer-facing web applications using React, Node.js, and TypeScript. Designed RESTful API endpoints using Express and implemented database operations with PostgreSQL. Collaborated with QA team to fix bugs and write integration tests. Deployed containerized applications onto AWS EC2 instances using Docker."
            }
        ],
        "projects": [
            {
                "name": "Client Billing Portal",
                "technologies": ["React", "Node.js", "Express", "PostgreSQL", "TypeScript"],
                "problem": "Clients required a direct self-service portal to view invoice history and make recurring payments.",
                "contribution": "Implemented React billing views, backend invoice generation endpoints, and PostgreSQL transaction queries.",
                "implementation": "Built Express routes with JWT authentication and PostgreSQL parameterized queries, paired with React tables.",
                "results": "Successfully handled over 15,000 monthly invoice queries with reliable data consistency."
            },
            {
                "name": "Team Collaboration Task Tracker",
                "technologies": ["React", "TypeScript", "Node.js", "PostgreSQL", "Docker"],
                "problem": "Internal remote consulting teams lacked a unified tool to track project milestone deliverables.",
                "contribution": "Built kanban task boards with draggable UI components and REST APIs for project task status updates.",
                "implementation": "Implemented drag-and-drop React interface synchronizing state with Node/Express REST backend.",
                "results": "Replaced third-party tool, saving approximately $12,000 in annual licensing costs."
            }
        ],
        "certifications": [
            "MongoDB Certified Developer",
            "AWS Certified Cloud Practitioner"
        ]
    }
]


def render_strong_resume(candidate: Dict[str, Any], output_path: Path):
    """Render a strong, highly structured, beautifully spaced ATS-friendly resume."""
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36,
    )
    story = []
    styles = getSampleStyleSheet()

    PRIMARY_COLOR = colors.HexColor("#0F2942")  # Deep Navy
    SECONDARY_COLOR = colors.HexColor("#2563EB")  # Modern Royal Blue
    TEXT_COLOR = colors.HexColor("#1E293B")  # Slate 800
    MUTED_COLOR = colors.HexColor("#64748B")  # Slate 500

    name_style = ParagraphStyle(
        "StrongName",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        textColor=PRIMARY_COLOR,
        alignment=TA_LEFT,
        spaceAfter=2,
    )
    contact_style = ParagraphStyle(
        "StrongContact",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        textColor=MUTED_COLOR,
        alignment=TA_LEFT,
        spaceAfter=10,
    )
    sec_style = ParagraphStyle(
        "StrongSection",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=15,
        textColor=PRIMARY_COLOR,
        spaceBefore=8,
        spaceAfter=3,
        keepWithNext=True,
    )
    body_style = ParagraphStyle(
        "StrongBody",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        textColor=TEXT_COLOR,
        spaceAfter=4,
    )
    subhead_style = ParagraphStyle(
        "StrongSubhead",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9.5,
        leading=13,
        textColor=PRIMARY_COLOR,
        spaceBefore=4,
        spaceAfter=2,
        keepWithNext=True,
    )
    meta_style = ParagraphStyle(
        "StrongMeta",
        parent=styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=8.5,
        leading=12,
        textColor=MUTED_COLOR,
        spaceAfter=3,
    )
    bullet_style = ParagraphStyle(
        "StrongBullet",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=12,
        textColor=TEXT_COLOR,
        leftIndent=12,
        spaceAfter=2,
    )

    # Header
    story.append(Paragraph(candidate["full_name"], name_style))
    contact_line = f"{candidate['email']} &nbsp;|&nbsp; {candidate['phone']} &nbsp;|&nbsp; {candidate['location']}"
    story.append(Paragraph(contact_line, contact_style))
    story.append(HRFlowable(width="100%", thickness=1, color=SECONDARY_COLOR, spaceAfter=6))

    # Professional Summary
    story.append(Paragraph("PROFESSIONAL SUMMARY", sec_style))
    story.append(Paragraph(candidate["professional_summary"], body_style))
    story.append(Spacer(1, 4))

    # Technical Skills
    story.append(Paragraph("TECHNICAL EXPERTISE", sec_style))
    skills_text = f"<b>Core Competencies:</b> {', '.join(candidate['skills'])}"
    story.append(Paragraph(skills_text, body_style))
    story.append(Spacer(1, 4))

    # Work Experience / Internships (if any)
    if candidate.get("experience"):
        story.append(Paragraph("PROFESSIONAL EXPERIENCE", sec_style))
        for exp in candidate["experience"]:
            title_line = f"<b>{exp['job_title']}</b> &mdash; {exp['company']}"
            date_line = f"{exp['start_date']} &ndash; {exp['end_date']}"
            story.append(Paragraph(title_line, subhead_style))
            story.append(Paragraph(date_line, meta_style))
            story.append(Paragraph(f"• {exp['description']}", bullet_style))
            story.append(Spacer(1, 3))
        story.append(Spacer(1, 4))

    # Technical Projects
    if candidate.get("projects"):
        story.append(Paragraph("KEY PROJECTS", sec_style))
        for proj in candidate["projects"]:
            p_head = f"<b>{proj['name']}</b> | <i>{', '.join(proj['technologies'])}</i>"
            story.append(Paragraph(p_head, subhead_style))
            story.append(Paragraph(f"• <b>Problem Solved:</b> {proj['problem']}", bullet_style))
            story.append(Paragraph(f"• <b>Implementation:</b> {proj['implementation']}", bullet_style))
            story.append(Paragraph(f"• <b>Results & Impact:</b> {proj['results']}", bullet_style))
            story.append(Spacer(1, 3))
        story.append(Spacer(1, 4))

    # Education
    story.append(Paragraph("EDUCATION", sec_style))
    for edu in candidate["education"]:
        edu_title = f"<b>{edu['degree']} in {edu['field_of_study']}</b>"
        edu_meta = f"{edu['institution']} | {edu['start_date']} &ndash; {edu['end_date']}"
        story.append(Paragraph(edu_title, subhead_style))
        story.append(Paragraph(edu_meta, meta_style))
        if edu.get("details"):
            story.append(Paragraph(f"• {edu['details']}", bullet_style))
        story.append(Spacer(1, 3))

    # Certifications
    if candidate.get("certifications"):
        story.append(Paragraph("CERTIFICATIONS", sec_style))
        for cert in candidate["certifications"]:
            story.append(Paragraph(f"• {cert}", bullet_style))

    doc.build(story)


def render_average_resume(candidate: Dict[str, Any], output_path: Path):
    """Render a standard average single-column resume with clean conventional typography."""
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=letter,
        leftMargin=40,
        rightMargin=40,
        topMargin=40,
        bottomMargin=40,
    )
    story = []
    styles = getSampleStyleSheet()

    PRIMARY_COLOR = colors.HexColor("#1F2937")  # Gray 800
    TEXT_COLOR = colors.HexColor("#374151")  # Gray 700

    name_style = ParagraphStyle(
        "AvgName",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=22,
        textColor=PRIMARY_COLOR,
        alignment=TA_CENTER,
        spaceAfter=4,
    )
    contact_style = ParagraphStyle(
        "AvgContact",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        textColor=TEXT_COLOR,
        alignment=TA_CENTER,
        spaceAfter=12,
    )
    sec_style = ParagraphStyle(
        "AvgSection",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=15,
        textColor=PRIMARY_COLOR,
        spaceBefore=8,
        spaceAfter=4,
        keepWithNext=True,
    )
    body_style = ParagraphStyle(
        "AvgBody",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        textColor=TEXT_COLOR,
        spaceAfter=4,
    )
    item_head = ParagraphStyle(
        "AvgItemHead",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9.5,
        leading=13,
        textColor=PRIMARY_COLOR,
        spaceBefore=3,
        spaceAfter=2,
        keepWithNext=True,
    )
    bullet_style = ParagraphStyle(
        "AvgBullet",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        textColor=TEXT_COLOR,
        leftIndent=12,
        spaceAfter=2,
    )

    story.append(Paragraph(candidate["full_name"], name_style))
    contact_line = f"{candidate['email']} • {candidate['phone']} • {candidate['location']}"
    story.append(Paragraph(contact_line, contact_style))
    story.append(HRFlowable(width="100%", thickness=0.8, color=colors.gray, spaceAfter=8))

    story.append(Paragraph("Professional Summary", sec_style))
    story.append(Paragraph(candidate["professional_summary"], body_style))
    story.append(Spacer(1, 4))

    story.append(Paragraph("Technical Skills", sec_style))
    story.append(Paragraph(", ".join(candidate["skills"]), body_style))
    story.append(Spacer(1, 4))

    if candidate.get("experience"):
        story.append(Paragraph("Work Experience", sec_style))
        for exp in candidate["experience"]:
            h = f"<b>{exp['job_title']}</b> - {exp['company']} ({exp['start_date']} - {exp['end_date']})"
            story.append(Paragraph(h, item_head))
            story.append(Paragraph(f"• {exp['description']}", bullet_style))
            story.append(Spacer(1, 3))
        story.append(Spacer(1, 4))

    if candidate.get("projects"):
        story.append(Paragraph("Projects", sec_style))
        for proj in candidate["projects"]:
            p_head = f"<b>{proj['name']}</b> ({', '.join(proj['technologies'])})"
            story.append(Paragraph(p_head, item_head))
            story.append(Paragraph(f"• Problem: {proj['problem']}", bullet_style))
            story.append(Paragraph(f"• Implementation: {proj['implementation']}", bullet_style))
            story.append(Paragraph(f"• Result: {proj['results']}", bullet_style))
            story.append(Spacer(1, 3))
        story.append(Spacer(1, 4))

    story.append(Paragraph("Education", sec_style))
    for edu in candidate["education"]:
        e_head = f"<b>{edu['degree']} in {edu['field_of_study']}</b>"
        e_sub = f"{edu['institution']}, {edu['start_date']} - {edu['end_date']}"
        story.append(Paragraph(e_head, item_head))
        story.append(Paragraph(e_sub, body_style))
        if edu.get("details"):
            story.append(Paragraph(f"• {edu['details']}", bullet_style))
        story.append(Spacer(1, 3))

    if candidate.get("certifications"):
        story.append(Paragraph("Certifications", sec_style))
        for cert in candidate["certifications"]:
            story.append(Paragraph(f"• {cert}", bullet_style))

    doc.build(story)


def render_basic_resume(candidate: Dict[str, Any], output_path: Path):
    """Render a basic minimalist resume with simple monochrome styling."""
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=letter,
        leftMargin=44,
        rightMargin=44,
        topMargin=44,
        bottomMargin=44,
    )
    story = []
    styles = getSampleStyleSheet()

    name_style = ParagraphStyle(
        "BasicName",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=16,
        leading=20,
        alignment=TA_LEFT,
        spaceAfter=2,
    )
    contact_style = ParagraphStyle(
        "BasicContact",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=12,
        spaceAfter=10,
    )
    sec_style = ParagraphStyle(
        "BasicSec",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=10.5,
        leading=14,
        spaceBefore=6,
        spaceAfter=2,
        keepWithNext=True,
    )
    body_style = ParagraphStyle(
        "BasicBody",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=12,
        spaceAfter=3,
    )
    bullet_style = ParagraphStyle(
        "BasicBullet",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=12,
        leftIndent=10,
        spaceAfter=2,
    )

    story.append(Paragraph(candidate["full_name"], name_style))
    story.append(Paragraph(f"Email: {candidate['email']} | Phone: {candidate['phone']} | Location: {candidate['location']}", contact_style))

    story.append(Paragraph("SUMMARY", sec_style))
    story.append(Paragraph(candidate["professional_summary"], body_style))

    story.append(Paragraph("SKILLS", sec_style))
    story.append(Paragraph(", ".join(candidate["skills"]), body_style))

    if candidate.get("experience"):
        story.append(Paragraph("WORK HISTORY", sec_style))
        for exp in candidate["experience"]:
            story.append(Paragraph(f"<b>{exp['job_title']}</b> - {exp['company']} ({exp['start_date']} to {exp['end_date']})", body_style))
            story.append(Paragraph(f"- {exp['description']}", bullet_style))

    if candidate.get("projects"):
        story.append(Paragraph("PROJECTS", sec_style))
        for proj in candidate["projects"]:
            story.append(Paragraph(f"<b>{proj['name']}</b> ({', '.join(proj['technologies'])})", body_style))
            story.append(Paragraph(f"- Objective: {proj['problem']}", bullet_style))
            story.append(Paragraph(f"- Method: {proj['implementation']}", bullet_style))
            story.append(Paragraph(f"- Outcome: {proj['results']}", bullet_style))

    story.append(Paragraph("EDUCATION", sec_style))
    for edu in candidate["education"]:
        story.append(Paragraph(f"<b>{edu['degree']} - {edu['field_of_study']}</b>, {edu['institution']} ({edu['start_date']} - {edu['end_date']})", body_style))
        if edu.get("details"):
            story.append(Paragraph(f"- {edu['details']}", bullet_style))

    if candidate.get("certifications"):
        story.append(Paragraph("CERTIFICATIONS", sec_style))
        for c in candidate["certifications"]:
            story.append(Paragraph(f"- {c}", bullet_style))

    doc.build(story)


def render_challenging_resume(candidate: Dict[str, Any], output_path: Path):
    """
    Render intentionally challenging resumes for extraction testing:
    - candidate04: Non-standard section order (Summary -> 'What I Built' -> 'Practical Engagements' -> 'Academic Background' -> 'Tooling & Stacks' at bottom)
    - candidate11: Dense compact formatting, mixed inline technical summary, bracket dates [MM.YYYY-MM.YYYY]
    """
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=letter,
        leftMargin=30,
        rightMargin=30,
        topMargin=30,
        bottomMargin=30,
    )
    story = []
    styles = getSampleStyleSheet()

    if candidate["id"] == "candidate04":
        # Non-standard section ordering and informal headings
        name_style = ParagraphStyle(
            "Chall4Name",
            parent=styles["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=17,
            leading=21,
            spaceAfter=2,
        )
        contact_style = ParagraphStyle(
            "Chall4Contact",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=12,
            spaceAfter=6,
        )
        head_style = ParagraphStyle(
            "Chall4Head",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=10.5,
            leading=14,
            spaceBefore=6,
            spaceAfter=3,
            keepWithNext=True,
        )
        body_style = ParagraphStyle(
            "Chall4Body",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=12,
            spaceAfter=3,
        )

        story.append(Paragraph(candidate["full_name"], name_style))
        story.append(Paragraph(f"Contact: {candidate['email']} / {candidate['phone']} / Located in {candidate['location']}", contact_style))

        # 1. Summary
        story.append(Paragraph("Candidate Profile", head_style))
        story.append(Paragraph(candidate["professional_summary"], body_style))

        # 2. Projects first under informal heading "What I Built"
        story.append(Paragraph("What I Built (Key Projects)", head_style))
        for proj in candidate["projects"]:
            p_text = (
                f"<b>{proj['name']}</b> using {', '.join(proj['technologies'])}. "
                f"Context: {proj['problem']} I personally handled the following: {proj['contribution']} "
                f"Specifically, {proj['implementation']} Which resulted in: {proj['results']}"
            )
            story.append(Paragraph(p_text, body_style))
            story.append(Spacer(1, 2))

        # 3. Practical Engagements
        if candidate.get("experience"):
            story.append(Paragraph("Hands-on Engagements & Activities", head_style))
            for exp in candidate["experience"]:
                e_text = f"<b>{exp['job_title']}</b> at {exp['company']} ({exp['start_date']} - {exp['end_date']}). {exp['description']}"
                story.append(Paragraph(e_text, body_style))

        # 4. Education under "Academic Background"
        story.append(Paragraph("Academic Background", head_style))
        for edu in candidate["education"]:
            story.append(Paragraph(f"{edu['degree']} in {edu['field_of_study']} from {edu['institution']} ({edu['start_date']} to {edu['end_date']}) - {edu.get('details', '')}", body_style))

        # 5. Skills placed strictly at the bottom under non-standard label
        story.append(Paragraph("Tooling & Stacks", head_style))
        story.append(Paragraph(", ".join(candidate["skills"]), body_style))

        if candidate.get("certifications"):
            story.append(Paragraph("Completed Credentials", head_style))
            for c in candidate["certifications"]:
                story.append(Paragraph(f"- {c}", body_style))

    else:
        # candidate11: Dense compact layout with bracket dates and inline embedded tech summary
        title_style = ParagraphStyle(
            "Chall11Title",
            parent=styles["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=15,
            leading=18,
            spaceAfter=1,
        )
        meta_style = ParagraphStyle(
            "Chall11Meta",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=8,
            leading=11,
            spaceAfter=4,
        )
        section_style = ParagraphStyle(
            "Chall11Sec",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=9.5,
            leading=12,
            spaceBefore=4,
            spaceAfter=2,
            keepWithNext=True,
        )
        body_style = ParagraphStyle(
            "Chall11Body",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=8,
            leading=11,
            spaceAfter=2,
        )

        story.append(Paragraph(f"<b>{candidate['full_name']}</b> &bull; Systems & Cloud Operations", title_style))
        story.append(Paragraph(f"Email: {candidate['email']} | Tel: {candidate['phone']} | City: {candidate['location']}", meta_style))

        story.append(Paragraph("Overview & Technical Profile", section_style))
        story.append(Paragraph(candidate["professional_summary"], body_style))

        story.append(Paragraph("Technical Skills Inventory", section_style))
        story.append(Paragraph("Stack: " + " / ".join(candidate["skills"]), body_style))

        story.append(Paragraph("Work Experience History", section_style))
        for exp in candidate["experience"]:
            line1 = f"<b>{exp['job_title']}</b> &mdash; <i>{exp['company']}</i> [{exp['start_date']} - {exp['end_date']}]"
            story.append(Paragraph(line1, body_style))
            story.append(Paragraph(f"&gt; {exp['description']}", body_style))

        story.append(Paragraph("Engineering Projects", section_style))
        for proj in candidate["projects"]:
            pline = f"<b>{proj['name']}</b> [{', '.join(proj['technologies'])}]: {proj['problem']} Contribution: {proj['contribution']} Result: {proj['results']}"
            story.append(Paragraph(pline, body_style))

        story.append(Paragraph("Education Credentials", section_style))
        for edu in candidate["education"]:
            story.append(Paragraph(f"<b>{edu['degree']}</b> in {edu['field_of_study']} &mdash; {edu['institution']} [{edu['start_date']} - {edu['end_date']}]", body_style))

        if candidate.get("certifications"):
            story.append(Paragraph("Certifications & Badges", section_style))
            story.append(Paragraph(" | ".join(candidate["certifications"]), body_style))

    doc.build(story)


def generate_all_resumes(
    output_dir: str = "backend/demo_fixtures/resumes",
    profiles_dir: str = "backend/demo_fixtures/profiles"
) -> List[Dict[str, Any]]:
    """Generate all 12 PDF resumes and persist structured profile JSONs."""
    out_path = Path(output_dir).resolve()
    prof_path = Path(profiles_dir).resolve()
    out_path.mkdir(parents=True, exist_ok=True)
    prof_path.mkdir(parents=True, exist_ok=True)

    generated = []

    print(f"=== Generating {len(CANDIDATES_DATA)} Synthetic Resumes ===")
    for cand in CANDIDATES_DATA:
        cid = cand["id"]
        fname = cand["file_name"]
        pdf_file = out_path / fname
        json_file = prof_path / f"{cid}.json"

        # 1. Save profile JSON
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(cand, f, indent=2)

        # 2. Render PDF using appropriate quality renderer
        quality = cand["quality"]
        if quality == "Strong":
            render_strong_resume(cand, pdf_file)
        elif quality == "Average":
            render_average_resume(cand, pdf_file)
        elif quality == "Basic":
            render_basic_resume(cand, pdf_file)
        elif quality == "Challenging":
            render_challenging_resume(cand, pdf_file)
        else:
            render_average_resume(cand, pdf_file)

        size_kb = pdf_file.stat().st_size / 1024
        print(f"  [OK] {fname} ({cand['full_name']}) - {quality} ({cand['category']}) - {size_kb:.1f} KB")

        generated.append({
            "candidate_id": cid,
            "filename": fname,
            "full_name": cand["full_name"],
            "category": cand["category"],
            "years_experience": cand["years_experience"],
            "quality": quality,
            "pdf_path": str(pdf_file),
            "json_path": str(json_file),
            "size_bytes": pdf_file.stat().st_size,
        })

    return generated


if __name__ == "__main__":
    generate_all_resumes()
