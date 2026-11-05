"""
story_generator.py
==================
Core backend module for the AI Story Generator.
Token-optimized with strict output limits, multi-SDK fallback, and robust error handling.
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
    """Retrieve Gemini API key with priority: override, Streamlit secrets, or .env."""
    if override_key and override_key.strip():
        key = override_key.strip()
        if key not in DUMMY_KEYS:
            return key

    try:
        import streamlit as st
        if hasattr(st, "secrets") and "GEMINI_API_KEY" in st.secrets:
            secret_val = str(st.secrets["GEMINI_API_KEY"]).strip()
            if secret_val and secret_val not in DUMMY_KEYS:
                return secret_val
    except Exception:
        pass

    env_val = os.getenv("GEMINI_API_KEY", "").strip()
    if env_val and env_val not in DUMMY_KEYS:
        return env_val

    return None


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


def generate_story_with_legacy_genai(
    api_key: str,
    system_prompt: str,
    user_prompt: str,
    model_name: str,
    max_output_tokens: int = 950,
) -> str:
    """Primary invocation using the standard google.generativeai SDK."""
    import google.generativeai as genai

    genai.configure(api_key=api_key)
    clean_model = model_name.replace("models/", "")

    model = genai.GenerativeModel(
        model_name=clean_model,
        system_instruction=system_prompt,
        generation_config={
            "temperature": 0.85,
            "top_p": 0.95,
            "max_output_tokens": max_output_tokens,
        },
    )

    response = model.generate_content(user_prompt)

    if hasattr(response, "text") and response.text:
        return response.text

    if hasattr(response, "candidates") and response.candidates:
        first_cand = response.candidates[0]
        if hasattr(first_cand, "content") and hasattr(first_cand.content, "parts"):
            parts = [p.text for p in first_cand.content.parts if hasattr(p, "text") and p.text]
            if parts:
                return "\n".join(parts)

    raise ValueError("Gemini API returned an empty response. Please try again.")


def generate_story_with_google_genai(
    api_key: str,
    system_prompt: str,
    user_prompt: str,
    model_name: str,
    max_output_tokens: int = 950,
) -> str:
    """Secondary invocation using modern google-genai SDK."""
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=api_key)
    clean_model = model_name.replace("models/", "")

    config = types.GenerateContentConfig(
        system_instruction=system_prompt,
        temperature=0.85,
        top_p=0.95,
        max_output_tokens=max_output_tokens,
    )

    response = client.models.generate_content(
        model=clean_model,
        contents=user_prompt,
        config=config,
    )

    if not response or not response.text:
        raise ValueError("Gemini API returned an empty response. Please try again.")

    return response.text


def _get_dynamic_model_candidates(preferred_model: str) -> list:
    """Build a clean, token-efficient model fallback list."""
    candidates = [preferred_model]
    for m in ["gemini-1.5-flash", "gemini-1.5-flash-8b", "gemini-2.0-flash", "gemini-pro"]:
        if m not in candidates:
            candidates.append(m)
    return candidates


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
    """Main entry point for generating a story with token controls."""
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

    chosen_model = model_name or DEFAULT_MODEL
    model_candidates = _get_dynamic_model_candidates(chosen_model)

    length_info = LENGTH_OPTIONS.get(length_choice, LENGTH_OPTIONS["Medium (500–700 words)"])
    max_tokens_budget = length_info.get("max_tokens", 950)

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

    raw_response_text = ""
    sdk_used = "unknown"
    successful_model = chosen_model
    last_exception = None

    def _call_gemini_single(model_to_use: str) -> Tuple[str, str]:
        try:
            return generate_story_with_legacy_genai(
                api_key=active_key,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                model_name=model_to_use,
                max_output_tokens=max_tokens_budget,
            ), "google.generativeai"
        except Exception as e_legacy:
            try:
                return generate_story_with_google_genai(
                    api_key=active_key,
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    model_name=model_to_use,
                    max_output_tokens=max_tokens_budget,
                ), "google-genai"
            except Exception:
                raise e_legacy

    for candidate in model_candidates:
        for attempt in range(2):
            try:
                raw_response_text, sdk_used = _call_gemini_single(candidate)
                successful_model = candidate
                last_exception = None
                break
            except Exception as exc:
                last_exception = exc
                err_str = str(exc)
                if ("429" in err_str or "RESOURCE_EXHAUSTED" in err_str) and attempt == 0:
                    time.sleep(2)
                    continue
                if "API_KEY_INVALID" in err_str or "PERMISSION_DENIED" in err_str:
                    break
                break

        if raw_response_text:
            break

    if last_exception is not None and not raw_response_text:
        exc_str = str(last_exception)
        if "API_KEY_INVALID" in exc_str or ("400" in exc_str and "key" in exc_str.lower()):
            error_msg = "Invalid Gemini API Key. Please verify your key at https://aistudio.google.com/app/apikey"
        elif "RESOURCE_EXHAUSTED" in exc_str or "429" in exc_str:
            error_msg = (
                f"Google Gemini Quota Exhausted / Rate Limit: {exc_str}\n\n"
                "👉 How to fix:\n"
                "1. If this key was made in Google Cloud Console, free quota is set to 0. Create a free key directly at: https://aistudio.google.com/app/apikey\n"
                "2. Try selecting 'gemini-1.5-flash-8b' or 'gemini-2.0-flash' in the Sidebar model dropdown.\n"
                "3. Or paste a fresh key into Sidebar > ⚙️ API Configuration."
            )
        elif "PERMISSION_DENIED" in exc_str:
            error_msg = "Permission denied. Ensure the Generative Language API is enabled for this key."
        elif "MODEL_NOT_FOUND" in exc_str or "404" in exc_str or "not found" in exc_str.lower():
            error_msg = (
                "Your Gemini API key could not access the model. Create a free key directly at: "
                "https://aistudio.google.com/app/apikey and paste it into the Sidebar."
            )
        else:
            error_msg = f"Story generation error: {exc_str}"

        return {
            "success": False,
            "error": error_msg,
            "story": "",
            "title": "",
            "word_count": 0,
            "reading_time_min": 0,
            "metadata": {},
        }

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
            "model": successful_model,
            "sdk": sdk_used,
        },
    }
