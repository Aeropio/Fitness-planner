"""
Core LLM Service and Workout Generation Engine.

Persona: Licensed Physical Therapist (DPT) & Certified Strength & Conditioning
Specialist (CSCS) specializing in biomechanics, injury prevention, and functional rehab.
"""

from __future__ import annotations

import os
from typing import Optional, Dict, Any, Tuple
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # Fallback to manual .env parsing if python-dotenv is not yet installed
    env_file = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(env_file):
        with open(env_file, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    os.environ.setdefault(key.strip(), val.strip())

# Supported input domains
VALID_GOALS = ["Build muscle", "Lose fat", "General fitness", "Improve endurance"]
VALID_LEVELS = ["Beginner", "Intermediate", "Advanced"]
VALID_EQUIPMENT = ["No equipment", "Home dumbbells", "Full gym"]

# Default model configuration (active and supported on Groq)
DEFAULT_MODEL = "qwen/qwen3.8-27b"


def get_available_models(api_key: Optional[str] = None) -> list[str]:
    """
    Retrieves available text generation models from Groq for the given API key.
    Filters out non-chat models (such as whisper, guardrails, or TTS).
    Falls back to active supported models if offline or if query fails.
    """
    fallback_models = ["qwen/qwen3.8-27b", "openai/gpt-oss-120b"]
    effective_api_key = api_key or os.getenv("GROQ_API_KEY")
    if not effective_api_key or not effective_api_key.strip():
        return fallback_models

    try:
        from groq import Groq
        client = Groq(api_key=effective_api_key.strip())
        model_list = client.models.list()

        excluded_keywords = ["whisper", "guard", "orpheus", "safeguard"]
        chat_models = [
            m.id for m in model_list.data
            if not any(kw in m.id.lower() for kw in excluded_keywords)
        ]

        preferred_order = ["qwen/qwen3.8-27b", "openai/gpt-oss-120b"]
        sorted_models = [m for m in preferred_order if m in chat_models]
        remaining = [m for m in chat_models if m not in preferred_order]
        result = sorted_models + sorted(remaining)

        return result if result else fallback_models
    except Exception:
        return fallback_models


class WorkoutGeneratorError(Exception):
    """Base exception for all workout generation domain errors."""
    pass


class InvalidInputError(WorkoutGeneratorError):
    """Raised when user inputs fail schema or boundary validation."""
    pass


class APIAuthenticationError(WorkoutGeneratorError):
    """Raised when Groq API key is missing or invalid."""
    pass


class APIRateLimitError(WorkoutGeneratorError):
    """Raised when Groq rate limits are encountered."""
    pass


class LLMServiceError(WorkoutGeneratorError):
    """Raised when external API invocation or parsing fails."""
    pass


def validate_workout_inputs(
    fitness_goal: str,
    experience_level: str,
    days_per_week: int,
    equipment_access: str,
    limitations: Optional[str] = None,
) -> None:
    """
    Validates structured input boundaries before dispatching to the LLM.
    
    Raises:
        InvalidInputError: If any parameter violates domain bounds.
    """
    if not fitness_goal or fitness_goal not in VALID_GOALS:
        raise InvalidInputError(
            f"Invalid fitness goal '{fitness_goal}'. Must be one of: {', '.join(VALID_GOALS)}"
        )

    if not experience_level or experience_level not in VALID_LEVELS:
        raise InvalidInputError(
            f"Invalid experience level '{experience_level}'. Must be one of: {', '.join(VALID_LEVELS)}"
        )

    if not isinstance(days_per_week, int) or days_per_week < 1 or days_per_week > 7:
        raise InvalidInputError(
            f"Invalid days per week ({days_per_week}). Training schedule must be between 1 and 7 days."
        )

    if not equipment_access or equipment_access not in VALID_EQUIPMENT:
        raise InvalidInputError(
            f"Invalid equipment access '{equipment_access}'. Must be one of: {', '.join(VALID_EQUIPMENT)}"
        )


def build_system_prompt() -> str:
    """
    Constructs the system prompt defining the Clinical PT & S&C persona,
    constraint satisfaction guidelines, and output formatting rules.
    """
    return """You are a dual-credentialed Doctor of Physical Therapy (DPT) and Certified Strength and Conditioning Specialist (CSCS).
Your expertise blends clinical biomechanics, progressive overload, injury risk mitigation, and functional movement restoration.

YOUR CORE MANDATE:
Generate a personalized, highly structured, evidence-based weekly workout plan that strictly honors every user constraint.

CLINICAL & PROGRAMMING DIRECTIVES:
1. HARD CONSTRAINT SATISFACTION:
   - Equipment Access: NEVER prescribe equipment the user lacks. If "Home dumbbells" is selected, do not include barbells, cables, or specialized gym machines. If "No equipment" is selected, prescribe strictly bodyweight, calisthenics, and household leverage exercises.
   - Schedule Cadence: Prescribe EXACTLY the requested number of training days (e.g., if 3 days, provide Day 1, Day 2, and Day 3). Do not provide fewer or more days.
   - Experience Level: Adjust movement complexity, neurological demand, and set volume accordingly (Beginner = motor pattern mastery, moderate volume; Advanced = higher mechanical tension, varied tempos, intelligent undulating splits).

2. INJURY PREVENTION & REHABILITATION INTEGRATION:
   - If the user reports injuries, pain, or movement limitations (e.g., bad knees, lower back tightness, rotator cuff impingement):
     a. Explicitly substitute contraindicated movement patterns with biomechanically safe, pain-free regressions.
     b. Provide targeted pre-activation / joint mobility primers in each day's warm-up.
     c. Include joint-friendly coaching cues (e.g., joint alignment, tempo control, avoiding end-range shear stress).
   - If no limitations are provided, include general bulletproofing warm-ups (hip mobility, thoracic spine mobility, scapular stability).

3. SAFETY & MEDICAL BOUNDARIES:
   - Do NOT make diagnostic claims or promise to 'cure' an acute medical condition.
   - Always include a concise, professional Clinical & Legal Disclaimer at the end.

4. REQUIRED OUTPUT STRUCTURE (Use Clean Markdown):
   - Executive Program Overview (Goal, Split Philosophy, Frequency)
   - Day-by-Day Detailed Plan:
     * Focus / Target Muscle Groups
     * Dynamic Warm-up & Joint Mobility (2-3 targeted activation drills)
     * Main Working Block (Structured Markdown Table with columns: Exercise, Sets, Reps/Duration, Rest, Biomechanical Coaching Cue & Regression)
     * Cool-Down & Down-regulation
   - Recovery & Joint Health Notes
   - Professional Disclaimer
"""


def build_user_prompt(
    fitness_goal: str,
    experience_level: str,
    days_per_week: int,
    equipment_access: str,
    limitations: Optional[str] = None,
) -> str:
    """
    Compiles structured user parameters into a contextual prompt for the LLM.
    """
    limitations_text = (
        limitations.strip()
        if (limitations and limitations.strip())
        else "None reported. Prioritize standard joint longevity and safe progressive overload."
    )

    return f"""Please design my customized weekly training program based on my personal clinical and fitness profile:

- Primary Fitness Goal: {fitness_goal}
- Experience Level: {experience_level}
- Training Frequency: {days_per_week} days per week
- Available Equipment: {equipment_access}
- Injuries, Pain, or Physical Limitations: {limitations_text}

Remember:
1. Deliver a full, ready-to-use plan covering exactly {days_per_week} days.
2. Every exercise MUST be 100% executable with '{equipment_access}'.
3. Specifically tailor exercise selection and joint angles to protect and rehab '{limitations_text}'.
4. Format each workout day with an organized markdown table and specific coaching cues.
"""


def generate_workout_plan(
    fitness_goal: str,
    experience_level: str,
    days_per_week: int,
    equipment_access: str,
    limitations: Optional[str] = None,
    api_key: Optional[str] = None,
    model: str = DEFAULT_MODEL,
    temperature: float = 0.5,
) -> str:
    """
    Generates a personalized workout and rehab plan using the Groq API.

    Parameters:
        fitness_goal: Target objective ('Build muscle', 'Lose fat', etc.)
        experience_level: User training experience ('Beginner', 'Intermediate', 'Advanced')
        days_per_week: Integer between 1 and 7
        equipment_access: Available gear ('No equipment', 'Home dumbbells', 'Full gym')
        limitations: Optional string describing injuries or movement restrictions
        api_key: Optional Groq API key (falls back to GROQ_API_KEY environment variable)
        model: Groq model identifier
        temperature: LLM sampling temperature (default 0.5 for grounded consistency)

    Returns:
        Formatted markdown string containing the complete workout plan.

    Raises:
        InvalidInputError: If parameters are invalid or out of bounds.
        APIAuthenticationError: If API key is missing or rejected.
        APIRateLimitError: If Groq rate limits are exceeded.
        LLMServiceError: For network errors or unexpected LLM failures.
    """
    # 1. Validate structured input boundaries
    validate_workout_inputs(
        fitness_goal=fitness_goal,
        experience_level=experience_level,
        days_per_week=days_per_week,
        equipment_access=equipment_access,
        limitations=limitations,
    )

    # 2. Resolve API Key
    effective_api_key = api_key or os.getenv("GROQ_API_KEY")
    if not effective_api_key or not effective_api_key.strip():
        raise APIAuthenticationError(
            "Groq API key not found. Please provide an API key in the application "
            "or set 'GROQ_API_KEY' in your .env file."
        )

    # 3. Import and initialize Groq client safely
    try:
        from groq import Groq, AuthenticationError, RateLimitError, APIConnectionError, APIError
    except ImportError:
        raise LLMServiceError(
            "The 'groq' package is not installed. Please run 'uv sync' or 'pip install groq'."
        )

    try:
        client = Groq(api_key=effective_api_key.strip())
    except Exception as exc:
        raise LLMServiceError(f"Failed to initialize Groq client: {str(exc)}") from exc

    # 4. Compile prompts
    system_prompt = build_system_prompt()
    user_prompt = build_user_prompt(
        fitness_goal=fitness_goal,
        experience_level=experience_level,
        days_per_week=days_per_week,
        equipment_access=equipment_access,
        limitations=limitations,
    )

    # 5. Invoke LLM with granular exception boundaries
    try:
        completion = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=temperature,
            max_tokens=4096,
        )

        if not completion.choices or not completion.choices[0].message:
            raise LLMServiceError("Received an empty response from the LLM. Please try again.")

        content = completion.choices[0].message.content
        if not content or not content.strip():
            raise LLMServiceError("The generated workout plan was blank. Please retry.")

        return content.strip()

    except AuthenticationError as exc:
        raise APIAuthenticationError(
            "Invalid Groq API Key. Please verify your API key in .env or the sidebar."
        ) from exc

    except RateLimitError as exc:
        raise APIRateLimitError(
            "Groq API rate limit reached. Please wait a few moments before retrying."
        ) from exc

    except APIConnectionError as exc:
        raise LLMServiceError(
            "Unable to connect to the Groq API network. Please check your internet connection."
        ) from exc

    except APIError as exc:
        raise LLMServiceError(
            f"Groq API error encountered ({exc.status_code if hasattr(exc, 'status_code') else 'Unknown'}): {str(exc)}"
        ) from exc

    except Exception as exc:
        raise LLMServiceError(f"An unexpected error occurred during generation: {str(exc)}") from exc


def swap_exercise(
    current_plan: str,
    exercise_to_replace: str,
    reason_or_limitation: str,
    equipment_access: str,
    api_key: Optional[str] = None,
    model: str = DEFAULT_MODEL,
) -> str:
    """
    Stretch Goal: Provides a clinically sound alternative for a single exercise
    given equipment and limitation constraints without having to regenerate the whole week.
    """
    effective_api_key = api_key or os.getenv("GROQ_API_KEY")
    if not effective_api_key:
        raise APIAuthenticationError("Groq API key required to swap exercise.")

    from groq import Groq, AuthenticationError, RateLimitError, APIError

    client = Groq(api_key=effective_api_key.strip())

    prompt = f"""As a Physical Therapist (DPT) and S&C Specialist, suggest 2 biomechanically safe replacement exercises for:
Target Exercise to Replace: '{exercise_to_replace}'
Reason / Pain / Limitation: '{reason_or_limitation}'
Allowed Equipment: '{equipment_access}'

For each alternative, provide:
1. Exercise Name
2. Prescribed Sets & Reps
3. Why this protects the joint / accommodates the limitation
4. Exact execution cue
Keep the response crisp and structured in markdown.
"""
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": build_system_prompt()},
                {"role": "user", "content": prompt},
            ],
            temperature=0.4,
            max_tokens=1000,
        )
        return response.choices[0].message.content.strip()
    except Exception as exc:
        raise LLMServiceError(f"Failed to swap exercise: {str(exc)}") from exc


if __name__ == "__main__":
    # Self-test routine for CLI / verification
    import sys

    print("--- Workout Generator Domain Self-Test ---")
    try:
        # Test input validator
        validate_workout_inputs("Build muscle", "Beginner", 3, "Home dumbbells")
        print("✓ Input validator passed valid parameters.")
    except Exception as e:
        print(f"✗ Input validator failed: {e}")
        sys.exit(1)

    try:
        # Test input validator catching invalid days
        validate_workout_inputs("Build muscle", "Beginner", 0, "Home dumbbells")
        print("✗ Validator failed to catch 0 days!")
    except InvalidInputError:
        print("✓ Input validator correctly rejected 0 days.")

    # Optional Live API verification if GROQ_API_KEY is detected
    api_key = os.getenv("GROQ_API_KEY")
    if api_key and api_key.strip():
        print(f"\n--- Live Groq API Test (Model: {DEFAULT_MODEL}) ---")
        try:
            sample_plan = generate_workout_plan(
                fitness_goal="General fitness",
                experience_level="Beginner",
                days_per_week=2,
                equipment_access="No equipment",
                limitations="None",
                model=DEFAULT_MODEL,
            )
            print("✓ Live workout plan generated successfully!")
            print(f"✓ Plan preview ({len(sample_plan)} chars):\n")
            print(sample_plan[:350] + "...\n")
        except Exception as err:
            print(f"✗ Live generation failed: {err}")
    else:
        print("\nℹ️ Tip: To test live Groq calls, ensure GROQ_API_KEY is set in your .env file.")
