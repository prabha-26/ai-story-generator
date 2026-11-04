"""
app.py
======
Streamlit web application for the AI Story Generator.
Features a modern dark-themed UI, dynamic prompt controls, dedicated reading card,
and export options.
"""

import streamlit as st
from story_generator import (
    GENRES,
    MOODS,
    AUDIENCES,
    LENGTH_OPTIONS,
    DEFAULT_MODEL,
    generate_story,
    get_api_key,
)

# -----------------------------------------------------------------------------
# 1. Page Configuration & Custom CSS Styling (Dark Theme & Gradients)
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="AI Story Generator",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded",
)

CUSTOM_CSS = """
<style>
/* Modern Dark Theme Theme Overrides */
:root {
    --bg-primary: #0e1117;
    --bg-secondary: #161b22;
    --card-bg: rgba(22, 27, 34, 0.85);
    --accent-gradient: linear-gradient(135deg, #FF6B6B 0%, #A060FF 50%, #4FACFE 100%);
    --accent-glow: 0 8px 32px 0 rgba(160, 96, 255, 0.25);
    --border-subtle: rgba(255, 255, 255, 0.1);
    --text-primary: #F0F6FC;
    --text-secondary: #8B949E;
}

/* Overall page background */
.stApp {
    background: radial-gradient(circle at 15% 15%, #181926 0%, #0e1117 100%);
    color: var(--text-primary);
}

/* Gradient Titles */
.gradient-title {
    font-size: 2.6rem;
    font-weight: 800;
    background: linear-gradient(135deg, #FF758C 0%, #FF7EB3 25%, #7976FF 65%, #00D4FF 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 0.25rem;
    letter-spacing: -0.5px;
}

.gradient-subtitle {
    color: var(--text-secondary);
    font-size: 1.05rem;
    margin-bottom: 1.5rem;
}

/* Custom styled badge pill */
.badge-container {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin: 12px 0 20px 0;
}

.badge {
    background: rgba(255, 255, 255, 0.06);
    border: 1px solid rgba(255, 255, 255, 0.12);
    color: #E6EDF3;
    padding: 5px 12px;
    border-radius: 999px;
    font-size: 0.82rem;
    font-weight: 600;
    letter-spacing: 0.3px;
    display: inline-flex;
    align-items: center;
    gap: 6px;
    backdrop-filter: blur(8px);
}

.badge-highlight {
    background: linear-gradient(135deg, rgba(160, 96, 255, 0.2) 0%, rgba(79, 172, 254, 0.2) 100%);
    border-color: rgba(160, 96, 255, 0.4);
    color: #c9d8ff;
}

/* Story Reading Card */
.story-container {
    background: var(--card-bg);
    border: 1px solid var(--border-subtle);
    border-radius: 16px;
    padding: 2.2rem 2.5rem;
    margin-top: 1rem;
    box-shadow: 0 12px 40px rgba(0, 0, 0, 0.45);
    backdrop-filter: blur(14px);
    line-height: 1.85;
    font-size: 1.12rem;
    color: #E6EDF3;
    font-family: 'Georgia', 'Cambria', serif;
}

.story-title {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    font-size: 2rem;
    font-weight: 700;
    color: #FFFFFF;
    margin-bottom: 0.75rem;
    border-bottom: 2px solid rgba(255, 255, 255, 0.08);
    padding-bottom: 0.6rem;
}

/* Feature cards for landing page */
.feature-card {
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 12px;
    padding: 1.25rem;
    margin-bottom: 1rem;
    transition: transform 0.2s ease, border-color 0.2s ease;
}
.feature-card:hover {
    border-color: rgba(160, 96, 255, 0.4);
    transform: translateY(-2px);
}
.feature-title {
    font-weight: 600;
    font-size: 1rem;
    color: #9ECBFF;
    margin-bottom: 0.4rem;
}
.feature-desc {
    font-size: 0.88rem;
    color: #8B949E;
}

/* Footer styling */
.footer-container {
    margin-top: 3.5rem;
    padding-top: 1.5rem;
    border-top: 1px solid rgba(255, 255, 255, 0.08);
    text-align: center;
    color: #6E7681;
    font-size: 0.85rem;
}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# 2. Session State Initialization & Callbacks
# -----------------------------------------------------------------------------
def init_session_state():
    """Initialize persistent session variables."""
    if "story_data" not in st.session_state:
        st.session_state.story_data = None
    if "api_error" not in st.session_state:
        st.session_state.api_error = None

    default_values = {
        "title_input": "",
        "topic_input": "",
        "genre_input": GENRES[0],
        "mood_input": MOODS[0],
        "audience_input": AUDIENCES[1],
        "characters_input": "",
        "setting_input": "",
        "length_input": "Medium (500–700 words)",
        "sidebar_api_key": "",
    }
    for key, val in default_values.items():
        if key not in st.session_state:
            st.session_state[key] = val


init_session_state()


def clear_inputs():
    """Reset all input fields in session state."""
    st.session_state.title_input = ""
    st.session_state.topic_input = ""
    st.session_state.genre_input = GENRES[0]
    st.session_state.mood_input = MOODS[0]
    st.session_state.audience_input = AUDIENCES[1]
    st.session_state.characters_input = ""
    st.session_state.setting_input = ""
    st.session_state.length_input = "Medium (500–700 words)"
    st.session_state.story_data = None
    st.session_state.api_error = None


def load_scifi_prompt():
    """Preload Sci-Fi prompt via on_click callback before widgets instantiate."""
    st.session_state.title_input = "The Dyson Singularity"
    st.session_state.topic_input = "A solitary maintenance engineer on a solar-harvesting Dyson ring discovers an anomalous encrypted audio broadcast coming from inside the core."
    st.session_state.genre_input = "Science Fiction"
    st.session_state.mood_input = "Suspenseful"
    st.session_state.audience_input = "Adults"
    st.session_state.characters_input = "Soren Vance (Chief Systems Engineer)"
    st.session_state.setting_input = "Perimeter Station Aegis, orbit of Kepler-452"
    st.session_state.length_input = "Medium (500–700 words)"


def load_fantasy_prompt():
    """Preload Fantasy prompt via on_click callback before widgets instantiate."""
    st.session_state.title_input = "The Whispering Library"
    st.session_state.topic_input = "An apprentice librarian finds a forbidden book whose pages rewrite themselves based on secrets murmured in the town square."
    st.session_state.genre_input = "Fantasy"
    st.session_state.mood_input = "Mysterious"
    st.session_state.audience_input = "Teenagers"
    st.session_state.characters_input = "Rowan (inquisitive apprentice), Master Bram"
    st.session_state.setting_input = "The Grand Archives of Oakhaven"
    st.session_state.length_input = "Medium (500–700 words)"


# -----------------------------------------------------------------------------
# 3. Sidebar: Story Generation Form & Settings
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### ✍️ Story Configuration")
    st.caption("Craft your custom parameters below to generate an original story.")

    # A. Topic and Title
    st.markdown("##### 📌 Story Concept")
    user_topic = st.text_area(
        label="Story Topic or Premise *",
        key="topic_input",
        placeholder="e.g., A clockmaker discovers an ancient pocket watch that can rewind time by sixty seconds...",
        height=100,
        help="Required. Describe what the story is about or the central hook.",
    )

    user_title = st.text_input(
        label="Story Title (Optional)",
        key="title_input",
        placeholder="Leave blank for an AI-generated title",
        help="Optional. Specify a title or let the AI invent one.",
    )

    # B. Genre & Tone
    st.markdown("##### 🎭 Style & Mood")
    col_g, col_m = st.columns(2)
    with col_g:
        user_genre = st.selectbox(
            label="Genre",
            options=GENRES,
            key="genre_input",
            help="Select the narrative genre.",
        )
    with col_m:
        user_mood = st.selectbox(
            label="Mood",
            options=MOODS,
            key="mood_input",
            help="Emotional atmosphere of the tale.",
        )

    # C. Audience & Characters
    col_a, col_l = st.columns(2)
    with col_a:
        user_audience = st.selectbox(
            label="Target Audience",
            options=AUDIENCES,
            key="audience_input",
            help="Tailors vocabulary, theme depth, and complexity.",
        )
    with col_l:
        user_length = st.selectbox(
            label="Story Length",
            options=list(LENGTH_OPTIONS.keys()),
            key="length_input",
            help="Desired word count range.",
        )

    # D. Characters & World
    st.markdown("##### 👥 Characters & Setting")
    user_characters = st.text_input(
        label="Main Character(s)",
        key="characters_input",
        placeholder="e.g., Elian (a cynical rogue), Lyra (an apprentice mage)",
        help="Names and short descriptions of key characters.",
    )

    user_setting = st.text_input(
        label="Setting / Location",
        key="setting_input",
        placeholder="e.g., The fog-drenched floating city of Aethelgard",
        help="Where and when the story unfolds.",
    )

    # E. Advanced API Settings Expander
    with st.expander("⚙️ API Configuration", expanded=False):
        env_key = get_api_key()
        has_env_key = bool(env_key)

        if has_env_key:
            st.success("✅ Gemini API key detected (Active via Secrets/Env)")
        else:
            st.warning("⚠️ No GEMINI_API_KEY detected. Provide below or in secrets.")

        custom_api_key = st.text_input(
            "Override Gemini API Key",
            type="password",
            key="sidebar_api_key",
            help="Optionally provide an API key for this session without modifying configuration.",
        )

        selected_model = st.selectbox(
            "Gemini Model",
            options=["gemini-1.5-flash", "gemini-2.0-flash", "gemini-1.5-pro"],
            index=0,
            help="Choose your preferred Gemini model version.",
        )

    st.markdown("---")

    # F. Action Buttons
    col_btn1, col_btn2 = st.columns([1.5, 1])
    with col_btn1:
        generate_clicked = st.button(
            "✨ Generate Story",
            type="primary",
            use_container_width=True,
        )
    with col_btn2:
        clear_clicked = st.button(
            "🧹 Clear",
            on_click=clear_inputs,
            use_container_width=True,
        )


# -----------------------------------------------------------------------------
# 4. Story Generation Execution Handler
# -----------------------------------------------------------------------------
def execute_generation():
    """Trigger the story generator backend with validation and spinner."""
    st.session_state.api_error = None

    active_api_key = st.session_state.sidebar_api_key.strip() or get_api_key()
    if not active_api_key:
        st.error(
            "🔑 **Gemini API Key Required**: Please provide your key in `.env` "
            "(`GEMINI_API_KEY=your_key`) or paste it under **Sidebar > ⚙️ API Configuration**."
        )
        return

    if not user_topic or not user_topic.strip():
        st.warning("⚠️ Please provide a story topic or premise to begin!")
        return

    with st.spinner("🔮 Summoning the muse... Crafting narrative arc and prose with Gemini..."):
        result = generate_story(
            topic=user_topic,
            genre=user_genre,
            characters=user_characters,
            setting=user_setting,
            mood=user_mood,
            audience=user_audience,
            length_choice=user_length,
            title=user_title,
            api_key=active_api_key,
            model_name=selected_model,
        )

    if result["success"]:
        st.session_state.story_data = result
        st.session_state.api_error = None
    else:
        st.session_state.api_error = result["error"]


if generate_clicked:
    execute_generation()


# -----------------------------------------------------------------------------
# 5. Main Canvas: Reading Area or Welcome Landing
# -----------------------------------------------------------------------------
st.markdown('<div class="gradient-title">✨ AI Story Generator</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="gradient-subtitle">Transform your wildest ideas into rich, structured narratives powered by Google Gemini.</div>',
    unsafe_allow_html=True,
)

# Display error alerts if any occurred
if st.session_state.api_error:
    st.error(f"❌ **Error Encountered:** {st.session_state.api_error}")

# When story exists, render the reading area
if st.session_state.story_data:
    data = st.session_state.story_data
    meta = data["metadata"]

    # Action Toolbar
    st.markdown("### 📖 Generated Story")

    col_tb1, col_tb2, col_tb3, col_tb4 = st.columns([1.2, 1.3, 1.2, 2.3])
    with col_tb1:
        st.button("🔄 Regenerate", on_click=execute_generation, use_container_width=True, help="Rerun with current inputs")

    with col_tb2:
        st.button("✨ Another Story", on_click=clear_inputs, use_container_width=True, help="Start a new concept")

    with col_tb3:
        # Prepare full story text file for download
        download_payload = f"""{data['title']}
========================================
Genre: {meta.get('genre')} | Mood: {meta.get('mood')}
Target Audience: {meta.get('audience')} | Words: {data.get('word_count')}
Model: {meta.get('model')}
========================================

{data['story']}
"""
        st.download_button(
            label="💾 Download TXT",
            data=download_payload,
            file_name=f"{data['title'].lower().replace(' ', '_')[:30]}_story.txt",
            mime="text/plain",
            use_container_width=True,
        )

    # Badges row
    st.markdown(
        f"""
        <div class="badge-container">
            <span class="badge badge-highlight">🏷️ {meta.get('genre', 'Story')}</span>
            <span class="badge">🎭 Mood: {meta.get('mood', 'Dynamic')}</span>
            <span class="badge">🎯 Audience: {meta.get('audience', 'All')}</span>
            <span class="badge">📊 {data.get('word_count', 0)} words</span>
            <span class="badge">⏱️ ~{data.get('reading_time_min', 1)} min read</span>
            <span class="badge">🤖 {meta.get('model', 'Gemini')}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Formatted Reading Card
    st.markdown(
        f"""
        <div class="story-container">
            <div class="story-title">{data['title']}</div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(data["story"])

    st.markdown("</div>", unsafe_allow_html=True)

    # Copy Story Helper
    with st.expander("📋 Copy Story Text", expanded=False):
        st.code(download_payload, language="markdown")
        st.caption("Click the copy icon in the upper right corner of the box above to copy instantly.")

else:
    # Landing Page with quick inspiration and guide
    st.markdown("---")
    st.markdown("#### 🌟 Welcome to the Creative Studio")
    st.write(
        "Whether you're developing an epic sci-fi universe, a cozy mystery, or a heartwarming children's fable, "
        "our AI Story Generator crafts balanced narrative arcs with distinct character depth and thematic resolution."
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(
            """
            <div class="feature-card">
                <div class="feature-title">🏛️ 5-Act Narrative Arc</div>
                <div class="feature-desc">Every story organically progresses through Introduction, Character Development, Conflict, Climax, and Resolution.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            """
            <div class="feature-card">
                <div class="feature-title">🎭 Tailored Tone & Audience</div>
                <div class="feature-desc">Dynamically calibrates vocabulary, tension, and stakes for Children, Teens, or Adult readers across 8 distinct genres.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col3:
        st.markdown(
            """
            <div class="feature-card">
                <div class="feature-title">⚡ Instant Export & Iteration</div>
                <div class="feature-desc">Regenerate, tweak parameters on the fly, copy directly to your clipboard, or download formatted TXT manuscripts.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("##### 💡 Need Inspiration? Try one of these ideas:")
    demo_col1, demo_col2 = st.columns(2)

    with demo_col1:
        st.button(
            "🚀 Load Sci-Fi Prompt: The Dyson Singularity",
            on_click=load_scifi_prompt,
            use_container_width=True,
        )

    with demo_col2:
        st.button(
            "🧙 Load Fantasy Prompt: The Whispering Library",
            on_click=load_fantasy_prompt,
            use_container_width=True,
        )


# -----------------------------------------------------------------------------
# 6. Modern Footer
# -----------------------------------------------------------------------------
st.markdown(
    """
    <div class="footer-container">
        AI Story Generator • Built with <b>Streamlit</b> & <b>Google Gemini API</b> • Clean Architecture for Generative AI Mini-Projects
    </div>
    """,
    unsafe_allow_html=True,
)
