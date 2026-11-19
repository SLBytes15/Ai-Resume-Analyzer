import os 
import json
import re
from pathlib import Path
from typing import Any

try:
    import chromadb  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    chromadb = None

try:
    import ollama  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    ollama = None

try:
    from llama_index.core import VectorStoreIndex, Settings  # type: ignore
    from llama_index.embeddings.huggingface import HuggingFaceEmbedding  # type: ignore
    from llama_index.vector_stores.chroma import ChromaVectorStore  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    VectorStoreIndex = None
    Settings = None
    HuggingFaceEmbedding = None
    ChromaVectorStore = None

if Settings is not None and HuggingFaceEmbedding is not None:
    try:
        Settings.embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")
    except Exception:  # pragma: no cover - model download may fail
        pass


def load_json_file(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def _normalize(text: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(text).lower())

def extract_skills_from_raw_jd(raw_text, model_name="nemotron-3-super:cloud"):
    prompt = f"""
Analyze this unstructured Job Description text and extract the target parameters.
Identify the core technical stack requirements and calculate the baseline minimum years of experience requested.

Raw Job Description Text:
{raw_text}

Return a strict JSON object with exactly these keys:
{{
  "role": "Estimated job title or profile classification",
  "skills": ["List", "of", "exact", "technical", "framework", "keywords"],
  "minimum_years": 0
}}
"""
    try:
        response = ollama(
            model_name=model_name,
            prompt=prompt,
            formal='json',
            options={'temperature': 0.0}
        )
        return json.loads(response['response'].strip())
    except Exception:
        return {
            "role": "Software Engineer",
            "skills": [s.strip() for s in raw_text.split(",") if len(s.strip()) > 0],
            "minimum_years": 0
        }



def _skill_matches(candidate_skills: list[str], required_skills: list[str]) -> tuple[list[str], list[str]]:
    matched: list[str] = []
    missing: list[str] = []

    for skill in required_skills:
        skill_norm = _normalize(skill)
        if any(
            skill_norm == _normalize(candidate_skill)
            or skill_norm in _normalize(candidate_skill)
            or _normalize(candidate_skill) in skill_norm
            for candidate_skill in candidate_skills
        ):
            matched.append(skill)
        else:
            missing.append(skill)

    return matched, missing


def run_explanation_engine(jd_skills, candidate_skills, model_name="nemotron-3-super:cloud"):
    """Generate a lightweight explanation for the candidate match."""
    matched, missing = _skill_matches(candidate_skills, jd_skills)
    reason = (
        f"The profile covers {len(matched)} of the requested skills and fits the target stack closely."
        if matched
        else "The profile does not clearly overlap with the requested skill set."
    )

    if ollama is None:
        return {"matched": matched, "missing": missing, "reason": reason}

    prompt = f"""
    Compare the Required Job Description Skills against the Candidate's Actual Skills.
    Required Skills: {json.dumps(jd_skills)}
    Candidate Skills: {json.dumps(candidate_skills)}

    Return a strict JSON object with exactly these keys:
    {{
    "matched": ["List of requirements fulfilled by the candidate"],
    "missing": ["List of requirements unfulfilled"],
    "reason": "A 1-sentence analytical synthesis"
    }}
    """
    try:
            response = ollama.generate(model=model_name, prompt=prompt, format='json', options={'temperature': 0.0})
            return json.loads(response['response'].strip())
    except Exception:
            matched = [s for s in jd_skills if s.lower() in [cs.lower() for cs in candidate_skills]]
            missing = [s for s in jd_skills if s not in matched]
            return {"matched": matched, "missing": missing, "reason": "Fallback engine analysis executed."}

def _heuristic_rank_candidates(jd_data: dict, profiles_dir: str, min_years: int) -> list[dict[str, Any]]:
    required_skills = jd_data.get("skills", [])
    profiles_path = Path(profiles_dir)
    ranked_matches: list[dict[str, Any]] = []

    for profile_file in sorted(profiles_path.glob("*.json")):
        candidate_profile = load_json_file(profile_file)
        cand_name = candidate_profile.get("candidate_name", profile_file.stem)
        cand_skills = candidate_profile.get("top_skills", candidate_profile.get("skills", []))
        yoe_str = str(candidate_profile.get("years_of_experience", "0"))
        cand_yoe = int("".join(filter(str.isdigit, yoe_str)) or 0)
        yoe_check = "✓ Pass" if cand_yoe >= min_years else f"Gap ({cand_yoe}/{min_years} Years)"

        matched_skills, missing_skills = _skill_matches(cand_skills, required_skills)
        skill_score = len(matched_skills) * 20
        score = min(99, skill_score)
        if not matched_skills:
            score = 0

        analysis_report = run_explanation_engine(required_skills, cand_skills)
        ranked_matches.append(
            {
                "id": candidate_profile.get("resume_id", profile_file.stem),
                "name": cand_name,
                "score": score,
                "yoe_status": yoe_check,
                "matched_skills": analysis_report.get("matched", matched_skills),
                "missing_skills": analysis_report.get("missing", missing_skills),
                "reasoning": analysis_report.get("reason", ""),
            }
        )

    return sorted(ranked_matches, key=lambda item: item["score"], reverse=True)


def run_candidate_matcher(raw_text: str, profiles_dir: str = "../candidate_profiles", chroma_db_path: str = "../chroma_db"):
    """Return ranked candidates using a local heuristic fallback when vector search dependencies are unavailable."""

    jd_data = extract_skills_from_raw_jd(raw_text)
    target_role = jd_data.get("role", "Unknown Role")
    required_skills = jd_data.get("skills", [])
    min_years = int(jd_data.get("minimum_years", 0))

    if chromadb is None or VectorStoreIndex is None or ChromaVectorStore is None:
        return _heuristic_rank_candidates(jd_data, profiles_dir, min_years)

    try:
        client = chromadb.PersistentClient(path=chroma_db_path)
        collection = client.get_collection(name="resume_collection")
    except Exception:
        return _heuristic_rank_candidates(jd_data, profiles_dir, min_years)

    vector_store = ChromaVectorStore(chroma_collection=collection)
    index = VectorStoreIndex.from_vector_store(vector_store=vector_store)
    retriever = index.as_retriever(similarity_top_k=10)

    query_text = f"Specializes in {', '.join(required_skills)}. Targeted operational profile: {target_role}"
    nodes = retriever.retrieve(query_text)

    results = collection.query(
        query_embeddings = [temporary_query_embedding],
        n_results = 10,
        include=["metadatas","distances"]
    )

    if not nodes:
        return _heuristic_rank_candidates(jd_data, profiles_dir, min_years)

    ranked_matches = []
    profiles_path = Path(profiles_dir)

    for idx, cand_id in enumerate(results["ids"][0]):
        distance = results["distances"][0][idx]
        metadata = results["metadatas"][0][idx] if results["metadatas"] else {}
        
        # Recruiter calibrated bounding scale: Convert distance to intuitive scores
        # Cosine distance boundaries: 0.40 (perfect) to 1.0 (noise)
        MIN_BOUND = 0.50
        MAX_BOUND = 0.85
        
        if distance <= MIN_BOUND:
            semantic_score = 100
        elif distance >= MAX_BOUND:
            semantic_score = 0
        else:
            normalized = (MAX_BOUND - distance) / (MAX_BOUND - MIN_BOUND)
            semantic_score = int(normalized * 100)

        real_resume_id = metadata.get("resume_id", cand_id)
        profile_json_file = profiles_path / f"{real_resume_id}.json"
        
        if profile_json_file.exists():
            candidate_profile = load_json_file(profile_json_file)
            cand_name = candidate_profile.get("candidate_name", f"Candidate {real_resume_id}")
            cand_skills = candidate_profile.get("top_skills", candidate_profile.get("skills", []))

            yoe_str = str(candidate_profile.get("years_of_experience", "0"))
            cand_yoe = int("".join(filter(str.isdigit, yoe_str)) or 0)
            yoe_check = "✓ Pass" if cand_yoe >= min_years else f"Gap ({cand_yoe}/{min_years} Years)"
        else:
            cand_name = f"Missing Profile ({real_resume_id})"
            cand_skills = []
            yoe_check = "Unknown"

        analysis_report = run_explanation_engine(required_skills, cand_skills)

        if len(analysis_report.get("matched",[])) == 0:
            semantic_score = 0
    
        ranked_matches.append(
            {
                "id": real_resume_id,
                "name": cand_name,
                "score": semantic_score,
                "yoe_status": yoe_check,
                "matched_skills": analysis_report.get("matched", []),
                "missing_skills": analysis_report.get("missing", []),
                "reasoning": analysis_report.get("reason", ""),
            }
        )

    unique_matches = {}
    for match in ranked_matches:
        if match["id"] not in unique_matches or match["score"] > unique_matches[match["id"]]["score"]:
            unique_matches[match["id"]] = match

    return sorted(unique_matches.values(), key=lambda item: item["score"], reverse=True)


if __name__ == "__main__":
    TARGET_JD_JSON = "../data/jds/jd.json"
    CANDIDATE_PROFILES_DIR = "../candidate_profiles"

    # jd_dictionary = load_json_file(TARGET_JD_JSON)
    jd_dictionary = f"""
    About the Role:
We are seeking a high-performing Full Stack Software Engineer to join our core product engineering group. In this role, you will be responsible for building out scalable user interfaces and maintaining cloud-native backend microservices.

Required Technical Skills & Competencies:
- Front-end architecture built entirely using React and TypeScript.
- Server-side infrastructure scaling on Node.js utilizing the Express framework.
- Core relational database data persistence layers structured around PostgreSQL.
- Solid understanding of modern DevOps workflows, specifically containerization with Docker and deployment pipelines across AWS.
- Hands-on experience building, securing, and testing resilient REST APIs.

Qualifications:
- A minimum of 4 Years of professional experience working within a modern product-driven environment.
- Strong collaborative mindset and experience with agile software development lifecycles.
"""
    results = run_candidate_matcher(jd_dictionary, profiles_dir=CANDIDATE_PROFILES_DIR)

    print(results)
    