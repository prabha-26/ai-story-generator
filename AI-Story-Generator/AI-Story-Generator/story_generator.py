"""
story_generator.py
==================
Core backend module for the AI Story Generator.
Handles Gemini API client initialization, prompt engineering, narrative structuring,
and robust error handling.
"""

import os
import re
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

LENGTH_OPTIONS = {
    "Short (200–300 words)": {
        "min_words": 200,
        "max_words": 300,
        "target_desc": "200 to 300 words (compact, fast-paced, high impact)",
    },
    "Medium (500–700 words)": {
        "min_words": 500,
        "max_words": 700,
        "target_desc": "500 to 700 words (well-developed characters, solid pacing)",
    },
    "Long (1000–1200 words)": {
        "min_words": 1000,
        "max_words": 1200,
        "target_desc": "1000 to 1200 words (rich atmosphere, immersive plot, detailed climax)",
    },
}

# Default model fallback order
DEFAULT_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

# Known placeholder values to ignore
DUMMY_KEYS = {
    "your_gemini_api_key_here",
    "your_actual_key_here",
    "your_api_key_here",
    "your_actual_gemini_api_key",
}


def get_api_key(override_key: Optional[str] = None) -> Optional[str]:
    """
    Retrieve Gemini API key with priority:
    1. Direct override parameter (e.g. from user input in sidebar)
    2. Streamlit secrets (st.secrets) for cloud deployments (Streamlit Cloud, HF Spaces)
    3. OS environment variable (os.environ / .env via python-dotenv)
    """
    if override_key and override_key.strip():
        key = override_key.strip()
        if key not in DUMMY_KEYS:
            return key

    # Check Streamlit Cloud secrets if available
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
    """
    Validate story input parameters before sending to LLM.
    Returns (is_valid, error_message).
    """
    if not topic or not topic.strip():
        return False, "Story topic/idea cannot be empty. Please provide a brief premise."
    if len(topic.strip()) < 5:
        return False, "Story topic is too short. Please provide at least a few descriptive words."
    if genre not in GENRES:
        return False, f"Invalid genre '{genre}'. Must be one of: {', '.join(GENRES)}"
    if mood not in MOODS:
        return False, f"Invalid mood '{mood}'. Must be one of: {', '.join(MOODS)}"
    if audience not in AUDIENCES:
        return False, f"Invalid audience '{audience}'. Must be one of: {', '.join(AUDIENCES)}"
    if length_choice not in LENGTH_OPTIONS:
        return False, "Invalid story length selection."
    return True, None


def build_system_prompt() -> str:
    """
    Construct the professional fiction writer system prompt.
    """
    return (
        "You are an acclaimed, master fiction author and master narrative designer. "
        "Your craft combines immersive sensory world-building, compelling character dynamics, "
        "and seamless narrative pacing.\n\n"
        "STORYTELLING PRINCIPLES:\n"
        "1. Structure: Build the story across 5 distinct narrative phases:\n"
        "   - I. Introduction (The Hook & World): Introduce the protagonist, setting, and initial status quo.\n"
        "   - II. Character Development: Reveal internal/external stakes, distinct personalities, and core motives.\n"
        "   - III. Conflict (The Inciting Incident & Obstacles): Introduce escalating friction and tension.\n"
        "   - IV. Climax: Deliver the dramatic peak, critical decision, or pivotal turning point.\n"
        "   - V. Resolution: Provide a satisfying, earned conclusion with lingering emotional resonance.\n"
        "2. Style & Tone: Strictly respect the selected Genre, Mood, and Target Audience guidelines.\n"
        "   - Children: Age-appropriate vocabulary, vivid imagination, warmth, zero inappropriate content.\n"
        "   - Teenagers: Relatable angst/ambition, energetic pacing, vivid dialogue, personal identity stakes.\n"
        "   - Adults: Nuanced themes, psychological depth, atmospheric subtext, layered relationships.\n"
        "3. Length Constraint: You MUST strictly honor the target word count bounds. Avoid repetitive fluff or abrupt endings.\n"
        "4. Output Format: Start directly with a captivating Title formatted as `# Title: <Your Title>`, followed by the story text."
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
    """
    Construct the dynamic user prompt with all inputs and story parameters.
    """
    length_info = LENGTH_OPTIONS.get(length_choice, LENGTH_OPTIONS["Medium (500–700 words)"])
    chars = characters.strip() if characters and characters.strip() else "Create memorable characters fitting the plot"
    loc = setting.strip() if setting and setting.strip() else "An evocative setting tailored to the story's theme"
    title_instruction = (
        f"Use this specific title: '{title.strip()}'."
        if title and title.strip()
        else "Create a creative, evocative title that fits the story."
    )

    prompt = f"""Write an original, highly engaging story based on the following specifications:

- **Topic / Premise:** {topic.strip()}
- **Title Instruction:** {title_instruction}
- **Genre:** {genre}
- **Mood / Atmosphere:** {mood}
- **Target Audience:** {audience}
- **Main Characters:** {chars}
- **Setting / Location:** {loc}
- **Length Constraint:** Exactly {length_info['target_desc']} (Target: {length_info['min_words']} - {length_info['max_words']} words).

Guidelines:
1. Ensure a clear five-part arc: Introduction -> Character Development -> Conflict -> Climax -> Resolution.
2. Use dialogue to show personality rather than just telling.
3. Keep the language natural, immersive, and grammatically impeccable.
4. Begin your response with:
   # Title: <Story Title>
   (followed by the narrative without markdown meta-announcements).
"""
    return prompt


def _parse_story_response(raw_text: str, user_title: Optional[str] = None) -> Tuple[str, str]:
    """
    Extract the title and story body from the raw LLM response.
    """
    text = raw_text.strip()
    extracted_title = ""

    # Look for '# Title: ...' or '# ...' at the very beginning
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

    # Clean up double title tags if LLM repeated it
    text = re.sub(r"^(?:Title:\s*|#+\s*)[^\n]+\n+", "", text, flags=re.IGNORECASE).strip()

    return extracted_title, text


def generate_story_with_google_genai(
    api_key: str,
    system_prompt: str,
    user_prompt: str,
    model_name: str,
) -> str:
    """
    Invoke Gemini using the modern `google-genai` SDK (`from google import genai`).
    """
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=api_key)
    clean_model = model_name.replace("models/", "")

    config = types.GenerateContentConfig(
        system_instruction=system_prompt,
        temperature=0.85,
        top_p=0.95,
    )

    response = client.models.generate_content(
        model=clean_model,
        contents=user_prompt,
        config=config,
    )

    if not response or not response.text:
        raise ValueError("Gemini API returned an empty response. Please try again.")

    return response.text


def generate_story_with_legacy_genai(
    api_key: str,
    system_prompt: str,
    user_prompt: str,
    model_name: str,
) -> str:
    """
    Fallback invocation using `google.generativeai` SDK.
    """
    import google.generativeai as genai

    genai.configure(api_key=api_key)

    model = genai.GenerativeModel(
        model_name=model_name,
        system_instruction=system_prompt,
        generation_config={
            "temperature": 0.85,
            "top_p": 0.95,
        },
    )

    response = model.generate_content(user_prompt)
    if not response or not response.text:
        raise ValueError("Gemini API returned an empty response. Please try again.")

    return response.text


def _get_dynamic_model_candidates(api_key: str, preferred_model: str) -> list:
    """
    Query Gemini API for accessible models for this API key,
    or build a prioritized candidate fallback list.
    """
    candidates = [preferred_model]
    for m in [
        "gemini-1.5-flash",
        "gemini-1.5-flash-latest",
        "models/gemini-1.5-flash",
        "gemini-2.0-flash",
        "gemini-1.5-pro",
        "models/gemini-pro",
        "gemini-pro",
    ]:
        if m not in candidates:
            candidates.append(m)

    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        online_models = [
            m.name for m in genai.list_models()
            if "generateContent" in getattr(m, "supported_generation_methods", [])
        ]
        if online_models:
            for om in reversed(online_models):
                clean_name = om.replace("models/", "")
                if clean_name not in candidates:
                    candidates.insert(0, clean_name)
                if om not in candidates:
                    candidates.insert(0, om)
    except Exception:
        pass

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
    """
    Main entry point for generating a story.
    Returns a structured dictionary with success status, story text, metrics, and metadata.
    """
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
                "file or enter it in the sidebar settings."
            ),
            "story": "",
            "title": "",
            "word_count": 0,
            "reading_time_min": 0,
            "metadata": {},
        }

    # 3. Model selection & candidate fallback list
    chosen_model = model_name or DEFAULT_MODEL
    model_candidates = _get_dynamic_model_candidates(active_key, chosen_model)

    # 4. Prompt assembly
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

    # 5. Call Gemini API trying candidate models
    raw_response_text = ""
    sdk_used = "unknown"
    successful_model = chosen_model
    last_exception = None

    def _call_gemini_single(model_to_use: str) -> Tuple[str, str]:
        try:
            return generate_story_with_google_genai(
                api_key=active_key,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                model_name=model_to_use,
            ), "google-genai"
        except (ImportError, ModuleNotFoundError):
            return generate_story_with_legacy_genai(
                api_key=active_key,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                model_name=model_to_use,
            ), "google-generativeai"

    # Iterate through model candidates until one succeeds
    for candidate in model_candidates:
        try:
            raw_response_text, sdk_used = _call_gemini_single(candidate)
            successful_model = candidate
            last_exception = None
            break
        except Exception as exc:
            last_exception = exc
            err_str = str(exc)
            if "API_KEY_INVALID" in err_str or "PERMISSION_DENIED" in err_str or "429" in err_str:
                break
            continue

    if last_exception is not None and not raw_response_text:
        exc_str = str(last_exception)
        if "API_KEY_INVALID" in exc_str or ("400" in exc_str and "key" in exc_str.lower()):
            error_msg = "Invalid Gemini API Key. Please verify your key at https://aistudio.google.com/app/apikey"
        elif "RESOURCE_EXHAUSTED" in exc_str or "429" in exc_str:
            error_msg = "Gemini API rate limit exceeded or quota exhausted. Please wait 60 seconds and try again."
        elif "PERMISSION_DENIED" in exc_str:
            error_msg = "Permission denied. Ensure the Generative Language API is enabled for this key."
        elif "MODEL_NOT_FOUND" in exc_str or "404" in exc_str or "not found" in exc_str.lower():
            error_msg = (
                "Your Gemini API key could not access the model. This happens if the key was created in Google Cloud "
                "without 'Generative Language API' enabled. Please create a free key directly at: "
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

    # 6. Parse response
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
