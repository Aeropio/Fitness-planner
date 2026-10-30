"""
KineticAI - Personalized Workout & Injury Prevention Planner
Presentation Layer (Streamlit Single-Page Application)

Engineered with Physical Therapy & CSCS Principles for safe, joint-friendly programming.
"""

from __future__ import annotations

import importlib
import os
import streamlit as st

# Domain service & exceptions (with reload to avoid stale Streamlit sys.modules cache)
import workout_generator
try:
    importlib.reload(workout_generator)
except Exception:
    pass

from workout_generator import (
    generate_workout_plan,
    swap_exercise,
    VALID_GOALS,
    VALID_LEVELS,
    VALID_EQUIPMENT,
    InvalidInputError,
    APIAuthenticationError,
    APIRateLimitError,
    LLMServiceError,
)

# Resilient model helper resolution
try:
    from workout_generator import get_available_models, DEFAULT_MODEL
except ImportError:
    DEFAULT_MODEL = "qwen/qwen3.8-27b"
    def get_available_models(api_key: str | None = None) -> list[str]:
        return ["qwen/qwen3.8-27b", "openai/gpt-oss-120b"]

# Page configuration
st.set_page_config(
    page_title="KineticAI | Physio-Engineered Workout Generator",
    page_icon="🏋️‍♂️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------
# Session State Initialization
# ---------------------------------------------------------
if "workout_plan" not in st.session_state:
    st.session_state["workout_plan"] = None

if "last_params" not in st.session_state:
    st.session_state["last_params"] = None

if "swapped_results" not in st.session_state:
    st.session_state["swapped_results"] = None


# ---------------------------------------------------------
# Sidebar: Configuration & API Key
# ---------------------------------------------------------
with st.sidebar:
    st.title("🏋️‍♂️ KineticAI Config")
    st.caption("Clinical Biomechanics & Injury-Free Programming")

    st.markdown("---")
    
    # Environment API Key or Manual Entry
    env_key = os.getenv("GROQ_API_KEY", "")
    api_key_input = st.text_input(
        "Groq API Key",
        value=env_key,
        type="password",
        help="Reads GROQ_API_KEY from .env by default. You can override it here.",
    )

    available_models = get_available_models(api_key_input or env_key)
    default_idx = (
        available_models.index(DEFAULT_MODEL)
        if DEFAULT_MODEL in available_models
        else 0
    )

    model_choice = st.selectbox(
        "LLM Engine",
        options=available_models,
        index=default_idx,
        help="Active Groq models. High-capacity models like Qwen 3.8 and GPT-OSS yield superior clinical nuance.",
    )

    st.markdown("---")
    st.markdown(
        """
        **Clinical Methodology:**
        - **DPT & CSCS Principles:** Dynamic joint preparation, safe movement planes, and volume auto-regulation.
        - **Constraint Guarantee:** Strict equipment lock & exact schedule pacing.
        - **Injury Regression:** Contraindicated movements are replaced with joint-friendly variations.
        """
    )
    st.caption("Assignment Submission • Codebasics AI Engineering Cohort")


# ---------------------------------------------------------
# Main UI Header
# ---------------------------------------------------------
st.title("🏋️‍♂️ KineticAI: Personalized Workout & Rehab Planner")
st.markdown(
    "Designed from the perspective of a **Doctor of Physical Therapy (DPT)** and **Certified Strength Coach (CSCS)**. "
    "Get an evidence-based, structured weekly workout plan that maximizes performance while proactively preventing injury."
)
st.markdown("---")

# ---------------------------------------------------------
# Section 1: Structured Input Controls
# ---------------------------------------------------------
st.subheader("1. Athlete & Clinical Profile")

col1, col2 = st.columns(2)

with col1:
    fitness_goal = st.selectbox(
        "🎯 Primary Fitness Goal",
        options=VALID_GOALS,
        index=0,
        help="Defines loading parameters, tempo, and metabolic demands.",
    )

    experience_level = st.selectbox(
        "📊 Experience Level",
        options=VALID_LEVELS,
        index=1,
        help="Beginner (motor learning & stability), Intermediate (progressive overload), Advanced (undulating volume).",
    )

    days_per_week = st.slider(
        "📅 Days Available Per Week",
        min_value=1,
        max_value=7,
        value=4,
        help="Exact training days to be programmed into your weekly split.",
    )

with col2:
    equipment_access = st.selectbox(
        "🧰 Equipment Access",
        options=VALID_EQUIPMENT,
        index=2,
        help="Hard constraint: Only exercises compatible with this gear will be programmed.",
    )

    limitations = st.text_area(
        "🩹 Injuries, Pain, or Physical Limitations (Optional)",
        placeholder="e.g. Mild patellofemoral knee pain with deep squats, history of left rotator cuff pinch on overhead press, lumbar tightness.",
        help="Our clinical prompt will screen for contraindicated movements and provide safe exercise regressions.",
        height=128,
    )

# ---------------------------------------------------------
# Action Buttons: Generate & Regenerate
# ---------------------------------------------------------
btn_col1, btn_col2, _ = st.columns([1.5, 1.5, 5])

generate_clicked = btn_col1.button("🚀 Generate Plan", type="primary", use_container_width=True)
regenerate_clicked = btn_col2.button("🔄 Regenerate Variation", use_container_width=True)

# ---------------------------------------------------------
# Execution Logic
# ---------------------------------------------------------
should_run = generate_clicked or (regenerate_clicked and st.session_state["workout_plan"] is not None)

if should_run:
    # Set temperature: slightly higher for regeneration to provide variety
    temp = 0.7 if regenerate_clicked else 0.4

    with st.spinner("Analyzing biomechanics and designing your customized plan..."):
        try:
            plan = generate_workout_plan(
                fitness_goal=fitness_goal,
                experience_level=experience_level,
                days_per_week=days_per_week,
                equipment_access=equipment_access,
                limitations=limitations,
                api_key=api_key_input,
                model=model_choice,
                temperature=temp,
            )

            # Persist in session state
            st.session_state["workout_plan"] = plan
            st.session_state["last_params"] = {
                "goal": fitness_goal,
                "level": experience_level,
                "days": days_per_week,
                "equipment": equipment_access,
                "limitations": limitations,
            }
            # Clear previous exercise swaps on new plan generation
            st.session_state["swapped_results"] = None
            st.success("Your customized plan has been successfully generated!")

        except InvalidInputError as e:
            st.warning(f"⚠️ Input Validation Warning: {str(e)}")
        except APIAuthenticationError as e:
            st.error(f"🔑 Authentication Error: {str(e)}")
            st.info("Tip: Create a `.env` file with `GROQ_API_KEY=gsk_...` or enter your key in the left sidebar.")
        except APIRateLimitError as e:
            st.error(f"⏳ Rate Limit Reached: {str(e)}")
        except LLMServiceError as e:
            st.error(f"🚨 Generation Failure: {str(e)}")
        except Exception as e:
            st.error(f"An unexpected error occurred: {str(e)}")

elif regenerate_clicked and st.session_state["workout_plan"] is None:
    st.info("Please generate an initial workout plan first before regenerating.")

# ---------------------------------------------------------
# Section 2: Display Generated Plan & Stretch Features
# ---------------------------------------------------------
if st.session_state["workout_plan"]:
    st.markdown("---")
    st.subheader("2. Your Personalized Program")

    # Stretch Goal: Export / Download Plan
    export_col1, export_col2 = st.columns([2, 6])
    with export_col1:
        st.download_button(
            label="📥 Download Plan (.md)",
            data=st.session_state["workout_plan"],
            file_name="kineticai_workout_plan.md",
            mime="text/markdown",
            use_container_width=True,
        )

    # Render Markdown Plan (unsafe_allow_html=True renders <br> line breaks inside tables)
    st.markdown(st.session_state["workout_plan"], unsafe_allow_html=True)

    # ---------------------------------------------------------
    # Stretch Goal: Exercise Swapper (Clinical Substitution)
    # ---------------------------------------------------------
    st.markdown("---")
    with st.expander("🔄 Exercise Swapper: Need a modification or substitute?"):
        st.markdown(
            "If an exercise feels uncomfortable, aggravates a joint, or you lack a specific setup, "
            "request targeted clinical alternatives below without re-running the entire week."
        )
        swap_col1, swap_col2 = st.columns(2)
        with swap_col1:
            exercise_to_swap = st.text_input(
                "Exercise to Replace",
                placeholder="e.g. Barbell Back Squat, Romanian Deadlift, Push-ups",
            )
        with swap_col2:
            swap_reason = st.text_input(
                "Reason / Joint Issue",
                placeholder="e.g. Anterior knee pain at 90 deg, wrist pain in extension",
            )

        if st.button("Find Safe Clinical Substitutions"):
            if not exercise_to_swap:
                st.warning("Please specify the name of the exercise you want to replace.")
            else:
                with st.spinner("Consulting clinical biomechanics database..."):
                    try:
                        swap_suggestion = swap_exercise(
                            current_plan=st.session_state["workout_plan"],
                            exercise_to_replace=exercise_to_swap,
                            reason_or_limitation=swap_reason or "Discomfort / unavailable",
                            equipment_access=equipment_access,
                            api_key=api_key_input,
                            model=model_choice,
                        )
                        st.session_state["swapped_results"] = swap_suggestion
                    except Exception as e:
                        st.error(f"Failed to generate alternative: {str(e)}")

        if st.session_state.get("swapped_results"):
            st.markdown("### Suggested Clinical Replacements:")
            st.markdown(st.session_state["swapped_results"], unsafe_allow_html=True)

