# post_generator.py (FIXED - Rate Limit Handling with 3 Tones)
from typing import Optional, Dict, Any
import concurrent.futures
from datetime import datetime
import time

# Import the low-level generation functions
from groq_llm import generate_groq_post, generate_groq_hashtags


def generate_post(
    topic: str,
    length: str,
    language: str,
    custom_prompt: Optional[str] = None,
    debug: bool = False,
) -> Dict[str, Any]:
    """
    Orchestrates: post -> hashtags -> engagement score.
    Returns a dict consumed by main.py
    """
    post_text, maybe_prompt = generate_groq_post(
        topic=topic,
        length_label=length,
        language=language,
        custom_prompt=custom_prompt,
        tone="professional",
        debug=debug,
    )

    hashtags = generate_groq_hashtags(topic)

    # lightweight engagement proxy: chars/250 (rounded)
    engagement = round(len(post_text) / 250.0, 2)

    result = {
        "post": post_text,
        "hashtags": hashtags,
        "engagement": engagement,
    }

    if debug:
        result["debug_prompt"] = maybe_prompt

    return result


# ===== MULTI-TONE (FIXED with 3 tones and rate limit handling) =====

def generate_multi_tone_posts(
    topic: str,
    length: str,
    language: str,
    custom_prompt: Optional[str] = None,
    debug: bool = False,
    use_parallel: bool = False,
) -> Dict[str, Dict[str, Any]]:
    """
    Generate 3 different tone variations of a post.
    Reduced from 5 to 3 tones to avoid rate limit issues.

    Args:
        topic: The topic or prompt for the post
        length: Post length (Short/Medium/Long)
        language: Language for the post
        custom_prompt: Optional custom prompt
        debug: Enable debug mode
        use_parallel: Generate tones in parallel (not recommended, may hit rate limits)

    Returns:
        Dictionary with tone names as keys and post data as values
        Example: {"Professional": {...}, "Casual": {...}, "Inspirational": {...}}
    """

    # Define the 3 tones with their descriptions (reduced from 5 to avoid rate limits)
    tones = {
        "Professional": "formal, business-appropriate, and polished",
        "Casual": "friendly, conversational, and approachable",
        "Inspirational": "uplifting, motivational, and energizing"
    }

    def generate_single_tone(tone_name: str, tone_description: str, retry_count: int = 3) -> tuple:
        """Helper function to generate a single tone variation with retry logic"""
        for attempt in range(retry_count):
            try:
                post_text, maybe_prompt = generate_groq_post(
                    topic=topic,
                    length_label=length,
                    language=language,
                    custom_prompt=custom_prompt,
                    tone=tone_description,
                    debug=debug,
                )

                # Generate hashtags for this tone (same topic-based hashtags)
                hashtags = generate_groq_hashtags(topic)

                # Calculate engagement score
                engagement = round(len(post_text) / 250.0, 2)

                result = {
                    "post": post_text,
                    "hashtags": hashtags,
                    "engagement": engagement,
                    "tone": tone_name,
                }

                if debug:
                    result["debug_prompt"] = maybe_prompt

                return tone_name, result

            except Exception as e:
                error_msg = str(e)
                # Check if it's a rate limit error
                if "rate_limit" in error_msg.lower() or "429" in error_msg:
                    if attempt < retry_count - 1:
                        # Wait before retrying (exponential backoff)
                        wait_time = (attempt + 1) * 2  # 2, 4, 6 seconds
                        print(f"Rate limit hit for {tone_name}. Waiting {wait_time}s before retry {attempt + 2}/{retry_count}...")
                        time.sleep(wait_time)
                        continue
                    else:
                        # Max retries reached, return a fallback
                        return tone_name, {
                            "post": f"Unable to generate {tone_name} tone due to rate limits. Please try again in a moment or uncheck multi-tone for single generation.",
                            "hashtags": [],
                            "engagement": 0,
                            "tone": tone_name,
                            "error": True
                        }
                else:
                    # Non-rate-limit error
                    return tone_name, {
                        "post": f"Error generating {tone_name} tone: {error_msg}",
                        "hashtags": [],
                        "engagement": 0,
                        "tone": tone_name,
                        "error": True
                    }

        # Should not reach here, but just in case
        return tone_name, {
            "post": f"Error generating {tone_name} tone after {retry_count} attempts.",
            "hashtags": [],
            "engagement": 0,
            "tone": tone_name,
            "error": True
        }

    results: Dict[str, Dict[str, Any]] = {}

    if use_parallel:
        # Parallel generation (faster but may hit rate limits)
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            future_to_tone = {
                executor.submit(generate_single_tone, tone_name, tone_desc): tone_name
                for tone_name, tone_desc in tones.items()
            }

            for future in concurrent.futures.as_completed(future_to_tone):
                tone_name, result = future.result()
                results[tone_name] = result
    else:
        # Sequential generation (safer, avoids rate limits)
        for idx, (tone_name, tone_description) in enumerate(tones.items()):
            # Add a delay between requests to avoid rate limits (2 seconds for safety)
            if idx > 0:
                time.sleep(2.0)  # 2 second delay between each tone
            
            tone_name, result = generate_single_tone(tone_name, tone_description)
            results[tone_name] = result

    return results


def generate_custom_tone_post(
    topic: str,
    length: str,
    language: str,
    custom_tone: str,
    custom_prompt: Optional[str] = None,
    debug: bool = False,
) -> Dict[str, Any]:
    """
    Generate a post with a custom user-defined tone.

    Args:
        topic: The topic or prompt for the post
        length: Post length (Short/Medium/Long)
        language: Language for the post
        custom_tone: User's custom tone description (e.g., "humorous and witty")
        custom_prompt: Optional custom prompt
        debug: Enable debug mode

    Returns:
        Dictionary with post data
    """
    post_text, maybe_prompt = generate_groq_post(
        topic=topic,
        length_label=length,
        language=language,
        custom_prompt=custom_prompt,
        tone=custom_tone,
        debug=debug,
    )

    hashtags = generate_groq_hashtags(topic)
    engagement = round(len(post_text) / 250.0, 2)

    result = {
        "post": post_text,
        "hashtags": hashtags,
        "engagement": engagement,
        "tone": custom_tone,
    }

    if debug:
        result["debug_prompt"] = maybe_prompt

    return result


# ===== MULTI-MODEL FEATURE (UNCHANGED - WORKING) =====

def generate_multi_model_posts(
    topic: str,
    length: str,
    language: str,
    custom_prompt: Optional[str] = None,
    debug: bool = False,
    use_parallel: bool = False,  # Changed to False by default for rate limit safety
) -> Dict[str, Dict[str, Any]]:
    """
    Generate post outputs for 3 'model style variants' for comparison.
    Reduced from 4 to 3 to avoid rate limits.

    Returns dict: { "Concise": {...}, "Detailed": {...}, "Conversational": {...} }
    """

    # Define model variants (reduced to 3 to avoid rate limits)
    model_variants = {
        "Llama-3.1-8B": "Respond in a concise, neutral style similar to a smaller LLM (brief, exact).",
        "Llama-3.1-70B": "Respond with a richer, more detailed style (longer reasoning, more examples).",
        "Groq": "Respond in a crisp, fast style with practical examples and short paragraphs.",
    }

    def _gen_for_model(model_name: str, model_instruction: str) -> tuple:
        try:
            # Build a model-specific prompt by prefixing an instruction
            prefix = model_instruction
            # Use custom_prompt if provided; otherwise use topic
            base = custom_prompt if custom_prompt else topic
            full_prompt = (prefix + "\n\n" + base).strip()

            # Call the underlying generator with the full_prompt as topic
            post_text, maybe_prompt = generate_groq_post(
                topic=full_prompt,
                length_label=length,
                language=language,
                custom_prompt=None,
                tone="professional",
                debug=debug,
            )

            hashtags = generate_groq_hashtags(topic)
            engagement = round(len(post_text) / 250.0, 2)

            result = {
                "post": post_text,
                "hashtags": hashtags,
                "engagement": engagement,
                "model": model_name,
            }
            if debug:
                result["debug_prompt"] = maybe_prompt
            return model_name, result
        except Exception as e:
            return model_name, {
                "post": f"Error generating for {model_name}: {str(e)}",
                "hashtags": [],
                "engagement": 0,
                "model": model_name,
                "error": True
            }

    results: Dict[str, Dict[str, Any]] = {}

    if use_parallel:
        # Parallel generation (faster but may hit rate limits)
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            future_to_model = {
                executor.submit(_gen_for_model, name, instr): name
                for name, instr in model_variants.items()
            }
            for future in concurrent.futures.as_completed(future_to_model):
                model_name, res = future.result()
                results[model_name] = res
    else:
        # Sequential generation (safer, avoids rate limits)
        for idx, (name, instr) in enumerate(model_variants.items()):
            # Add delay between requests to avoid rate limits
            if idx > 0:
                time.sleep(2.0)  # 2 second delay between each model variant
            
            model_name, res = _gen_for_model(name, instr)
            results[model_name] = res

    return results


# End of post_generator.py