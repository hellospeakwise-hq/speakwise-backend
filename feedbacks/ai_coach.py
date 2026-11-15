"""AI Coach (SpeakBot) service for public speakers on SpeakWise.

Integrates Google Gemini API with fallback to Groq Cloud API, plus a smart
analytical fallback engine when keys are absent during local testing.
"""

import logging
import os
import uuid
from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple

import requests

from feedbacks.models import RATING_FIELDS, Feedback
from profiles.models.speaker_models import SpeakerProfile

logger = logging.getLogger(__name__)

GEMINI_API_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
)
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

DEFAULT_GEMINI_MODELS = ["gemini-3.8-flash", "gemini-2.5-flash"]
DEFAULT_GROQ_MODELS = ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"]


def build_speaker_feedback_data(
    speaker: SpeakerProfile, experience_id: Optional[str] = None
) -> Dict[str, Any]:
    """Compile aggregated metrics and anonymized feedback for the speaker."""
    queryset = Feedback.objects.filter(speaker=speaker).select_related("experience")

    if experience_id:
        # Distinguish between UUID and feedback_slug safely
        is_uuid = False
        parsed_uuid = None
        try:
            parsed_uuid = uuid.UUID(str(experience_id))
            is_uuid = True
        except (ValueError, TypeError, AttributeError):
            is_uuid = False

        if is_uuid:
            queryset = queryset.filter(experience__id=parsed_uuid)
        else:
            queryset = queryset.filter(experience__feedback_slug=experience_id)

    feedbacks = list(queryset.order_by("-created_at"))

    if not feedbacks:
        return {
            "total_feedbacks": 0,
            "talks_count": 0,
            "overall_avg": None,
            "dimension_averages": {},
            "talks": [],
            "top_strength": None,
            "top_growth_area": None,
        }

    # Aggregate dimension scores
    dimension_totals = defaultdict(int)
    talk_groups = defaultdict(list)

    for fb in feedbacks:
        for field in RATING_FIELDS:
            val = getattr(fb, field, None)
            if val is not None:
                dimension_totals[field] += val

        talk_key = fb.experience.id if fb.experience else "unassigned"
        talk_groups[talk_key].append(fb)

    total_fb_count = len(feedbacks)
    dimension_averages = {
        field: round(dimension_totals[field] / total_fb_count, 1)
        for field in RATING_FIELDS
    }

    # Identify strength and growth area
    sorted_dims = sorted(
        [(k, v) for k, v in dimension_averages.items() if k != "overall_rating"],
        key=lambda item: item[1],
        reverse=True,
    )
    top_strength = (
        sorted_dims[0][0].replace("_", " ").title() if sorted_dims else "Overall"
    )
    top_growth_area = (
        sorted_dims[-1][0].replace("_", " ").title() if sorted_dims else "Overall"
    )

    # Talks summary
    talks_data = []
    for _exp_id, group in talk_groups.items():
        sample_exp = group[0].experience
        talk_avg = round(sum(f.overall_rating for f in group) / len(group), 1)

        comments = [
            f.comments.strip() for f in group if f.comments and f.comments.strip()
        ]

        talk_info = {
            "topic": sample_exp.topic if sample_exp else "General Session",
            "event_name": sample_exp.event_name if sample_exp else "Unknown Event",
            "event_date": str(sample_exp.event_date)
            if sample_exp and sample_exp.event_date
            else "N/A",
            "feedback_count": len(group),
            "average_rating": talk_avg,
            "category_averages": {
                f: round(sum(getattr(item, f, 0) for item in group) / len(group), 1)
                for f in RATING_FIELDS
            },
            "comments": comments[:15],  # Cap comments per talk to keep tokens balanced
        }
        talks_data.append(talk_info)

    return {
        "total_feedbacks": total_fb_count,
        "talks_count": len(talks_data),
        "overall_avg": dimension_averages.get("overall_rating"),
        "dimension_averages": dimension_averages,
        "talks": talks_data,
        "top_strength": top_strength,
        "top_growth_area": top_growth_area,
    }


def format_feedback_context_prompt(data: Dict[str, Any]) -> str:
    """Format data dictionary into structured markdown for the LLM."""
    if data["total_feedbacks"] == 0:
        return "The speaker currently has no feedback submitted yet on SpeakWise."

    lines = [
        f"### Speaker Global Performance",
        f"- Total Feedback Reviews: {data['total_feedbacks']}",
        f"- Presentations Analyzed: {data['talks_count']}",
        f"- Overall Average Rating: {data['overall_avg']}/10",
        "",
        "### Dimension Averages (Scale 1–10):",
    ]
    for dim, score in data["dimension_averages"].items():
        label = dim.replace("_", " ").title()
        lines.append(f"- **{label}**: {score}/10")

    lines.append("\n### Presentation Breakdowns & Attendee Comments:")
    for talk in data["talks"]:
        lines.append(
            f'\n#### Talk: "{talk["topic"]}" at {talk["event_name"]} ({talk["event_date"]})'
        )
        lines.append(
            f"- Reviews: {talk['feedback_count']} | Average Rating: {talk['average_rating']}/10"
        )
        lines.append(
            "- Scores: "
            + ", ".join(
                f"{k.replace('_', ' ').title()}: {v}/10"
                for k, v in talk["category_averages"].items()
                if k != "overall_rating"
            )
        )
        if talk["comments"]:
            lines.append("- Audience Comments:")
            for comment in talk["comments"]:
                lines.append(f'  * "{comment}"')
        else:
            lines.append("- Audience Comments: None submitted with text.")

    return "\n".join(lines)


def get_system_prompt(feedback_context_md: str) -> str:
    """Return the system instruction for the AI speaker coach."""
    return f"""You are "SpeakBot", an expert public speaking and presentation coach on the SpeakWise platform.
Your mission is to help speakers transform attendee feedback and ratings into clear, actionable improvements for future talks.

Here is the speaker's real feedback data from their dashboard:
---
{feedback_context_md}
---

Guidelines:
1. Always base your advice, numbers, and comparisons on the real data provided above.
2. If asked which talk performed best or worst, compare their scores and cite specific dimensions (e.g., Clarity vs. Engagement).
3. Offer constructive, encouraging coaching advice with 2-3 specific, actionable recommendations.
4. If there are written attendee quotes, mention key themes or quote helpful feedback to validate your points.
5. Keep your tone professional, friendly, and empowering. Use GitHub-flavored markdown with bolding, lists, and clear headings.
6. If the speaker has no feedback yet, explain what metrics SpeakWise tracks (Engagement, Clarity, Content Depth, Knowledge, Practical Relevance) and how they can collect feedback with their QR codes.
"""


def _call_gemini_api(
    system_prompt: str, user_query: str, history: Optional[List[Dict[str, str]]] = None
) -> Tuple[Optional[str], Optional[str]]:
    """Query Google Gemini API. Loops through available candidate models."""
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        return None, None

    model_env = os.getenv("GEMINI_MODEL", "")
    models = (
        [m.strip() for m in model_env.split(",") if m.strip()]
        if model_env
        else DEFAULT_GEMINI_MODELS
    )

    # Prepare conversation contents
    contents = []
    if history:
        for msg in history:
            role = "model" if msg.get("role") in ("assistant", "model") else "user"
            contents.append({"role": role, "parts": [{"text": msg.get("content", "")}]})

    contents.append({"role": "user", "parts": [{"text": user_query}]})

    payload = {
        "system_instruction": {"parts": [{"text": system_prompt}]},
        "contents": contents,
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 1200,
        },
    }

    headers = {"Content-Type": "application/json"}

    for model in models:
        url = f"{GEMINI_API_URL.format(model=model)}?key={api_key}"
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=12)
            if resp.status_code == 200:
                data = resp.json()
                candidates = data.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts and "text" in parts[0]:
                        return parts[0]["text"], model
            else:
                logger.warning(
                    "Gemini API model %s failed with status %d: %s",
                    model,
                    resp.status_code,
                    resp.text[:200],
                )
        except Exception as e:
            logger.warning("Gemini API call error on %s: %s", model, e)

    return None, None


def _call_groq_api(
    system_prompt: str, user_query: str, history: Optional[List[Dict[str, str]]] = None
) -> Tuple[Optional[str], Optional[str]]:
    """Query Groq Cloud API as fallback or primary."""
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    if not api_key:
        return None, None

    model_env = os.getenv("GROQ_MODEL", "")
    models = (
        [m.strip() for m in model_env.split(",") if m.strip()]
        if model_env
        else DEFAULT_GROQ_MODELS
    )

    messages = [{"role": "system", "content": system_prompt}]
    if history:
        for msg in history:
            role = "assistant" if msg.get("role") in ("assistant", "model") else "user"
            messages.append({"role": role, "content": msg.get("content", "")})
    messages.append({"role": "user", "content": user_query})

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    for model in models:
        payload = {
            "model": model,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 1200,
        }
        try:
            resp = requests.post(
                GROQ_API_URL, headers=headers, json=payload, timeout=20
            )
            if resp.status_code == 200:
                data = resp.json()
                choices = data.get("choices", [])
                if choices:
                    text = choices[0].get("message", {}).get("content", "")
                    if text:
                        return text, model
            else:
                logger.warning(
                    "Groq API model %s returned status %d: %s",
                    model,
                    resp.status_code,
                    resp.text[:200],
                )
        except Exception as e:
            logger.warning("Groq API call error on %s: %s", model, e)

    return None, None


def _generate_analytical_fallback(data: Dict[str, Any], user_query: str) -> str:
    """Intelligent fallback generated locally from real statistics."""
    if data["total_feedbacks"] == 0:
        return (
            "### Welcome to SpeakBot AI Coach! 🎙️\n\n"
            "You haven't received any audience feedback on SpeakWise yet. Once you share your "
            "talk's QR code or link during your next speaking session, attendees can rate you across:\n\n"
            "- **Engagement** (Audience connection and energy)\n"
            "- **Clarity** (Structure, slides, and pacing)\n"
            "- **Content Depth** (Value and technical substance)\n"
            "- **Speaker Knowledge** (Command of the domain)\n"
            "- **Practical Relevance** (Real-world takeaways)\n\n"
            "Ask me anytime once feedback starts coming in, and I will highlight trends and coach you!"
        )

    overall = data["overall_avg"]
    top_strength = data["top_strength"]
    top_growth = data["top_growth_area"]
    talks = data["talks"]

    # Best and worst talk
    best_talk = max(talks, key=lambda t: t["average_rating"]) if talks else None
    worst_talk = min(talks, key=lambda t: t["average_rating"]) if talks else None

    # Sample comments
    all_comments = []
    for t in talks:
        all_comments.extend(t.get("comments", []))

    return (
        f"### SpeakBot Performance Analysis 🎯\n\n"
        f"Based on **{data['total_feedbacks']} feedback submissions** across your speaking engagements:\n\n"
        f"- **Overall Rating:** `{overall}/10`\n"
        f"- **Primary Strength:** **{top_strength}** (Audiences consistently rate you highly here)\n"
        f"- **Top Opportunity for Growth:** **{top_growth}** (Area where audience ratings have the most room to climb)\n\n"
        f"#### Presentation Performance:\n"
        + (
            f'- 🌟 **Strongest Session:** "{best_talk["topic"]}" at {best_talk["event_name"]} with an average of `{best_talk["average_rating"]}/10`.\n'
            if best_talk
            else ""
        )
        + (
            f'- ⚠️ **Session with Lowest Ratings:** "{worst_talk["topic"]}" at {worst_talk["event_name"]} (`{worst_talk["average_rating"]}/10`).\n'
            if worst_talk and worst_talk != best_talk
            else ""
        )
        + f"\n#### 3 Actionable Tips for Your Next Talk:\n"
        f"1. **Elevate Your {top_growth}:** Add structured pause checkpoints or practical live takeaways to raise audience perception in this dimension.\n"
        f"2. **Double Down on {top_strength}:** Keep what works! Your audience clearly responds well to this part of your delivery.\n"
        f"3. **Incorporate Interactive Feedback Moments:** Remind attendees to scan your SpeakWise QR code right before concluding your slides for higher feedback completion rates.\n\n"
        + (f'> *Attendee Highlight:* "{all_comments[0]}"\n' if all_comments else "")
    )


def ask_speakbot(
    speaker: SpeakerProfile,
    query: str,
    experience_id: Optional[str] = None,
    history: Optional[List[Dict[str, str]]] = None,
) -> Dict[str, Any]:
    """Unified entry point to consult SpeakBot AI."""
    # 1. Compile speaker data
    data = build_speaker_feedback_data(speaker, experience_id=experience_id)
    context_md = format_feedback_context_prompt(data)
    system_prompt = get_system_prompt(context_md)

    clean_query = (
        query.strip()
        or "Give me a complete coaching breakdown of my speaking performance and areas to improve."
    )

    # 2. Try Gemini (Primary)
    reply, model_used = _call_gemini_api(system_prompt, clean_query, history)
    provider = "gemini"

    # 3. Try Groq (Fallback)
    if not reply:
        reply, model_used = _call_groq_api(system_prompt, clean_query, history)
        provider = "groq"

    # 4. Fallback to analytical calculation if neither key is active
    if not reply:
        reply = _generate_analytical_fallback(data, clean_query)
        provider = "analytics_fallback"
        model_used = "speakbot-rule-engine"

    return {
        "reply": reply,
        "provider": provider,
        "model": model_used,
        "summary": {
            "total_feedbacks": data["total_feedbacks"],
            "talks_analyzed": data["talks_count"],
            "avg_rating": data["overall_avg"],
            "top_strength": data["top_strength"],
            "top_growth_area": data["top_growth_area"],
        },
    }
