from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
import math
import re
from typing import Iterable


REFERENCE_DATE = date(2026, 6, 1)
DISPLAY_SCORE_STEP = 0.000001

# The weights below are intentionally plain. In a real recruiter conversation,
# these are the knobs we would debate and tune with hiring feedback.
SCORING_WEIGHTS = {
    "career": 0.29,
    "role": 0.17,
    "skill": 0.14,
    "experience": 0.13,
    "company": 0.10,
    "logistics": 0.07,
    "behavior": 0.10,
}

SYNERGY_BONUSES = {
    "career_in_band": 0.035,
    "role_and_skills": 0.025,
    "product_and_location": 0.015,
    "high_availability": 0.015,
}

PROFICIENCY = {
    "beginner": 0.35,
    "intermediate": 0.65,
    "advanced": 0.88,
    "expert": 1.0,
}

CORE_SKILLS = {
    "information retrieval": 1.0,
    "learning to rank": 1.0,
    "semantic search": 0.96,
    "vector search": 0.92,
    "embeddings": 0.88,
    "recommendation systems": 0.9,
    "ranking systems": 1.0,
    "search backend": 0.9,
    "search infrastructure": 0.9,
    "search & discovery": 0.95,
    "bm25": 0.78,
    "faiss": 0.76,
    "pinecone": 0.7,
    "qdrant": 0.7,
    "weaviate": 0.7,
    "milvus": 0.7,
    "elasticsearch": 0.66,
    "opensearch": 0.66,
    "sentence transformers": 0.7,
    "llms": 0.54,
    "rag": 0.62,
    "fine-tuning llms": 0.52,
    "lora": 0.42,
    "qlora": 0.42,
    "peft": 0.42,
    "mlops": 0.56,
    "mlflow": 0.5,
    "kubeflow": 0.48,
    "bentoml": 0.45,
    "feature engineering": 0.5,
    "python": 0.5,
    "pytorch": 0.44,
    "tensorflow": 0.4,
}

ADJACENT_SKILLS = {
    "spark",
    "airflow",
    "kafka",
    "data pipelines",
    "apache beam",
    "databricks",
    "snowflake",
    "bigquery",
    "fastapi",
    "docker",
    "kubernetes",
    "aws",
    "gcp",
    "azure",
    "microservices",
    "rest apis",
    "sql",
    "statistical modeling",
    "machine learning",
    "deep learning",
    "data science",
}

NOISY_AI_SKILLS = {
    "langchain",
    "llamaindex",
    "prompt engineering",
    "openai api",
    "hugging face transformers",
}

CV_SPEECH_SKILLS = {
    "computer vision",
    "image classification",
    "object detection",
    "opencv",
    "yolo",
    "cnn",
    "gans",
    "diffusion models",
    "speech recognition",
    "asr",
    "tts",
    "reinforcement learning",
    "forecasting",
    "time series",
}

PRODUCT_COMPANIES = {
    "Adobe",
    "Amazon",
    "Apple",
    "BYJU'S",
    "CRED",
    "Dream11",
    "Flipkart",
    "Freshworks",
    "Glance",
    "Google",
    "Haptik",
    "InMobi",
    "Krutrim",
    "LinkedIn",
    "Locobuzz",
    "Mad Street Den",
    "Meesho",
    "Meta",
    "Microsoft",
    "Netflix",
    "Niramai",
    "Nykaa",
    "Observe.AI",
    "Ola",
    "Paytm",
    "PharmEasy",
    "PhonePe",
    "PolicyBazaar",
    "Razorpay",
    "Rephrase.ai",
    "Saarthi.ai",
    "Salesforce",
    "Sarvam AI",
    "Swiggy",
    "Uber",
    "Unacademy",
    "Vedantu",
    "Verloop.io",
    "Wysa",
    "Yellow.ai",
    "Zomato",
    "Zoho",
    "upGrad",
}

AI_PRODUCT_COMPANIES = {
    "Glance",
    "Haptik",
    "Krutrim",
    "Mad Street Den",
    "Niramai",
    "Observe.AI",
    "Rephrase.ai",
    "Saarthi.ai",
    "Sarvam AI",
    "Verloop.io",
    "Wysa",
    "Yellow.ai",
}

SERVICES_COMPANIES = {
    "Accenture",
    "Capgemini",
    "Cognizant",
    "Genpact AI",
    "HCL",
    "Infosys",
    "Mindtree",
    "Mphasis",
    "TCS",
    "Tech Mahindra",
    "Wipro",
}

COMPANY_FOUNDED = {
    "Adobe": 1982,
    "Amazon": 1994,
    "Apple": 1976,
    "BYJU'S": 2011,
    "CRED": 2018,
    "Dream11": 2008,
    "Flipkart": 2007,
    "Freshworks": 2010,
    "Glance": 2019,
    "Google": 1998,
    "Haptik": 2013,
    "InMobi": 2007,
    "Krutrim": 2023,
    "LinkedIn": 2002,
    "Locobuzz": 2011,
    "Mad Street Den": 2013,
    "Meesho": 2015,
    "Meta": 2004,
    "Microsoft": 1975,
    "Netflix": 1997,
    "Niramai": 2016,
    "Nykaa": 2012,
    "Observe.AI": 2017,
    "Ola": 2010,
    "Paytm": 2010,
    "PharmEasy": 2015,
    "PhonePe": 2015,
    "PolicyBazaar": 2008,
    "Razorpay": 2014,
    "Rephrase.ai": 2019,
    "Saarthi.ai": 2017,
    "Salesforce": 1999,
    "Sarvam AI": 2023,
    "Swiggy": 2014,
    "Uber": 2009,
    "Unacademy": 2015,
    "Vedantu": 2011,
    "Verloop.io": 2015,
    "Wysa": 2015,
    "Yellow.ai": 2016,
    "Zomato": 2008,
    "Zoho": 1996,
    "upGrad": 2015,
}

PREFERRED_CITIES = {
    "pune": 1.0,
    "noida": 1.0,
    "gurgaon": 0.88,
    "delhi": 0.86,
    "hyderabad": 0.84,
    "bangalore": 0.82,
    "mumbai": 0.82,
}

GOOD_INDIA_CITIES = {
    "chennai",
    "kolkata",
    "ahmedabad",
    "chandigarh",
    "coimbatore",
    "jaipur",
    "indore",
    "kochi",
    "trivandrum",
    "vizag",
}

TITLE_WEIGHTS = [
    (re.compile(r"\bsenior ml engineer\b.*\b(search|ranking)\b", re.I), 1.0),
    (re.compile(r"\bsenior ai engineer\b", re.I), 0.98),
    (re.compile(r"\blead ai engineer\b", re.I), 0.96),
    (re.compile(r"\bstaff machine learning engineer\b", re.I), 0.94),
    (re.compile(r"\bsenior machine learning engineer\b", re.I), 0.9),
    (re.compile(r"\brecommendation systems engineer\b", re.I), 0.88),
    (re.compile(r"\bsearch engineer\b", re.I), 0.87),
    (re.compile(r"\bsenior nlp engineer\b", re.I), 0.84),
    (re.compile(r"\bapplied ml engineer\b", re.I), 0.8),
    (re.compile(r"\bmachine learning engineer\b", re.I), 0.78),
    (re.compile(r"\bnlp engineer\b", re.I), 0.72),
    (re.compile(r"\bsenior applied scientist\b", re.I), 0.7),
    (re.compile(r"\bsenior data scientist\b", re.I), 0.68),
    (re.compile(r"\bsenior software engineer \(ml\)\b", re.I), 0.66),
    (re.compile(r"\bml engineer\b", re.I), 0.62),
    (re.compile(r"\bai research engineer\b", re.I), 0.5),
    (re.compile(r"\bdata scientist\b", re.I), 0.48),
    (re.compile(r"\bai specialist\b", re.I), 0.42),
    (re.compile(r"\bsenior data engineer\b", re.I), 0.34),
    (re.compile(r"\bdata engineer\b", re.I), 0.28),
    (re.compile(r"\bbackend engineer\b", re.I), 0.26),
    (re.compile(r"\bsoftware engineer\b", re.I), 0.24),
    (re.compile(r"\bcloud engineer\b|\bdevops engineer\b", re.I), 0.18),
]

NON_TECH_TITLE = re.compile(
    r"\b(marketing manager|hr manager|sales executive|accountant|graphic designer|"
    r"mechanical engineer|civil engineer|customer support|content writer|operations manager|"
    r"business analyst|project manager)\b",
    re.I,
)

CORE_CAREER_PATTERNS = [
    (re.compile(r"\brag[- ]based ranking pipeline\b", re.I), 1.0),
    (re.compile(r"\b(search|ranking|recommendation|personalization) (system|layer|infrastructure)\b", re.I), 0.95),
    (re.compile(r"\b(search and discovery|discovery feed|personalization infrastructure)\b", re.I), 0.92),
    (re.compile(r"\bsemantic search\b|\bembedding[- ]based search\b", re.I), 0.88),
    (re.compile(r"\bvector (database|search|index|representations)\b", re.I), 0.78),
    (re.compile(r"\blearning to rank\b|\bxgboost ranking\b|\branking models?\b", re.I), 0.86),
    (re.compile(r"\bBM25\b|\bhybrid search\b|\binformation retrieval\b", re.I), 0.75),
    (re.compile(r"\bFAISS\b|\bPinecone\b|\bQdrant\b|\bWeaviate\b|\bMilvus\b|\bOpenSearch\b|\bElasticsearch\b", re.I), 0.55),
    (re.compile(r"\bNDCG\b|\bMRR\b|\bMAP\b|\boffline benchmark|\bA/B test", re.I), 0.72),
    (re.compile(r"\bfine[- ]tuned?\b|\bLoRA\b|\bQLoRA\b|\bPEFT\b", re.I), 0.45),
    (re.compile(r"\bproduction ML pipelines?\b|\bmodel deployment\b|\bMLOps\b|\bKubeflow\b|\bMLflow\b", re.I), 0.48),
    (re.compile(r"\bserving [0-9]+[MK]\+? (users|queries|documents)\b|\bdeployed to real users\b", re.I), 0.45),
    (re.compile(r"\bconnect .* relevant\b|\blearns from user behavior\b", re.I), 0.65),
]

ADJACENT_CAREER_PATTERNS = [
    (re.compile(r"\bdata pipelines?\b|\bSpark\b|\bAirflow\b|\bKafka\b", re.I), 0.28),
    (re.compile(r"\bfeature pipelines?\b|\bfeature engineering\b", re.I), 0.32),
    (re.compile(r"\bbackend systems?\b|\bmicroservices?\b|\bFastAPI\b|\bPython\b", re.I), 0.22),
    (re.compile(r"\bNLP pipelines?\b|\bdocument classification\b|\bsentiment analysis\b", re.I), 0.3),
    (re.compile(r"\bpredictive modeling\b|\bfraud-detection\b|\bchurn prediction\b", re.I), 0.22),
]

RESEARCH_OR_SIDE_PROJECT_PATTERNS = re.compile(
    r"\bpure research\b|\bacademic lab\b|\bside project\b|\bkaggle\b|\bonline courses?\b|"
    r"\bself-directed\b|\bexperimented with ChatGPT\b|\bcurious about how AI\b",
    re.I,
)

CV_SPEECH_PATTERN = re.compile(
    r"\bcomputer vision\b|\bimage moderation\b|\bimage classification\b|\bobject detection\b|"
    r"\bYOLO\b|\bOpenCV\b|\bspeech recognition\b|\bASR\b|\bTTS\b|\brobotics\b",
    re.I,
)


@dataclass(frozen=True)
class RankedCandidate:
    candidate_id: str
    rank: int
    score: float
    reasoning: str
    diagnostics: dict[str, object]


@dataclass
class CandidateScore:
    candidate: dict
    score: float
    diagnostics: dict[str, object]


def clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return min(hi, max(lo, value))


def calibrated_score(raw_signal: float) -> float:
    """Convert scorer evidence into a readable 0-1 confidence score.

    A hard clamp made many excellent candidates display as 1.000000, which hid
    meaningful differences. A logistic curve keeps order, avoids saturation,
    and still reads naturally as confidence.
    """
    return clamp(1.0 / (1.0 + math.exp(-7.0 * (raw_signal - 0.5))))


def parse_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return datetime.strptime(value[:10], "%Y-%m-%d").date()
    except ValueError:
        return None


def norm(value: str | None) -> str:
    return (value or "").strip().lower()


def title_fit(title: str) -> float:
    for pattern, weight in TITLE_WEIGHTS:
        if pattern.search(title):
            return weight
    if NON_TECH_TITLE.search(title):
        return 0.02
    return 0.08


def duration_factor(months: int | float | None) -> float:
    if not months:
        return 0.18
    if months < 6:
        return 0.32
    if months < 12:
        return 0.52
    if months < 24:
        return 0.78
    if months < 48:
        return 0.94
    return 1.0


def endorsement_factor(endorsements: int | None) -> float:
    endorsements = endorsements or 0
    return clamp(0.55 + math.log1p(endorsements) / math.log(61) * 0.45)


def skill_scores(candidate: dict, career_support: float) -> tuple[float, list[str], dict[str, int]]:
    signals = candidate.get("redrob_signals", {})
    assessments = {norm(k): float(v) for k, v in signals.get("skill_assessment_scores", {}).items()}
    raw_points = 0.0
    max_points = 0.0
    evidence: list[tuple[float, str]] = []
    counts = {"core": 0, "adjacent": 0, "noisy": 0, "cv_speech": 0, "impossible": 0}

    for skill in candidate.get("skills", []):
        name = skill.get("name", "")
        key = norm(name)
        proficiency = PROFICIENCY.get(norm(skill.get("proficiency")), 0.5)
        months = skill.get("duration_months") or 0
        if proficiency >= 0.88 and months <= 1:
            counts["impossible"] += 1

        if key in CORE_SKILLS:
            counts["core"] += 1
            base = CORE_SKILLS[key]
        elif key in ADJACENT_SKILLS:
            counts["adjacent"] += 1
            base = 0.24
        elif key in NOISY_AI_SKILLS:
            counts["noisy"] += 1
            base = 0.14
        elif key in CV_SPEECH_SKILLS:
            counts["cv_speech"] += 1
            base = 0.08
        else:
            continue

        assessment = assessments.get(key)
        assessment_factor = 1.0
        if assessment is not None:
            assessment_factor = 0.75 + clamp(assessment / 100.0) * 0.45

        trusted = (
            base
            * proficiency
            * duration_factor(months)
            * endorsement_factor(skill.get("endorsements"))
            * assessment_factor
        )
        raw_points += trusted
        max_points += base
        if key in CORE_SKILLS or key in ADJACENT_SKILLS:
            evidence.append((trusted, name))

    if max_points <= 0:
        return 0.0, [], counts

    support_factor = 0.35 + 0.65 * clamp(career_support / 1.5)
    skill_fit = clamp((raw_points / 4.8) * support_factor)
    top = [name for _, name in sorted(evidence, reverse=True)[:5]]
    return skill_fit, top, counts


def career_scores(candidate: dict) -> tuple[float, float, float, list[str], dict[str, object]]:
    career_fit = 0.0
    applied_months = 0.0
    strongest_role = 0.0
    evidence: list[tuple[float, str]] = []
    product_months = 0
    services_months = 0
    current_title = candidate.get("profile", {}).get("current_title", "")

    for idx, job in enumerate(candidate.get("career_history", [])):
        title = job.get("title", "")
        desc = job.get("description", "")
        company = job.get("company", "")
        months = float(job.get("duration_months") or 0)
        role = title_fit(title)
        strongest_role = max(strongest_role, role * (1.05 if idx == 0 else 1.0))

        text = f"{title}. {desc}. {job.get('industry', '')}"
        core = 0.0
        matched: list[str] = []
        for pattern, weight in CORE_CAREER_PATTERNS:
            if pattern.search(text):
                core += weight
                matched.append(pattern.pattern[:42])
        for pattern, weight in ADJACENT_CAREER_PATTERNS:
            if pattern.search(text):
                core += weight

        role_boost = 0.45 * role
        product_boost = 0.12 if company in PRODUCT_COMPANIES else 0.0
        if company in AI_PRODUCT_COMPANIES:
            product_boost += 0.08
        job_score = min(1.75, core + role_boost + product_boost)
        recency = 1.0 if idx == 0 else (0.86 if idx == 1 else 0.72)
        career_fit += job_score * duration_factor(months) * recency

        if role >= 0.45 or core >= 0.55:
            applied_months += months * min(1.0, 0.55 + core / 2.0 + role / 3.0)

        if company in PRODUCT_COMPANIES:
            product_months += int(months)
        if company in SERVICES_COMPANIES:
            services_months += int(months)

        if job_score >= 0.65:
            label = title
            if "ranking" in desc.lower():
                label += " with ranking"
            elif "semantic search" in desc.lower() or "embedding" in desc.lower():
                label += " with semantic search"
            elif "recommendation" in desc.lower():
                label += " with recommendation systems"
            elif "production ml" in desc.lower():
                label += " with production ML"
            evidence.append((job_score * recency, label))

    headline_summary = " ".join(
        [
            candidate.get("profile", {}).get("headline", ""),
            candidate.get("profile", {}).get("summary", ""),
            current_title,
        ]
    )
    summary_core = 0.0
    for pattern, weight in CORE_CAREER_PATTERNS:
        if pattern.search(headline_summary):
            summary_core += weight * 0.45
    if RESEARCH_OR_SIDE_PROJECT_PATTERNS.search(headline_summary):
        summary_core -= 0.18

    career_fit = clamp((career_fit + summary_core) / 3.4)
    applied_fit = clamp(applied_months / 54.0)
    top = [name for _, name in sorted(evidence, reverse=True)[:4]]
    details = {
        "applied_months": round(applied_months, 1),
        "product_months": product_months,
        "services_months": services_months,
        "strongest_role": strongest_role,
    }
    return career_fit, applied_fit, strongest_role, top, details


def experience_fit(years: float, applied_fit: float) -> float:
    if 5.0 <= years <= 9.0:
        total = 0.78 + 0.22 * (1.0 - min(abs(years - 7.0) / 2.5, 1.0))
    elif 4.0 <= years < 5.0:
        total = 0.62
    elif 9.0 < years <= 10.5:
        total = 0.66
    elif 3.0 <= years < 4.0:
        total = 0.38
    elif 10.5 < years <= 12.0:
        total = 0.42
    else:
        total = 0.16
    return clamp(0.68 * total + 0.32 * applied_fit)


def company_fit(candidate: dict, career_details: dict[str, object]) -> float:
    profile = candidate.get("profile", {})
    current_company = profile.get("current_company", "")
    current_industry = profile.get("current_industry", "")
    product_months = float(career_details.get("product_months") or 0)
    services_months = float(career_details.get("services_months") or 0)

    score = 0.28
    if current_company in PRODUCT_COMPANIES:
        score += 0.28
    if current_company in AI_PRODUCT_COMPANIES:
        score += 0.12
    if current_industry in {"AI/ML", "SaaS", "Fintech", "E-commerce", "Food Delivery", "Gaming", "Internet"}:
        score += 0.16
    elif "AI" in current_industry or "Tech" in current_industry:
        score += 0.1
    elif current_industry == "IT Services":
        score -= 0.07

    if product_months:
        score += min(0.22, product_months / 84.0 * 0.22)
    if product_months == 0 and services_months > 0:
        score -= 0.18
    return clamp(score)


def logistics_fit(candidate: dict) -> float:
    profile = candidate.get("profile", {})
    signals = candidate.get("redrob_signals", {})
    country = profile.get("country", "")
    location = norm(profile.get("location"))
    willing = bool(signals.get("willing_to_relocate"))
    mode = norm(signals.get("preferred_work_mode"))

    if country != "India":
        base = 0.18 + (0.16 if willing else 0.0)
    else:
        base = 0.52
        for city, value in PREFERRED_CITIES.items():
            if city in location:
                base = value
                break
        else:
            if any(city in location for city in GOOD_INDIA_CITIES):
                base = 0.68
        if willing and base < 0.82:
            base += 0.08

    if mode in {"hybrid", "flexible"}:
        base += 0.05
    elif mode == "remote":
        base -= 0.04
    return clamp(base)


def behavior_fit(candidate: dict) -> float:
    signals = candidate.get("redrob_signals", {})
    last_active = parse_date(signals.get("last_active_date"))
    if last_active is None:
        recency = 0.1
    else:
        days = max(0, (REFERENCE_DATE - last_active).days)
        if days <= 14:
            recency = 1.0
        elif days <= 30:
            recency = 0.88
        elif days <= 60:
            recency = 0.72
        elif days <= 120:
            recency = 0.48
        else:
            recency = 0.18

    response = clamp(float(signals.get("recruiter_response_rate") or 0))
    response_time = float(signals.get("avg_response_time_hours") or 240)
    response_speed = clamp(1.0 - response_time / 240.0)
    profile_complete = clamp(float(signals.get("profile_completeness_score") or 0) / 100.0)
    interview = clamp(float(signals.get("interview_completion_rate") or 0))
    offer = signals.get("offer_acceptance_rate")
    offer_score = 0.45 if offer is None or float(offer) < 0 else clamp(float(offer))
    github = float(signals.get("github_activity_score") or -1)
    github_score = 0.35 if github < 0 else clamp(github / 100.0)
    notice = int(signals.get("notice_period_days") or 180)
    if notice <= 30:
        notice_score = 1.0
    elif notice <= 60:
        notice_score = 0.72
    elif notice <= 90:
        notice_score = 0.42
    elif notice <= 120:
        notice_score = 0.24
    else:
        notice_score = 0.08

    open_to_work = 1.0 if signals.get("open_to_work_flag") else 0.28
    verified = (
        0.34 * bool(signals.get("verified_email"))
        + 0.33 * bool(signals.get("verified_phone"))
        + 0.33 * bool(signals.get("linkedin_connected"))
    )
    recruiter_pull = clamp(
        math.log1p(int(signals.get("saved_by_recruiters_30d") or 0)) / math.log(16)
        * 0.55
        + math.log1p(int(signals.get("profile_views_received_30d") or 0)) / math.log(101)
        * 0.45
    )

    return clamp(
        0.18 * recency
        + 0.19 * response
        + 0.09 * response_speed
        + 0.11 * open_to_work
        + 0.12 * notice_score
        + 0.08 * github_score
        + 0.06 * profile_complete
        + 0.05 * interview
        + 0.03 * offer_score
        + 0.03 * verified
        + 0.06 * recruiter_pull
    )


def risk_penalty(
    candidate: dict,
    career_fit: float,
    role_fit: float,
    skill_counts: dict[str, int],
    career_details: dict[str, object],
) -> tuple[float, list[str]]:
    profile = candidate.get("profile", {})
    signals = candidate.get("redrob_signals", {})
    risk = 0.0
    flags: list[str] = []
    title = profile.get("current_title", "")
    summary = profile.get("summary", "")
    all_career_text = " ".join(
        f"{h.get('title','')} {h.get('description','')}" for h in candidate.get("career_history", [])
    )

    if skill_counts["impossible"] >= 2:
        risk += 0.35
        flags.append("impossible skill durations")
    if skill_counts["core"] >= 7 and career_fit < 0.23 and role_fit < 0.28:
        risk += 0.38
        flags.append("AI keyword stuffing without career evidence")
    if NON_TECH_TITLE.search(title) and career_fit < 0.35:
        risk += 0.28
        flags.append("non-technical current role")
    if RESEARCH_OR_SIDE_PROJECT_PATTERNS.search(summary) and career_fit < 0.55:
        risk += 0.14
        flags.append("self-learning or research-heavy AI signal")
    if CV_SPEECH_PATTERN.search(all_career_text) and career_fit < 0.6:
        risk += 0.16
        flags.append("CV/speech-heavy rather than retrieval/ranking")

    product_months = float(career_details.get("product_months") or 0)
    services_months = float(career_details.get("services_months") or 0)
    if services_months > 48 and product_months == 0:
        risk += 0.18
        flags.append("services-only career")

    history = candidate.get("career_history", [])
    if len(history) >= 4:
        avg_tenure = sum(float(h.get("duration_months") or 0) for h in history) / len(history)
        seniorish = sum(1 for h in history if re.search(r"\b(senior|staff|lead|principal)\b", h.get("title", ""), re.I))
        if avg_tenure < 20 and seniorish >= 2:
            risk += 0.12
            flags.append("short-tenure senior title trajectory")

    for job in history:
        start = parse_date(job.get("start_date"))
        founded = COMPANY_FOUNDED.get(job.get("company", ""))
        if start and founded and start.year < founded:
            risk += 0.45
            flags.append(f"job predates {job.get('company')} founding")
            break

    if int(signals.get("notice_period_days") or 0) > 120:
        risk += 0.05
        flags.append("very long notice period")
    if float(signals.get("recruiter_response_rate") or 0) < 0.12:
        risk += 0.05
        flags.append("low recruiter response rate")

    return min(risk, 0.82), flags


def cap_for_missing_evidence(score: float, career_fit: float, role_fit: float, logistics: float, flags: list[str]) -> float:
    capped = score
    if career_fit < 0.18 and role_fit < 0.32:
        capped = min(capped, 0.42)
    if "AI keyword stuffing without career evidence" in flags:
        capped = min(capped, 0.28)
    if "job predates" in " ".join(flags) or "impossible skill durations" in flags:
        capped = min(capped, 0.18)
    if logistics < 0.22 and career_fit < 0.72:
        capped = min(capped, 0.74)
    return capped


def score_candidate(candidate: dict) -> CandidateScore:
    profile = candidate.get("profile", {})
    career_fit, applied_fit, strongest_role, career_evidence, career_details = career_scores(candidate)
    current_role = title_fit(profile.get("current_title", ""))
    role_fit = clamp(0.72 * current_role + 0.28 * strongest_role)
    skill_fit, skill_evidence, skill_counts = skill_scores(candidate, career_fit + applied_fit)
    exp_fit = experience_fit(float(profile.get("years_of_experience") or 0), applied_fit)
    comp_fit = company_fit(candidate, career_details)
    log_fit = logistics_fit(candidate)
    beh_fit = behavior_fit(candidate)
    risk, flags = risk_penalty(candidate, career_fit, role_fit, skill_counts, career_details)

    evidence_score = (
        SCORING_WEIGHTS["career"] * career_fit
        + SCORING_WEIGHTS["role"] * role_fit
        + SCORING_WEIGHTS["skill"] * skill_fit
        + SCORING_WEIGHTS["experience"] * exp_fit
        + SCORING_WEIGHTS["company"] * comp_fit
        + SCORING_WEIGHTS["logistics"] * log_fit
        + SCORING_WEIGHTS["behavior"] * beh_fit
    )

    synergy = 0.0
    if career_fit > 0.7 and 5 <= float(profile.get("years_of_experience") or 0) <= 9:
        synergy += SYNERGY_BONUSES["career_in_band"]
    if role_fit > 0.75 and skill_fit > 0.45:
        synergy += SYNERGY_BONUSES["role_and_skills"]
    if comp_fit > 0.68 and log_fit > 0.68:
        synergy += SYNERGY_BONUSES["product_and_location"]
    if beh_fit > 0.72:
        synergy += SYNERGY_BONUSES["high_availability"]

    raw_score = evidence_score + synergy - risk
    final_score = cap_for_missing_evidence(
        calibrated_score(raw_score), career_fit, role_fit, log_fit, flags
    )
    top_evidence = career_evidence + skill_evidence[:3]
    diagnostics = {
        "title": profile.get("current_title", ""),
        "location": f"{profile.get('location', '')}, {profile.get('country', '')}",
        "experience_years": profile.get("years_of_experience", ""),
        "career_fit": career_fit,
        "role_fit": role_fit,
        "skill_fit": skill_fit,
        "experience_fit": exp_fit,
        "company_fit": comp_fit,
        "logistics_fit": log_fit,
        "behavior_fit": beh_fit,
        "risk_penalty": risk,
        "evidence_score": evidence_score,
        "raw_score": raw_score,
        "risk_flags": flags,
        "top_evidence": top_evidence,
        "skill_counts": skill_counts,
        "applied_months": career_details.get("applied_months"),
    }
    return CandidateScore(candidate=candidate, score=final_score, diagnostics=diagnostics)


def reason_for(scored: CandidateScore, rank: int) -> str:
    c = scored.candidate
    p = c.get("profile", {})
    s = c.get("redrob_signals", {})
    d = scored.diagnostics
    title = p.get("current_title", "Candidate")
    years = p.get("years_of_experience", "?")
    location = p.get("location", "unknown location")
    evidence = d.get("top_evidence", [])
    if evidence:
        evidence_text = ", ".join(str(x) for x in evidence[:2])
    else:
        evidence_text = "adjacent ML/software evidence"

    signal_bits = []
    response = s.get("recruiter_response_rate")
    if isinstance(response, (int, float)):
        signal_bits.append(f"{response:.0%} recruiter response")
    notice = s.get("notice_period_days")
    if isinstance(notice, int):
        signal_bits.append(f"{notice}-day notice")
    if s.get("open_to_work_flag"):
        signal_bits.append("open to work")
    if location:
        signal_bits.append(location)
    signal_text = "; ".join(signal_bits[:4])

    concerns = d.get("risk_flags", [])
    if rank <= 20:
        tone = "Strong fit"
    elif rank <= 60:
        tone = "Good fit"
    else:
        tone = "Qualified but lower-confidence fit"

    concern_text = ""
    if concerns:
        concern_text = f" Concern: {concerns[0]}."
    return (
        f"{tone}: {title} with {years} years; evidence includes {evidence_text}. "
        f"Signals: {signal_text}.{concern_text}"
    )


def rank_candidates(candidates: Iterable[dict], top_k: int = 100) -> list[RankedCandidate]:
    scored = [score_candidate(candidate) for candidate in candidates]
    scored.sort(
        key=lambda item: (
            -item.score,
            -float(item.diagnostics.get("career_fit") or 0),
            -float(item.diagnostics.get("behavior_fit") or 0),
            item.candidate.get("candidate_id", ""),
        )
    )
    ranked: list[RankedCandidate] = []
    previous_display_score: float | None = None
    for rank, item in enumerate(scored[:top_k], start=1):
        display_score = item.score
        if previous_display_score is not None and display_score >= previous_display_score:
            display_score = max(0.0, previous_display_score - DISPLAY_SCORE_STEP)
        previous_display_score = display_score
        ranked.append(
            RankedCandidate(
                candidate_id=item.candidate.get("candidate_id", ""),
                rank=rank,
                score=display_score,
                reasoning=reason_for(item, rank),
                diagnostics=item.diagnostics,
            )
        )
    return ranked
