import re
from typing import Dict, List, Optional, Set, Tuple

NORMALIZATION_VERSION = "v1.0.0"

# Canonical mappings: key is lower-case normalized form, value is display canonical name
CANONICAL_SKILL_MAP: Dict[str, str] = {
    # Languages
    "python": "Python",
    "py": "Python",
    "python3": "Python",
    "javascript": "JavaScript",
    "js": "JavaScript",
    "typescript": "TypeScript",
    "ts": "TypeScript",
    "java": "Java",
    "c++": "C++",
    "cpp": "C++",
    "c#": "C#",
    "csharp": "C#",
    "golang": "Go",
    "go": "Go",
    "ruby": "Ruby",
    "rust": "Rust",
    "php": "PHP",
    "swift": "Swift",
    "kotlin": "Kotlin",
    "scala": "Scala",
    "r": "R",
    # Frameworks / Libraries
    "react": "React",
    "reactjs": "React",
    "react.js": "React",
    "react native": "React Native",
    "react-native": "React Native",
    "vue": "Vue.js",
    "vuejs": "Vue.js",
    "vue.js": "Vue.js",
    "angular": "Angular",
    "angularjs": "Angular",
    "nextjs": "Next.js",
    "next.js": "Next.js",
    "nodejs": "Node.js",
    "node.js": "Node.js",
    "node": "Node.js",
    "express": "Express.js",
    "expressjs": "Express.js",
    "express.js": "Express.js",
    "fastapi": "FastAPI",
    "flask": "Flask",
    "django": "Django",
    "spring": "Spring",
    "spring boot": "Spring Boot",
    "springboot": "Spring Boot",
    "asp.net": "ASP.NET",
    "dotnet": ".NET",
    ".net": ".NET",
    # Databases
    "sql": "SQL",
    "postgresql": "PostgreSQL",
    "postgres": "PostgreSQL",
    "psql": "PostgreSQL",
    "mysql": "MySQL",
    "mongodb": "MongoDB",
    "mongo": "MongoDB",
    "redis": "Redis",
    "sqlite": "SQLite",
    "oracle": "Oracle DB",
    "cassandra": "Cassandra",
    "dynamodb": "DynamoDB",
    # Cloud / DevOps / Infrastructure
    "docker": "Docker",
    "kubernetes": "Kubernetes",
    "k8s": "Kubernetes",
    "aws": "AWS",
    "amazon web services": "AWS",
    "gcp": "GCP",
    "google cloud": "GCP",
    "google cloud platform": "GCP",
    "azure": "Azure",
    "microsoft azure": "Azure",
    "terraform": "Terraform",
    "ansible": "Ansible",
    "git": "Git",
    "github": "GitHub",
    "gitlab": "GitLab",
    "ci/cd": "CI/CD",
    "cicd": "CI/CD",
    "jenkins": "Jenkins",
    "linux": "Linux",
    "rest": "REST API",
    "rest api": "REST API",
    "restful": "REST API",
    "graphql": "GraphQL",
    "grpc": "gRPC",
}

# Strict negative discrimination: do not allow false matches across these distinct technologies
STRICT_DISTINCT_PAIRS: Set[Tuple[str, str]] = {
    ("java", "javascript"),
    ("javascript", "java"),
    ("react", "react native"),
    ("react native", "react"),
    ("c", "c++"),
    ("c++", "c"),
    ("c", "c#"),
    ("c#", "c"),
    ("c++", "c#"),
    ("c#", "c++"),
}


class SkillNormalizer:
    """Deterministic, rule-based skill normalization."""

    @staticmethod
    def clean_text(text: str) -> str:
        """Strip punctuation and extraneous whitespace while preserving symbols like +, #, . in tech names."""
        if not text:
            return ""
        cleaned = re.sub(r"[\t\r\n]+", " ", text)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        return cleaned

    @classmethod
    def normalize_skill(cls, raw_skill: str) -> Tuple[str, str]:
        """
        Normalize a raw skill string.
        Returns tuple of (canonical_name, original_cleaned).
        """
        original = cls.clean_text(raw_skill)
        if not original:
            return "", ""

        lookup_key = original.lower()
        # Direct lookup
        if lookup_key in CANONICAL_SKILL_MAP:
            return CANONICAL_SKILL_MAP[lookup_key], original

        # Strip surrounding non-alphanumeric except common tech symbols (+, #, .)
        stripped = re.sub(r"^[^\w+#.]+|[^\w+#.]+$", "", lookup_key)
        if stripped in CANONICAL_SKILL_MAP:
            return CANONICAL_SKILL_MAP[stripped], original

        # Title case standard fallback if no alias rule exists
        canonical = original.strip().title()
        return canonical, original

    @classmethod
    def are_skills_matching(cls, skill_a: str, skill_b: str) -> bool:
        """
        Check if two skills match canonically without false positive collisions.
        """
        canon_a, _ = cls.normalize_skill(skill_a)
        canon_b, _ = cls.normalize_skill(skill_b)

        if not canon_a or not canon_b:
            return False

        lower_a = canon_a.lower()
        lower_b = canon_b.lower()

        # Check negative distinct pairs
        if (lower_a, lower_b) in STRICT_DISTINCT_PAIRS:
            return False

        return lower_a == lower_b


skill_normalizer = SkillNormalizer()
