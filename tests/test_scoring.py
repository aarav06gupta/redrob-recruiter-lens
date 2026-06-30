import unittest

from redrob_ranker.scoring import rank_candidates, score_candidate


def candidate(
    candidate_id,
    title,
    summary,
    skills,
    career,
    years=7.0,
    company="Razorpay",
    industry="Fintech",
    location="Noida, Uttar Pradesh",
):
    return {
        "candidate_id": candidate_id,
        "profile": {
            "anonymized_name": "Test Candidate",
            "headline": title,
            "summary": summary,
            "location": location,
            "country": "India",
            "years_of_experience": years,
            "current_title": title,
            "current_company": company,
            "current_company_size": "1001-5000",
            "current_industry": industry,
        },
        "career_history": career,
        "education": [],
        "skills": skills,
        "certifications": [],
        "languages": [],
        "redrob_signals": {
            "profile_completeness_score": 92,
            "signup_date": "2025-01-01",
            "last_active_date": "2026-05-20",
            "open_to_work_flag": True,
            "profile_views_received_30d": 20,
            "applications_submitted_30d": 2,
            "recruiter_response_rate": 0.8,
            "avg_response_time_hours": 12,
            "skill_assessment_scores": {},
            "connection_count": 200,
            "endorsements_received": 50,
            "notice_period_days": 30,
            "expected_salary_range_inr_lpa": {"min": 25, "max": 38},
            "preferred_work_mode": "hybrid",
            "willing_to_relocate": True,
            "github_activity_score": 75,
            "search_appearance_30d": 100,
            "saved_by_recruiters_30d": 5,
            "interview_completion_rate": 0.9,
            "offer_acceptance_rate": 0.8,
            "verified_email": True,
            "verified_phone": True,
            "linkedin_connected": True,
        },
    }


def skill(name, months=36, proficiency="advanced", endorsements=30):
    return {
        "name": name,
        "proficiency": proficiency,
        "endorsements": endorsements,
        "duration_months": months,
    }


class ScoringTests(unittest.TestCase):
    def test_career_evidence_beats_keyword_stuffing(self):
        strong = candidate(
            "CAND_0000001",
            "Senior Machine Learning Engineer",
            "Built production search, retrieval, ranking, and evaluation systems.",
            [skill("Information Retrieval"), skill("Learning to Rank"), skill("Python")],
            [
                {
                    "company": "Razorpay",
                    "title": "Senior Machine Learning Engineer",
                    "start_date": "2021-01-01",
                    "end_date": None,
                    "duration_months": 60,
                    "is_current": True,
                    "industry": "Fintech",
                    "company_size": "1001-5000",
                    "description": "Owned the ranking layer for a product search system, including learning to rank, NDCG evaluation, and live A/B tests.",
                }
            ],
        )
        stuffer = candidate(
            "CAND_0000002",
            "Marketing Manager",
            "Curious about AI tools.",
            [
                skill("Information Retrieval"),
                skill("Learning to Rank"),
                skill("RAG"),
                skill("Pinecone"),
                skill("FAISS"),
                skill("Embeddings"),
                skill("Semantic Search"),
            ],
            [
                {
                    "company": "Acme Corp",
                    "title": "Marketing Manager",
                    "start_date": "2021-01-01",
                    "end_date": None,
                    "duration_months": 60,
                    "is_current": True,
                    "industry": "Manufacturing",
                    "company_size": "201-500",
                    "description": "Owned campaign planning, brand messaging, and stakeholder communication.",
                }
            ],
            company="Acme Corp",
            industry="Manufacturing",
        )

        self.assertGreater(score_candidate(strong).score, score_candidate(stuffer).score)

    def test_company_founding_honeypot_is_capped(self):
        impossible = candidate(
            "CAND_0000003",
            "Senior AI Engineer",
            "Strong search and ranking profile.",
            [skill("Ranking Systems"), skill("Search Backend")],
            [
                {
                    "company": "Sarvam AI",
                    "title": "Senior AI Engineer",
                    "start_date": "2019-01-01",
                    "end_date": None,
                    "duration_months": 84,
                    "is_current": True,
                    "industry": "AI/ML",
                    "company_size": "51-200",
                    "description": "Owned production search and ranking systems.",
                }
            ],
            company="Sarvam AI",
            industry="AI/ML",
        )
        self.assertLessEqual(score_candidate(impossible).score, 0.18)

    def test_strong_candidate_score_stays_below_perfect(self):
        strong = candidate(
            "CAND_0000004",
            "Senior Machine Learning Engineer",
            "Built production search, retrieval, ranking, and evaluation systems.",
            [skill("Information Retrieval"), skill("Learning to Rank"), skill("Python")],
            [
                {
                    "company": "Razorpay",
                    "title": "Senior Machine Learning Engineer",
                    "start_date": "2021-01-01",
                    "end_date": None,
                    "duration_months": 60,
                    "is_current": True,
                    "industry": "Fintech",
                    "company_size": "1001-5000",
                    "description": "Owned the ranking layer for a product search system, including learning to rank, NDCG evaluation, and live A/B tests.",
                }
            ],
        )

        score = score_candidate(strong).score
        self.assertGreater(score, 0.8)
        self.assertLess(score, 1.0)

    def test_ranked_scores_are_monotonic(self):
        rows = [
            candidate(
                "CAND_0000001",
                "Search Engineer",
                "Production ranking systems.",
                [skill("Learning to Rank")],
                [
                    {
                        "company": "Razorpay",
                        "title": "Search Engineer",
                        "start_date": "2021-01-01",
                        "end_date": None,
                        "duration_months": 60,
                        "is_current": True,
                        "industry": "Fintech",
                        "company_size": "1001-5000",
                        "description": "Owned the ranking layer for product search.",
                    }
                ],
            ),
            candidate(
                "CAND_0000002",
                "Search Engineer",
                "Production ranking systems.",
                [skill("Learning to Rank")],
                [
                    {
                        "company": "Razorpay",
                        "title": "Search Engineer",
                        "start_date": "2021-01-01",
                        "end_date": None,
                        "duration_months": 60,
                        "is_current": True,
                        "industry": "Fintech",
                        "company_size": "1001-5000",
                        "description": "Owned the ranking layer for product search.",
                    }
                ],
            ),
        ]
        ranked = rank_candidates(rows, top_k=2)
        self.assertGreater(ranked[0].score, ranked[1].score)


if __name__ == "__main__":
    unittest.main()
