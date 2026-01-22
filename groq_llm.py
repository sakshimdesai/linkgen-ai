import os
from typing import Optional, Tuple
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError("❌ GROQ_API_KEY missing. Add it to your .env file.")

# IMPORTANT: do NOT pass unsupported kwargs (like proxies)
client = Groq(api_key=GROQ_API_KEY)


def _clean_text(s: str) -> str:
    """Trim, collapse excessive blank lines/spaces."""
    if not s:
        return ""
    # Normalize Windows newlines, strip leading/trailing spaces per line, collapse blank lines
    lines = [ln.strip() for ln in s.replace("\r\n", "\n").split("\n")]
    # Remove consecutive empty lines
    out = []
    prev_blank = False
    for ln in lines:
        is_blank = (ln == "")
        if is_blank and prev_blank:
            continue
        out.append(ln)
        prev_blank = is_blank
    return "\n".join(out).strip()


def build_prompt(
    topic: str,
    length_label: str,
    language: str,
    custom_prompt: Optional[str] = None,
    tone: str = "professional",
) -> str:
    """
    Strict prompt: forces the model to use the user's custom text if provided,
    and generate natively in the selected language (not translating from English first).
    """

    length_map = {
        "Short": "30-60 words",
        "Medium": "120-160 words",
        "Long": "220-320 words",
    }
    word_range = length_map.get(length_label, "120-160 words")

    lang_instruction = ""
    lang_lower = language.lower()
    if lang_lower == "english":
        lang_instruction = "Write the post in natural, native English."
    elif lang_lower == "hindi":
        lang_instruction = (
            "पोस्ट को स्वाभाविक, प्रामाणिक हिंदी में लिखें। शुरुआत से हिंदी में लिखें; अंग्रेज़ी से अनुवाद न करें।"
        )
    elif lang_lower == "kannada":
        lang_instruction = (
            "ಪೋಸ್ಟ್ ಅನ್ನು ಸ್ವಾಭಾವಿಕ, ಶುದ್ಧ ಕನ್ನಡದಲ್ಲಿ ಬರೆಯಿರಿ. ಪ್ರಾರಂಭದಿಂದಲೇ ಕನ್ನಡದಲ್ಲಿ ರಚಿಸಿ; ಇಂಗ್ಲಿಷ್‌ನಿಂದ ಅನುವಾದಿಸಬೇಡಿ."
        )
    else:
        lang_instruction = f"Write the post in {language}."

    user_fragment = ""
    if custom_prompt and custom_prompt.strip():
        snippet = custom_prompt.strip()
        user_fragment = (
            "\nIMPORTANT: Incorporate the following user instruction as the main focus. "
            "Do NOT ignore it. Use the exact context to guide the content.\n"
            f"USER_PROMPT_START\n{snippet}\nUSER_PROMPT_END\n"
        )

    # Note: No backslashes inside f-strings; plain string concatenation to avoid syntax issues.
    prompt = (
        "You are an expert LinkedIn post writer.\n\n"
        f'Topic: "{topic}"\n'
        f"{lang_instruction}\n"
        f"Tone: {tone}\n"
        f"Target length: {word_range}.\n\n"
        "Structure:\n"
        "- Start with a short hook (1 sentence).\n"
        "- Include 2–4 short paragraphs or bullet points with insights/lessons.\n"
        "- End with a concise CTA or a question to invite comments.\n\n"
        "Formatting:\n"
        "- Use clean line breaks and simple bullets.\n"
        "- Sound human and professional; avoid robotic phrasing.\n"
        "- DO NOT include hashtags (they will be generated separately).\n\n"
        "Return ONLY the post text, no extra commentary, no JSON.\n"
        + user_fragment
    )
    return prompt


def generate_groq_post(
    topic: str,
    length_label: str,
    language: str,
    custom_prompt: Optional[str] = None,
    tone: str = "professional",
    debug: bool = False,
) -> Tuple[str, Optional[str]]:
    """
    Returns (post_text, prompt_if_debug_else_None).
    If debug=True, we also return the prompt so you can display it in UI.
    """
    prompt = build_prompt(topic, length_label, language, custom_prompt, tone)

    if debug:
        print("----- LLM PROMPT START -----")
        print(prompt)
        print("----- LLM PROMPT END -----")

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.6,
    )

    try:
        raw = response.choices[0].message.content
    except Exception:
        raw = str(response)

    cleaned = _clean_text(raw)
    return (cleaned, prompt if debug else None)


def generate_groq_hashtags(topic: str) -> list[str]:
    """
    Generate up to 8 short, relevant, space-separated hashtags. 
    """
    prompt = (
        "Generate 8 short, relevant LinkedIn hashtags for this topic:\n"
        f"{topic}\n\n"
        "Rules:\n"
        "- Return ONLY hashtags, space-separated.\n"
        "- No commentary, no bullets, no numbering."
    )

    resp = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.4,
    )

    try:
        raw = resp.choices[0].message.content.strip()
    except Exception:
        raw = ""

    tags = raw.split()
    tags = [t if t.startswith("#") else f"#{t}" for t in tags]
    return tags[:8]
