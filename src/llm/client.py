import os
import time
from typing import Optional

from dotenv import load_dotenv
from google import genai
from google.genai import types


# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

load_dotenv()


# ============================================================
# CONFIGURATION
# ============================================================

MODEL_NAME = os.getenv(
    "GEMINI_MODEL",
    "gemini-2.5-flash",
)

MAX_RETRIES = 5

INITIAL_RETRY_DELAY = 5

MAX_RETRY_DELAY = 60


# ============================================================
# API KEY
# ============================================================

API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise RuntimeError(
        "GEMINI_API_KEY environment variable is not set.\n"
        "Set GEMINI_API_KEY in your environment or create "
        "a .env file in the project root."
    )


# ============================================================
# GEMINI CLIENT
# ============================================================

client = genai.Client(
    api_key=API_KEY
)


# ============================================================
# RETRYABLE ERRORS
# ============================================================

def is_retryable_error(
    error: Exception,
) -> bool:
    """
    Determine whether an exception represents a temporary
    API/server condition that should be retried.
    """

    error_text = str(error).lower()

    retryable_statuses = [
        # HTTP status codes
        "429",
        "500",
        "502",
        "503",
        "504",

        # Gemini/API messages
        "unavailable",
        "resource exhausted",
        "temporarily unavailable",
        "internal server error",
        "bad gateway",
        "gateway timeout",

        # Network errors
        "timeout",
        "timed out",
        "connection reset",
        "connection aborted",
        "connection refused",
    ]

    return any(
        status in error_text
        for status in retryable_statuses
    )


# ============================================================
# RETRY DELAY
# ============================================================

def get_retry_delay(
    attempt: int,
) -> int:
    """
    Calculate exponential backoff delay.

    Attempt 1 -> 5 seconds
    Attempt 2 -> 10 seconds
    Attempt 3 -> 20 seconds
    Attempt 4 -> 40 seconds
    Attempt 5 -> 60 seconds maximum
    """

    return min(
        INITIAL_RETRY_DELAY * (2 ** (attempt - 1)),
        MAX_RETRY_DELAY,
    )


# ============================================================
# GENERATE TEXT
# ============================================================

def generate_text(
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.2,
    max_output_tokens: int = 4096,
) -> str:
    """
    Generate text using Gemini.

    Temporary API/server errors are retried using
    exponential backoff.

    Permanent errors are raised immediately.
    """

    last_error: Optional[Exception] = None

    for attempt in range(
        1,
        MAX_RETRIES + 1,
    ):

        try:

            print(
                f"\nGenerating with Gemini "
                f"(attempt {attempt}/{MAX_RETRIES})..."
            )

            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=temperature,
                    max_output_tokens=max_output_tokens,
                ),
            )

            # ------------------------------------------------
            # Validate response
            # ------------------------------------------------

            if response is None:

                raise RuntimeError(
                    "Gemini returned an empty response object."
                )

            text = getattr(
                response,
                "text",
                None,
            )

            if text is None:

                raise RuntimeError(
                    "Gemini response did not contain text."
                )

            text = text.strip()

            if not text:

                raise RuntimeError(
                    "Gemini returned empty text."
                )

            print(
                "Gemini generation successful."
            )

            return text

        except Exception as error:

            last_error = error

            # ================================================
            # PERMANENT ERROR
            # ================================================

            if not is_retryable_error(error):

                print(
                    "\n"
                    + "=" * 70
                )

                print(
                    "NON-RETRYABLE GEMINI ERROR"
                )

                print(
                    "=" * 70
                )

                print(
                    f"Error: {error}"
                )

                raise

            # ================================================
            # RETRIES EXHAUSTED
            # ================================================

            if attempt >= MAX_RETRIES:

                print(
                    "\n"
                    + "=" * 70
                )

                print(
                    "GEMINI API RETRIES EXHAUSTED"
                )

                print(
                    "=" * 70
                )

                print(
                    f"Attempts  : {MAX_RETRIES}"
                )

                print(
                    f"Model     : {MODEL_NAME}"
                )

                print(
                    f"Last error: {error}"
                )

                print(
                    "=" * 70
                )

                raise

            # ================================================
            # RETRY
            # ================================================

            delay = get_retry_delay(
                attempt
            )

            print(
                "\n"
                + "-" * 70
            )

            print(
                "Temporary Gemini API error."
            )

            print(
                f"Attempt {attempt}/{MAX_RETRIES} failed."
            )

            print(
                f"Model: {MODEL_NAME}"
            )

            print(
                f"Error: {error}"
            )

            print(
                f"Retrying in {delay} seconds..."
            )

            print(
                "-" * 70
            )

            time.sleep(delay)

    # ========================================================
    # SAFETY FALLBACK
    # ========================================================

    if last_error:

        raise last_error

    raise RuntimeError(
        "Gemini generation failed unexpectedly."
    )