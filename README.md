# 🏋️‍♂️ KineticAI: Personalized Workout & Injury Prevention Planner

> **AI Engineering Cohort — Assignment 1: Build a Workout Plan Generator**  
> *Role:* Licensed Doctor of Physical Therapy (DPT) & Certified Strength and Conditioning Specialist (CSCS)  
> *Architecture:* Modular Python, Streamlit UI, Groq LLM Cloud, managed via `uv` and `pyproject.toml`.

---

## 📌 Executive Overview

KineticAI moves beyond generic workout prompts by embedding a **Doctor of Physical Therapy (DPT) and CSCS** persona into the prompt engineering pipeline. It collects structured biomechanical inputs and user constraints to generate a clinically sound weekly training plan that maximizes hypertrophy, strength, or endurance while actively screening for injury risks, joint discomfort, and contraindications.

---

## 📂 Project Structure

```text
workout-plan-generator/
├── .venv/                  # Managed automatically by uv
├── .env                    # Local secrets (GROQ_API_KEY=gsk_...) [Git ignored]
├── .env.sample             # Sanitized environment template for reviewers
├── .gitignore              # Ignores .venv, .env, __pycache__, etc.
├── .python-version         # Pinned Python version (3.11)
├── pyproject.toml          # PEP 621 dependencies & project metadata
├── workout_generator.py    # Core domain: Typed LLM function, prompt engine, error boundaries
├── app.py                  # Presentation layer: Single-page Streamlit app with session state
└── README.md               # Architecture documentation, runbook & grading guide
```

---

## 🚀 Quickstart & Setup (Powered by `uv`)

This project uses modern Python packaging via **[`uv`](https://docs.astral.sh/uv/)**.

### 1. Prerequisites
Ensure `uv` is installed:
```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. Clone & Environment Configuration
```bash
# 1. Navigate to the project directory
cd workout-plan-generator

# 2. Copy the sample environment file
cp .env.sample .env

# 3. Add your Groq API Key to .env
# Open .env and set: GROQ_API_KEY=gsk_your_actual_key_here
```

### 3. Launch the Application
Run Streamlit directly with `uv`. `uv` will automatically provision `.venv`, resolve `uv.lock`, and start the app:
```bash
uv run streamlit run app.py
```

*(Alternatively, standard pip workflows are also supported: `pip install -e .` followed by `streamlit run app.py`)*

---

## 🧪 Iterative Testing & Verification Runbook

Follow these structured steps to evaluate the system iteratively:

### Step 1: Unit & Domain Validation (No API call required)
Verify input boundaries and defensive constraints:
```bash
uv run python workout_generator.py
```
**Expected Outcome:**
- Valid inputs pass smoothly.
- Invalid input tests (e.g., 0 days selected, invalid goal strings) trigger custom `InvalidInputError` exceptions without crashing.

### Step 2: Authentication Error Boundary Test
1. Temporarily comment out or invalidate `GROQ_API_KEY` in `.env`.
2. Launch `uv run streamlit run app.py`.
3. Click **🚀 Generate Plan**.
**Expected Outcome:**
- Friendly alert: *"🔑 Authentication Error: Groq API key not found."* with actionable setup instructions. Zero unhandled Python tracebacks.

### Step 3: Clinical Limitation & Constraint Testing
1. In the UI, set:
   - **Goal:** Build muscle
   - **Experience:** Beginner
   - **Days:** 3
   - **Equipment:** `Home dumbbells`
   - **Limitations:** *"Patellofemoral pain (bad knees) on deep squats, and right shoulder impingement on overhead press."*
2. Click **🚀 Generate Plan**.
**Expected Verification:**
- Output contains **exactly 3 days**.
- Zero barbells or cable machines are recommended (strictly dumbbells or bodyweight).
- Deep quad-shear squats are replaced with joint-friendly regressions (e.g., Box Squats, Goblet Squats with vertical shins, or Glute-dominant Hinges).
- Overhead pressing is replaced with neutral-grip floor presses, landmine presses, or lateral raises.
- Prominent **Clinical & Legal Disclaimer** is rendered.

### Step 4: Session State Persistence & Download (Stretch Goals)
1. After generating a plan, modify one of the dropdowns or click the sidebar.
   - **Verification:** The generated plan remains intact on the screen without being wiped out.
2. Click **📥 Download Plan (.md)** to verify markdown file export.
3. Click **🔄 Regenerate Variation** to confirm variation generation without crashing.

### Step 5: Exercise Swapper Test (Clinical Substitution Stretch Goal)
1. Expand the **🔄 Exercise Swapper** section.
2. Select or enter:
   - *Exercise to replace:* Select any recommended exercise from the dropdown (or choose custom)
   - *Reason:* `Lower back soreness / lumbar flexion sensitivity`
3. Click **Find Safe Clinical Substitutions**.
**Expected Outcome:**
- Generates 2 safe regressions (e.g., Supported Chest Dumbbell Row / Glute Bridges / Swiss Ball Leg Curls) with execution cues.

---

## 📊 Rubric Compliance Matrix

| Rubric Criteria | Weight | Implementation Details |
| :--- | :---: | :--- |
| **App runs without crashing on empty or invalid input** | **20%** | Bounded Streamlit widgets (slider 1–7) + domain validator `validate_workout_inputs()` preventing invalid states. |
| **Inputs are structured and passed into prompt** | **25%** | Dedicated `build_user_prompt()` systematically compiles parameters into contextual directives. |
| **Prompt respects constraints, well-structured, usable** | **30%** | DPT/CSCS system prompt with strict equipment locks, exact day matching, injury regressions, and clean Markdown tables. |
| **Error handling (API, rate limits, malformed response)** | **15%** | Granular try/except blocks catching `AuthenticationError`, `RateLimitError`, `APIConnectionError`, and blank responses with user-friendly alerts. |
| **Code quality (type hints, separation, readability)** | **10%** | Full Python type hints throughout `workout_generator.py` and `app.py`, custom domain exception hierarchy, and modular file layout. |

