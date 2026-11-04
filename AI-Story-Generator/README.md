# 📖 AI Story Generator

An AI-powered web application that generates original, compelling, and structured short stories dynamically using the **Google Gemini API** and **Streamlit**.

Built with a modular Python architecture, this mini-project demonstrates modern generative AI engineering principles, prompt engineering, structured narrative generation, and responsive web design.

---

## 🌟 Key Features

- **🎭 Rich Story Customization:**
  - **Topic / Premise:** User-defined narrative hooks and concepts.
  - **Custom or AI Title:** Provide a custom title or let Gemini generate one.
  - **8 Diverse Genres:** Fantasy, Science Fiction, Horror, Mystery, Romance, Adventure, Comedy, and Thriller.
  - **6 Moods & Atmospheres:** Emotional, Suspenseful, Inspirational, Funny, Dark, Mysterious.
  - **Target Audience Calibration:** Children, Teenagers, or Adults (adjusting vocabulary, maturity, and thematic depth).
  - **Main Characters & Setting:** Specify character personas, roles, and world locations.
  - **Target Story Length:**
    - Short: 200–300 words
    - Medium: 500–700 words
    - Long: 1000–1200 words

- **🏛️ 5-Stage Narrative Architecture:**
  Each story strictly adheres to classic storytelling mechanics:
  1. *Introduction* (The Hook & Status Quo)
  2. *Character Development* (Motivations & Core Stakes)
  3. *Conflict* (Escalating Friction & Obstacles)
  4. *Climax* (Peak Tension & Crucial Decision)
  5. *Resolution* (Earned Payoff & Meaningful Closure)

- **🎨 Modern Dark UI / UX:**
  - Radial glowing dark background with glassmorphic cards.
  - Gradient titles, badges, and primary action buttons.
  - Dedicated reading card formatted with elegant serif typography.
  - Real-time word count and estimated reading time calculations.

- **⚡ User Productivity Tools:**
  - **Regenerate Story:** Re-roll the narrative with current parameters.
  - **Generate Another Story:** Quickly start a new concept.
  - **One-Click Copy:** Easily copy the full story text to clipboard.
  - **Download as TXT:** Save formatted stories directly to disk.
  - **Clear Inputs:** Reset the entire form with a single button.
  - **One-Click Demo Inspiration:** Pre-populate sci-fi or fantasy scenarios to test immediately.

- **🛡️ Secure & Resilient Architecture:**
  - Zero hardcoded credentials (managed via `.env` and `python-dotenv`).
  - Dual SDK compatibility: modern `google-genai` (current unified SDK) with automatic fallback to `google-generativeai`.
  - Input validation and informative error alerts for missing keys, quota limits (429), or network dropouts.

---

## 🏗️ Project Architecture & File Structure

```text
AI-Story-Generator/
│
├── app.py                 # Streamlit UI, state management, and user interaction workflow
├── story_generator.py     # Gemini API integration, prompt engineering, and response parsing
├── requirements.txt       # Project Python dependencies
├── .env.example           # Template for environment credentials
├── .env                   # Local secrets (excluded from git)
├── .gitignore             # Git ignore rules protecting API keys and cache
└── README.md              # Project documentation and setup guide
```

### Module Responsibilities

1. **`app.py`:**
   - Initializes Streamlit page layout and custom CSS styling.
   - Handles `st.session_state` to support input clearing, regeneration, and downloading.
   - Manages the sidebar form and renders the dedicated reading interface.

2. **`story_generator.py`:**
   - Validates user inputs against allowed constraints.
   - Assembles system instructions and dynamic user prompts.
   - Connects to Google GenAI client (`gemini-2.5-flash` or `gemini-1.5-flash`).
   - Normalizes titles, parses narrative body, and calculates word count and reading metrics.

---

## 🛠️ Technology Stack

| Layer | Technology | Purpose |
|---|---|---|
| **Frontend** | Streamlit | Reactive web interface and controls |
| **Backend** | Python 3.10+ | Core logic and validation |
| **LLM Model** | Google Gemini (`gemini-2.5-flash` / `gemini-1.5-flash`) | Dynamic story generation |
| **AI SDK** | `google-genai` / `google-generativeai` | Official Google GenAI SDK |
| **Configuration** | `python-dotenv` | Secure environment variable handling |

---

## 🚀 Quickstart Guide

### 1. Prerequisites
- Python **3.10 or higher** installed on your system.
- A free Google account to acquire a Gemini API key.

### 2. Clone or Navigate to the Project Directory
```bash
cd AI-Story-Generator
```

### 3. Create and Activate a Virtual Environment

**On macOS / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**On Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

---

## 🔑 Obtaining & Configuring Your Gemini API Key

1. Visit **Google AI Studio**: [https://aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)
2. Sign in with your Google account.
3. Click **"Create API Key"** and copy your generated key string.
4. In your project directory, copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
5. Open `.env` in any text editor and replace the placeholder:
   ```env
   GEMINI_API_KEY=AIzaSy...your_actual_key_here
   GEMINI_MODEL=gemini-2.5-flash
   ```

*(Alternatively, you can also paste your API key directly into the application's sidebar under **⚙️ API Configuration** during runtime).*

---

## ▶️ Running the Application

With your virtual environment active, run:

```bash
streamlit run app.py
```

The Streamlit server will start and automatically open the application in your default web browser at:
```text
http://localhost:8501
```

---

## 🧪 Sample Input & Generated Story Output

### Sample Input
- **Story Topic:** A solitary chronologist in an ancient observatory discovers that constellations are moving backwards.
- **Title (Optional):** *(Blank - AI generated)*
- **Genre:** Science Fiction
- **Mood:** Suspenseful
- **Target Audience:** Adults
- **Main Characters:** Dr. Vane Karr (veteran astronomer)
- **Setting:** Mount Alabaster High-Altitude Observatory
- **Story Length:** Medium (500–700 words)

### Sample Output

```markdown
# Title: The Reverse Zodiac

The bronze armature of the great refraction mirror groaned against the sub-zero mountain air. Dr. Vane Karr adjusted the focal vernier, rubbing grease and frost from his thumb. For forty years, the Mount Alabaster Observatory had tracked the steady crawl of the Milky Way—predictable as a pulse, indifferent as marble.

Until tonight.

Vane blinked against the icy eyepiece. The constellation Cygnus was wrong. Its tail star, Deneb, had shifted three arcseconds toward the zenith since twilight. In astronomy, three arcseconds over an epoch was notable; three arcseconds in two hours was cosmic impossibility.

"Telemetry calibration error," Vane muttered aloud, his breath condensing in pale plumes across the frosted brass gears. He climbed the iron gantry down to the punch-card chronometers. The brass counterweights ticked in strict unison: beat, click, beat, click. But when he fed the optical plates through the comparator, the truth curdled in his stomach.

The stars were not drifting. They were retracing their steps.

An unnatural vibration hummed through the granite foundations of the peak. Outside, the pine valleys were silent, bathed in sterile moonlight. Above, Cassiopeia's jagged crown was slowly folding backward, straightening into lines recorded only in Sumerian clay tablets six millennia ago. The universe wasn't expanding—it was rewinding.

A sharp clatter echoed behind him. The seismic gauge on the master console trembled violently as atmospheric pressure plunged. If celestial geometry was in reverse, planetary gravity would inevitably slip its gears.

Vane reached for the radio transmitter to alert the lowlands, but his hand froze. Through the open dome slit, Orion's belt shifted visibly, three brilliant diamond lanterns flickering as if caught in a temporal eddy. He had spent his life waiting for the heavens to speak; he had never imagined their message would be an undoing.

With trembling fingers, Vane loaded a fresh roll of parchment into the solar recorder. He would document the rewind until the dawn refused to rise.
```

---

## 🧠 AI Prompt Engineering Design

The system implements a structured **two-tier prompt strategy**:

1. **System Prompt (`build_system_prompt`):**
   - Establishes the LLM identity as an acclaimed fiction author.
   - Enforces the 5-phase storytelling blueprint (Hook -> Development -> Conflict -> Climax -> Resolution).
   - Establishes boundaries for audience maturity, grammatical precision, and natural dialogue.
   - Prohibits meta-commentary (e.g., "Sure, here is your story:").

2. **Dynamic User Prompt (`build_user_prompt`):**
   - Merges all user configurations (topic, character dynamics, setting, genre, tone).
   - Injects quantitative word count constraints (e.g., *200–300 words* vs. *1000–1200 words*).
   - Formats instructions for clean title parsing via regex.

---

## 🔮 Future Enhancement Suggestions

1. **Audio Narration (Text-to-Speech):** Integrate ElevenLabs or Google Cloud TTS for voiceover narration.
2. **AI Cover Art Generator:** Use Imagen 3 to generate book cover illustrations matching the story mood.
3. **Interactive "Choose Your Own Adventure":** Allow branching choices at the end of each chapter.
4. **PDF / EPUB Export:** Compile multi-chapter anthologies into formatted e-books.
5. **Multi-Language Support:** Allow story generation and translation into Spanish, French, German, or Japanese.

---

## 📄 License & Attribution

Designed and developed as a modern Generative AI Mini-Project. Built with [Streamlit](https://streamlit.io/) and the [Google GenAI SDK](https://github.com/googleapis/python-genai).
