"""
story_generator.py
==================
Core backend module for the AI Story Generator.
Token-optimized with strict output limits, clean model targeting,
and transparent error reporting.
"""

import os
import re
import time
from typing import Dict, Any, Optional, Tuple
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Valid configuration options
GENRES = [
    "Fantasy",
    "Science Fiction",
    "Horror",
    "Mystery",
    "Romance",
    "Adventure",
    "Comedy",
    "Thriller",
]

MOODS = [
    "Emotional",
    "Suspenseful",
    "Inspirational",
    "Funny",
    "Dark",
    "Mysterious",
]

AUDIENCES = [
    "Children",
    "Teenagers",
    "Adults",
]

# Token budgets calibrated for story lengths (saving up to 80% output tokens)
LENGTH_OPTIONS = {
    "Short (200–300 words)": {
        "min_words": 200,
        "max_words": 300,
        "max_tokens": 550,
        "target_desc": "200–300 words",
    },
    "Medium (500–700 words)": {
        "min_words": 500,
        "max_words": 700,
        "max_tokens": 950,
        "target_desc": "500–700 words",
    },
    "Long (1000–1200 words)": {
        "min_words": 1000,
        "max_words": 1200,
        "max_tokens": 1600,
        "target_desc": "1000–1200 words",
    },
}

# Default model fallback
DEFAULT_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

# Known placeholder values to ignore
DUMMY_KEYS = {
    "your_gemini_api_key_here",
    "your_actual_key_here",
    "your_api_key_here",
    "your_actual_gemini_api_key",
}


def get_api_key(override_key: Optional[str] = None) -> Optional[str]:
    """Retrieve Gemini API key and strip accidental quotes and whitespace."""
    def _clean(val):
        if val is None:
            return None
        v = str(val).strip().strip("'\"").strip()
        return v if v and v not in DUMMY_KEYS else None

    # 1. Override from UI input
    ui_key = _clean(override_key)
    if ui_key:
        return ui_key

    # 2. Streamlit Cloud secrets
    try:
        import streamlit as st
        if hasattr(st, "secrets") and "GEMINI_API_KEY" in st.secrets:
            sec = _clean(st.secrets["GEMINI_API_KEY"])
            if sec:
                return sec
    except Exception:
        pass

    # 3. Environment variable (.env)
    return _clean(os.getenv("GEMINI_API_KEY"))


def validate_inputs(
    topic: str,
    genre: str,
    mood: str,
    audience: str,
    length_choice: str,
) -> Tuple[bool, Optional[str]]:
    """Validate story input parameters before sending to LLM."""
    if not topic or not topic.strip():
        return False, "Story topic cannot be empty. Please provide a brief premise."
    if len(topic.strip()) < 5:
        return False, "Story topic is too short. Please provide at least a few words."
    if genre not in GENRES:
        return False, f"Invalid genre '{genre}'."
    if mood not in MOODS:
        return False, f"Invalid mood '{mood}'."
    if audience not in AUDIENCES:
        return False, f"Invalid audience '{audience}'."
    if length_choice not in LENGTH_OPTIONS:
        return False, "Invalid story length selection."
    return True, None


def build_system_prompt() -> str:
    """Concise, token-optimized system instruction."""
    return (
        "You are an acclaimed fiction writer. Write engaging, original stories structured in 5 phases: "
        "Hook/Intro, Character motivations, Conflict, Climax, and Resolution. "
        "Strictly honor the selected Genre, Mood, Audience, and Word Count. "
        "Start directly with: # Title: <Your Title>, followed immediately by the narrative."
    )


def build_user_prompt(
    topic: str,
    genre: str,
    characters: str,
    setting: str,
    mood: str,
    audience: str,
    length_choice: str,
    title: Optional[str] = None,
) -> str:
    """Concise, token-optimized user prompt."""
    length_info = LENGTH_OPTIONS.get(length_choice, LENGTH_OPTIONS["Medium (500–700 words)"])
    chars = characters.strip() if characters and characters.strip() else "Compelling characters"
    loc = setting.strip() if setting and setting.strip() else "Immersive setting"
    title_instruction = f"Title must be '{title.strip()}'." if title and title.strip() else "Invent a creative title."

    return (
        f"Topic: {topic.strip()}\n"
        f"Genre: {genre} | Mood: {mood} | Audience: {audience}\n"
        f"Characters: {chars} | Setting: {loc}\n"
        f"Target Length: {length_info['target_desc']} (max {length_info['max_words']} words).\n"
        f"{title_instruction}\n\n"
        "Write the story now without introductory commentary."
    )


def _parse_story_response(raw_text: str, user_title: Optional[str] = None) -> Tuple[str, str]:
    """Extract clean title and narrative body with fallback safeguards."""
    text = raw_text.strip()
    extracted_title = ""

    title_match = re.search(r"^(?:#+\s*(?:Title:\s*)?|\*\*Title:\s*\*\*\s*)([^\n]+)", text, re.IGNORECASE)
    if title_match:
        extracted_title = title_match.group(1).strip().strip('"*#')
        text = text[title_match.end():].strip()
    elif user_title and user_title.strip():
        extracted_title = user_title.strip()
    else:
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        if lines and len(lines[0]) < 80 and not lines[0].endswith("."):
            extracted_title = lines[0].strip("#* ")
            text = "\n\n".join(lines[1:]).strip()
        else:
            extracted_title = "Untitled Masterpiece"

    text = re.sub(r"^(?:Title:\s*|#+\s*)[^\n]+\n+", "", text, flags=re.IGNORECASE).strip()

    if not text:
        text = raw_text.strip()

    return extracted_title or "Untitled Masterpiece", text


def _invoke_gemini_api(
    api_key: str,
    model_name: str,
    system_prompt: str,
    user_prompt: str,
    max_tokens: int,
) -> Tuple[str, str]:
    """
    Direct invocation of Gemini API with SDK fallback.
    """
    clean_model = model_name.replace("models/", "")
    full_prompt = f"{system_prompt}\n\n---\n\n{user_prompt}"

    # Engine 1: google-genai (new official SDK)
    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=api_key)
        config = types.GenerateContentConfig(
            temperature=0.85,
            top_p=0.95,
            max_output_tokens=max_tokens,
        )
        res = client.models.generate_content(
            model=clean_model,
            contents=full_prompt,
            config=config,
        )
        if hasattr(res, "text") and res.text:
            return res.text, "google-genai"
    except Exception as e_genai:
        # Engine 2: google.generativeai (fallback)
        try:
            import google.generativeai as legacy_genai
            legacy_genai.configure(api_key=api_key)
            model = legacy_genai.GenerativeModel(clean_model)
            res = model.generate_content(
                full_prompt,
                generation_config={
                    "temperature": 0.85,
                    "top_p": 0.95,
                    "max_output_tokens": max_tokens,
                },
            )
            if hasattr(res, "text") and res.text:
                return res.text, "google.generativeai"

            if hasattr(res, "candidates") and res.candidates:
                cand = res.candidates[0]
                if hasattr(cand, "content") and hasattr(cand.content, "parts"):
                    parts = [p.text for p in cand.content.parts if hasattr(p, "text") and p.text]
                    if parts:
                        return "\n".join(parts), "google.generativeai"
        except Exception:
            raise e_genai

        raise e_genai

    raise RuntimeError("Empty response received from Gemini API.")


def generate_story(
    topic: str,
    genre: str,
    characters: str,
    setting: str,
    mood: str,
    audience: str,
    length_choice: str,
    title: Optional[str] = None,
    api_key: Optional[str] = None,
    model_name: Optional[str] = None,
) -> Dict[str, Any]:
    """Main entry point for generating a story."""
    # 1. Validate inputs
    is_valid, validation_err = validate_inputs(topic, genre, mood, audience, length_choice)
    if not is_valid:
        return {
            "success": False,
            "error": validation_err,
            "story": "",
            "title": "",
            "word_count": 0,
            "reading_time_min": 0,
            "metadata": {},
        }

    # 2. Validate API key
    active_key = get_api_key(api_key)
    if not active_key:
        return {
            "success": False,
            "error": (
                "Gemini API Key is missing. Please set `GEMINI_API_KEY` in your `.env` "
                "or enter it in the sidebar settings."
            ),
            "story": "",
            "title": "",
            "word_count": 0,
            "reading_time_min": 0,
            "metadata": {},
        }

    # 3. Model selection
    target_model = model_name or DEFAULT_MODEL

    # 4. Token limit calculation
    length_info = LENGTH_OPTIONS.get(length_choice, LENGTH_OPTIONS["Medium (500–700 words)"])
    max_tokens_budget = length_info.get("max_tokens", 950)

    # 5. Prompt assembly
    system_prompt = build_system_prompt()
    user_prompt = build_user_prompt(
        topic=topic,
        genre=genre,
        characters=characters,
        setting=setting,
        mood=mood,
        audience=audience,
        length_choice=length_choice,
        title=title,
    )

    # 6. Execute Generation
    raw_response_text = ""
    sdk_used = "unknown"
    error_details = ""

    # Attempt the target model
    try:
        raw_response_text, sdk_used = _invoke_gemini_api(
            api_key=active_key,
            model_name=target_model,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=max_tokens_budget,
        )
    except Exception as exc:
        error_details = str(exc)
        # If rate limited (429), try one quick retry with backoff
        if "429" in error_details or "RESOURCE_EXHAUSTED" in error_details:
            time.sleep(3)
            try:
                raw_response_text, sdk_used = _invoke_gemini_api(
                    api_key=active_key,
                    model_name=target_model,
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    max_tokens=max_tokens_budget,
                )
                error_details = ""
            except Exception as retry_exc:
                error_details = str(retry_exc)

    if not raw_response_text:
        return {
            "success": False,
            "error": f"Gemini Error on '{target_model}': {error_details}",
            "story": "",
            "title": "",
            "word_count": 0,
            "reading_time_min": 0,
            "metadata": {},
        }

    # 7. Parse response
    final_title, story_body = _parse_story_response(raw_response_text, user_title=title)
    words = story_body.split()
    word_count = len(words)
    reading_time_min = max(1, round(word_count / 225))

    return {
        "success": True,
        "error": None,
        "title": final_title,
        "story": story_body,
        "word_count": word_count,
        "reading_time_min": reading_time_min,
        "metadata": {
            "genre": genre,
            "mood": mood,
            "audience": audience,
            "length_choice": length_choice,
            "characters": characters.strip() if characters else "N/A",
            "setting": setting.strip() if setting else "N/A",
            "model": target_model,
            "sdk": sdk_used,
        },
    }
