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
DEFAULT_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")


def get_api_key(override_key: Optional[str] = None) -> Optional[str]:
    """
    Retrieve Gemini API key from explicit parameter or environment variables.
    """
    if override_key and override_key.strip():
        return override_key.strip()
    return os.getenv("GEMINI_API_KEY", "").strip() or None


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
        # Remove the matched title line from the story body
        text = text[title_match.end():].strip()
    elif user_title and user_title.strip():
        extracted_title = user_title.strip()
    else:
        # Fallback to first line if short enough
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

    # Use client.models.generate_content
    config = types.GenerateContentConfig(
        system_instruction=system_prompt,
        temperature=0.85,
        top_p=0.95,
    )

    response = client.models.generate_content(
        model=model_name,
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

    # 3. Model selection
    active_model = model_name or DEFAULT_MODEL

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

    # 5. Call Gemini API with SDK detection (prefer modern google-genai)
    raw_response_text = ""
    sdk_used = "unknown"
    error_msg = None

    try:
        try:
            # Attempt modern Google GenAI SDK first
            raw_response_text = generate_story_with_google_genai(
                api_key=active_key,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                model_name=active_model,
            )
            sdk_used = "google-genai"
        except (ImportError, ModuleNotFoundError):
            # Fall back to legacy google-generativeai
            raw_response_text = generate_story_with_legacy_genai(
                api_key=active_key,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                model_name=active_model,
            )
            sdk_used = "google-generativeai"

    except Exception as exc:
        exc_str = str(exc)
        # Handle specific common failure cases cleanly
        if "API_KEY_INVALID" in exc_str or "400" in exc_str and "key" in exc_str.lower():
            error_msg = "Invalid Gemini API Key. Please verify your API key at https://aistudio.google.com/app/apikey"
        elif "RESOURCE_EXHAUSTED" in exc_str or "429" in exc_str:
            error_msg = "Gemini API rate limit exceeded or quota exhausted. Please wait a minute and try again."
        elif "PERMISSION_DENIED" in exc_str:
            error_msg = "Permission denied. Check that the Gemini API is enabled for your project/key."
        elif "MODEL_NOT_FOUND" in exc_str or "404" in exc_str:
            error_msg = f"The model '{active_model}' was not found or is not supported by your API tier. Try switching to 'gemini-1.5-flash' in .env."
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
    # Average adult reading speed: ~200-250 wpm
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
            "model": active_model,
            "sdk": sdk_used,
        },
    }
