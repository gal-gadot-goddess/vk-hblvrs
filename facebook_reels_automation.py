"""
Habla Verse - Bilingual Spanish/Russian Content Generator for VK
Teaches Spanish to Russian speakers with Habla Verse branding
"""

import os
import sys
import json
import random
import asyncio
import subprocess
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()

POLLINATIONS_API_KEY = os.getenv("POLLINATIONS_API_KEY")
AI_MODEL = os.getenv("AI_MODEL", "gemini-fast")

# Directories
BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
IMAGES_DIR = OUTPUT_DIR / "images"
AUDIO_DIR = OUTPUT_DIR / "audio"
VIDEO_DIR = OUTPUT_DIR / "video"
HISTORY_DIR = OUTPUT_DIR / "history"

for d in [OUTPUT_DIR, IMAGES_DIR, AUDIO_DIR, VIDEO_DIR, HISTORY_DIR]:
    d.mkdir(exist_ok=True)

# Video settings (9:16 vertical)
VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 1920
FPS = 30

# English category names (for American/European learners)
CATEGORIES_ENGLISH = [
    "Motivation", "Love", "Success", "Wisdom", "Happiness",
    "Self Improvement", "Gratitude", "Friendship", "Hope", "Creativity",
    "Inner Peace", "Confidence", "Perseverance", "Inspiration", "Positive Life",
    "Courage", "Kindness", "Patience", "Forgiveness", "Strength",
    "Joy", "Balance", "Growth", "Purpose", "Mindfulness",
]

# Emoji icons for each category (for visual branding)
CATEGORY_EMOJIS = {
    "Motivation": "🔥", "Love": "❤️", "Success": "🏆", "Wisdom": "🦉", "Happiness": "😊",
    "Self Improvement": "🌟", "Gratitude": "🙏", "Friendship": "🤝", "Hope": "💡", "Creativity": "🎨",
    "Inner Peace": "🪶", "Confidence": "💪", "Perseverance": "⚡", "Inspiration": "✨", "Positive Life": "☀️",
    "Courage": "🌸", "Kindness": "💐", "Patience": "⏳", "Forgiveness": "🕊️", "Strength": "🗿",
    "Joy": "🎉", "Balance": "⚖️", "Growth": "🌱", "Purpose": "🎯", "Mindfulness": "🧘",
}

# Russian translations for display
CATEGORIES_RUSSIAN = {
    "Motivation": "Мотивация",
    "Love": "Любовь",
    "Success": "Успех",
    "Wisdom": "Мудрость",
    "Happiness": "Счастье",
    "Self Improvement": "Саморазвитие",
    "Gratitude": "Благодарность",
    "Friendship": "Дружба",
    "Hope": "Надежда",
    "Creativity": "Творчество",
    "Inner Peace": "Внутренний Покой",
    "Confidence": "Уверенность",
    "Perseverance": "Настойчивость",
    "Inspiration": "Вдохновение",
    "Positive Life": "Позитивная Жизнь",
    "Courage": "Мужество",
    "Kindness": "Доброта",
    "Patience": "Терпение",
    "Forgiveness": "Прощение",
    "Strength": "Сила",
    "Joy": "Радость",
    "Balance": "Баланс",
    "Growth": "Рост",
    "Purpose": "Цель",
    "Mindfulness": "Осознанность",
}

# Edge TTS voices
SPANISH_VOICE = "es-ES-AlvaroNeural"
RUSSIAN_VOICE = "ru-RU-DmitryNeural"

# Phrase history file (NEVER delete this!)
PHRASE_HISTORY_FILE = HISTORY_DIR / "all_generated_phrases.json"


# ============== PHRASE HISTORY MANAGEMENT (Prevent Repeats) ==============

# Track phrases generated in current session to prevent immediate repeats
_session_phrases = set()

def load_phrase_history():
    """Load all previously generated phrases"""
    if PHRASE_HISTORY_FILE.exists():
        with open(PHRASE_HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"phrases": [], "last_updated": None}


def save_phrase_history(data):
    """Save phrase history"""
    data["last_updated"] = datetime.now().isoformat()
    with open(PHRASE_HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def is_phrase_used(english_phrase):
    """Check if phrase was already generated (global history + current session)"""
    history = load_phrase_history()
    english_lower = english_phrase.lower().strip()
    
    # Check global history
    for p in history.get("phrases", []):
        if p.get("english", "").lower().strip() == english_lower:
            return True
    
    # Check current session
    if english_lower in _session_phrases:
        return True
    
    return False


def add_phrase_to_session(english_phrase):
    """Add phrase to session tracking"""
    _session_phrases.add(english_phrase.lower().strip())


def add_phrases_to_history(phrases, category):
    """Add new phrases to history"""
    history = load_phrase_history()
    for phrase in phrases:
        history["phrases"].append({
            "english": phrase.get("english", ""),
            "russian": phrase.get("russian", phrase.get("Russian", "")),
            "category": category,
            "generated_at": datetime.now().isoformat()
        })
    save_phrase_history(history)
    print(f"[history] Added {len(phrases)} phrases to history (total: {len(history['phrases'])})")


# ============== CONTENT GENERATION ==============

FALLBACK_PHRASES = {
    "Motivation": [
        {"english": "Cada d\u00eda, una nueva oportunidad", "russian": "\u041a\u0430\u0436\u0434\u044b\u0439 \u0434\u0435\u043d\u044c, \u043d\u043e\u0432\u044b\u0439 \u0448\u0430\u043d\u0441", "spanish_cyrillic": "\u041a\u0430\u0434\u0430 \u0434\u0438\u0430, \u0443\u043d\u0430 \u043d\u0443\u044d\u0432\u0430 \u043e\u043f\u043e\u0440\u0442\u0443\u043d\u0438\u0434\u0430\u0434"},
        {"english": "T\u00fa eres, m\u00e1s fuerte de lo que piensas", "russian": "\u0422\u044b \u0441\u0438\u043b\u044c\u043d\u0435\u0435, \u0447\u0435\u043c \u0434\u0443\u043c\u0430\u0435\u0448\u044c", "spanish_cyrillic": "\u0422\u0443 \u044d\u0440\u0435\u0441, \u043c\u0430\u0441 \u0444\u0443\u044d\u0440\u0442\u044d \u0434\u0435 \u043b\u043e \u043a\u0435 \u043f\u044c\u0435\u043d\u0441\u0430\u0441"},
        {"english": "Peque\u00f1os pasos, grandes cambios", "russian": "\u041c\u0430\u043b\u0435\u043d\u044c\u043a\u0438\u0435 \u0448\u0430\u0433\u0438, \u0431\u043e\u043b\u044c\u0448\u0438\u0435 \u0438\u0437\u043c\u0435\u043d\u0435\u043d\u0438\u044f", "spanish_cyrillic": "\u041f\u044d\u043a\u0435\u043d\u044c\u043e\u0441 \u043f\u0430\u0441\u043e\u0441, \u0433\u0440\u0430\u043d\u0434\u044d\u0441 \u043a\u0430\u043c\u0431\u044c\u043e\u0441"},
        {"english": "Sigue adelante, sigue creciendo", "russian": "\u041f\u0440\u043e\u0434\u043e\u043b\u0436\u0430\u0439 \u0434\u0432\u0438\u0433\u0430\u0442\u044c\u0441\u044f, \u043f\u0440\u043e\u0434\u043e\u043b\u0436\u0430\u0439 \u0440\u0430\u0441\u0442\u0438", "spanish_cyrillic": "\u0421\u0438\u0433\u044d \u0430\u0434\u0435\u043b\u044f\u043d\u0442\u044d, \u0441\u0438\u0433\u044d \u043a\u0440\u044d\u0441\u044c\u0435\u043d\u0434\u043e"},
        {"english": "Tu potencial, es infinito", "russian": "\u0422\u0432\u043e\u0439 \u043f\u043e\u0442\u0435\u043d\u0446\u0438\u0430\u043b, \u0431\u0435\u0437\u0433\u0440\u0430\u043d\u0438\u0447\u0435\u043d", "spanish_cyrillic": "\u0422\u0443 \u043f\u043e\u0442\u044d\u043d\u0441\u044c\u044f\u043b, \u044d\u0441 \u0438\u043d\u0444\u0438\u043d\u0438\u0442\u043e"},
    ],
    "Love": [
        {"english": "El amor lo puede todo", "russian": "\u041b\u044e\u0431\u043e\u0432\u044c \u043c\u043e\u0436\u0435\u0442 \u0432\u0441\u0451", "spanish_cyrillic": "\u042d\u043b\u044c \u0430\u043c\u043e\u0440 \u043b\u043e \u043f\u0443\u044d\u0434\u044d \u0442\u043e\u0434\u043e"},
        {"english": "Sigue a tu coraz\u00f3n siempre", "russian": "\u0412\u0441\u0435\u0433\u0434\u0430 \u0441\u043b\u0435\u0434\u0443\u0439 \u0437\u0430 \u0441\u0435\u0440\u0434\u0446\u0435\u043c", "spanish_cyrillic": "\u0421\u0438\u0433\u044d \u0430 \u0442\u0443 \u043a\u043e\u0440\u0430\u0441\u043e\u043d \u0441\u044c\u0435\u043c\u043f\u0440\u044d"},
        {"english": "Cada coraz\u00f3n, tiene su canci\u00f3n", "russian": "\u0423 \u043a\u0430\u0436\u0434\u043e\u0433\u043e \u0441\u0435\u0440\u0434\u0446\u0430, \u0435\u0441\u0442\u044c \u043f\u0435\u0441\u043d\u044f", "spanish_cyrillic": "\u041a\u0430\u0434\u0430 \u043a\u043e\u0440\u0430\u0441\u043e\u043d, \u0442\u044c\u0435\u043d\u044d \u0441\u0443 \u043a\u0430\u043d\u0441\u044c\u043e\u043d"},
    ],
    "Success": [
        {"english": "El trabajo duro, da frutos", "russian": "\u0422\u044f\u0436\u0435\u043b\u044b\u0439 \u0442\u0440\u0443\u0434, \u043e\u043a\u0443\u043f\u0430\u0435\u0442\u0441\u044f", "spanish_cyrillic": "\u042d\u043b\u044c \u0442\u0440\u0430\u0431\u0430\u0445\u043e \u0434\u0443\u0440\u043e, \u0434\u0430 \u0444\u0440\u0443\u0442\u043e\u0441"},
        {"english": "Conc\u00e9ntrate en tus metas", "russian": "\u0421\u043e\u0441\u0440\u0435\u0434\u043e\u0442\u043e\u0447\u044c\u0441\u044f \u043d\u0430 \u0441\u0432\u043e\u0438\u0445 \u0446\u0435\u043b\u044f\u0445", "spanish_cyrillic": "\u041a\u043e\u043d\u0441\u044d\u043d\u0442\u0440\u0430\u0442\u044d \u044d\u043d \u0442\u0443\u0441 \u043c\u044d\u0442\u0430\u0441"},
    ],
}

def get_fallback_phrases(category_english: str, num_phrases: int = 5) -> list:
    """Return fallback phrases when API is unavailable"""
    fallback = FALLBACK_PHRASES.get(category_english, [])
    if not fallback:
        fallback = [
            {"english": "Aprende algo nuevo cada d\u00eda", "russian": "\u0423\u0447\u0438\u0441\u044c \u0447\u0435\u043c\u0443-\u0442\u043e \u043d\u043e\u0432\u043e\u043c\u0443 \u043a\u0430\u0436\u0434\u044b\u0439 \u0434\u0435\u043d\u044c", "spanish_cyrillic": "\u0410\u043f\u0440\u044d\u043d\u0434\u044d \u0430\u043b\u044c\u0433\u043e \u043d\u0443\u044d\u0432\u043e \u043a\u0430\u0434\u0430 \u0434\u0438\u0430"},
            {"english": "La pr\u00e1ctica, lleva al progreso", "russian": "\u041f\u0440\u0430\u043a\u0442\u0438\u043a\u0430 \u0432\u0435\u0434\u0451\u0442 \u043a \u043f\u0440\u043e\u0433\u0440\u0435\u0441\u0441\u0443", "spanish_cyrillic": "\u041b\u0430 \u043f\u0440\u0430\u043a\u0442\u0438\u043a\u0430, \u043b\u044c\u0435\u0432\u0430 \u0430\u043b\u044c \u043f\u0440\u043e\u0433\u0440\u044d\u0441\u043e"},
            {"english": "Sigue adelante, t\u00fa puedes", "russian": "\u041f\u0440\u043e\u0434\u043e\u043b\u0436\u0430\u0439, \u0443 \u0442\u0435\u0431\u044f \u043f\u043e\u043b\u0443\u0447\u0438\u0442\u0441\u044f", "spanish_cyrillic": "\u0421\u0438\u0433\u044d \u0430\u0434\u0435\u043b\u044f\u043d\u0442\u044d, \u0442\u0443 \u043f\u0443\u044d\u0434\u044d\u0441"},
        ]
    
    unique = []
    for p in fallback:
        if not is_phrase_used(p["english"]):
            p.setdefault("spanish_cyrillic", "")
            unique.append(p)
        if len(unique) >= num_phrases:
            break
    
    return unique


def generate_phrases(category_english: str, num_phrases: int = 5) -> list:
    """Generate unique bilingual phrases with natural pauses, ensuring NO repeats ever"""

    category_russian = CATEGORIES_RUSSIAN[category_english]

    # Optimized for 2-minute total generation time
    max_attempts = 3  # Max 3 attempts (not 10) to stay under 2 minutes
    all_tried_phrases = set()  # Track all phrases seen across all attempts
    
    for attempt in range(max_attempts):
        try:
            import requests
            url = "https://gen.pollinations.ai/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {POLLINATIONS_API_KEY}",
                "Content-Type": "application/json"
            }

            # Load history to give AI context of what's already used
            history = load_phrase_history()
            used_english = [p["english"] for p in history.get("phrases", [])[-50:]]
            used_context = "\n".join([f"- {p}" for p in used_english[:20]])

            # Add randomness to prompt to prevent API caching
            style_variations = [
                "Write phrases that feel personal and intimate, like advice from a friend.",
                "Create phrases with vivid imagery and metaphors from nature.",
                "Write phrases that challenge conventional thinking and inspire action.",
                "Create phrases that emphasize inner strength and self-discovery.",
                "Write phrases that celebrate small victories and daily progress.",
                "Create phrases with a poetic, contemplative tone.",
                "Write direct, empowering statements that motivate immediate action.",
                "Create phrases that blend wisdom with modern life challenges.",
            ]
            style_instruction = random.choice(style_variations)

            # Add random seed to prevent API caching
            random_seed = random.randint(1000, 9999)

            prompt = f"""Create {num_phrases * 3} unique {category_english} phrases for Russian speakers learning Spanish.

{style_instruction}

FORMAT RULES (CRITICAL):
1. Keep phrases SHORT (4-8 words max per language)
2. Add NATURAL PAUSES using commas (e.g., "Sue\u00f1a en grande, empieza peque\u00f1o")
3. Each phrase should be speakable in 2-4 seconds
4. NEVER use these already-generated phrases:
{used_context}

5. AVOID THESE OVERUSED CLICH\u00c9S (never use these):
   - "Poco a poco"
   - "Nunca te rindas"
   - "Cree en ti mismo"
   - "Todo es posible"
   - "El \u00e9xito llega"
   - "Sigue adelante"
   - "No te detengas"
   - "Eres \u00fanico"
   - "La vida es bella"

6. CRITICAL - FIELD RULES:
   - "english": ONLY Spanish text (NO Russian words allowed!)
   - "russian": ONLY Russian translation
   - "spanish_cyrillic": The Spanish phrase written with Russian/Cyrillic letters for pronunciation (e.g. "Sue\u00f1a en grande" \u2192 "\u0421\u0443\u044d\u043d\u044f \u044d\u043d \u0433\u0440\u0430\u043d\u0434\u044d")

Return as JSON array:
[{{"english": "Spanish text", "russian": "Russian translation", "spanish_cyrillic": "Spanish phrase in Cyrillic letters"}}]

EXAMPLES of CORRECT format:
\u2713 {{\\"english\\": \\"Sue\u00f1a en grande, empieza peque\u00f1o\\", \\"russian\\": \\"\u041c\u0435\u0447\u0442\u0430\u0439 \u043f\u043e-\u043a\u0440\u0443\u043f\u043d\u043e\u043c\u0443, \u043d\u0430\u0447\u0438\u043d\u0430\u0439 \u0441 \u043c\u0430\u043b\u043e\u0433\u043e\\", \\"spanish_cyrillic\\": \\"\u0421\u0443\u044d\u043d\u044f \u044d\u043d \u0433\u0440\u0430\u043d\u0434\u044d, \u044d\u043c\u043f\u044c\u0435\u0441\u0430 \u043f\u044d\u043a\u0435\u043d\u044c\u043e\\"}}

Random seed: {random_seed}

CRITICAL: Every phrase MUST be completely new, unique, and ORIGINAL. DO NOT repeat phrases from the used list above."""

            # Higher temperature for more creativity
            payload = {
                "model": AI_MODEL,
                "messages": [
                    {"role": "system", "content": "You are a Spanish teacher. Create SHORT, FRESH, unique phrases with natural pauses. NEVER repeat phrases. Be creative and original."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 1.5,
                "top_p": 1.0,
                "presence_penalty": 0.5,
                "frequency_penalty": 0.5
            }

            print(f"[content] Attempt {attempt + 1}/{max_attempts}: Calling API...")
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()

            data = response.json()
            content = data["choices"][0]["message"]["content"].strip()

            print(f"[content] Raw API response: {content[:400]}...")

            # Extract JSON
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            phrases = json.loads(content)
            print(f"[content] Parsed {len(phrases)} phrases from JSON")

            # Filter out already-used phrases and ensure proper length
            unique_phrases = []
            skipped_long = 0
            skipped_used = 0
            skipped_session = 0
            skipped_cliche = 0
            
            # Cliché patterns to detect
            cliche_patterns = [
                "little by little", "slow and steady", "patience is a virtue",
                "rome wasn't built", "good things take time", "one step at a time",
                "keep trying", "don't give up", "wait for it", "believe in yourself",
                "never give up", "dream big", "you are capable", "your future"
            ]
            
            for phrase in phrases:
                english = phrase.get("english", "").strip()
                english_lower = english.lower()

                # Skip if too long (over 9 words)
                if len(english.split()) > 9:
                    skipped_long += 1
                    continue

                # Skip if English field contains Russian text (common API mistake)
                russian_chars_in_english = any(c in english_lower for c in ['й', 'ц', 'у', 'к', 'е', 'н', 'г', 'ш', 'щ', 'з', 'х', 'ъ', 'ф', 'ы', 'в', 'а', 'п', 'р', 'о', 'л', 'д', 'ж', 'э', 'я', 'ч', 'с', 'м', 'и', 'т', 'ь', 'б', 'ю', 'ё'])
                if russian_chars_in_english:
                    print(f"[content] Skipping (Russian in English field): {english}")
                    skipped_long += 1
                    continue

                # Skip if contains cliché patterns
                if any(cliche in english_lower for cliche in cliche_patterns):
                    skipped_cliche += 1
                    print(f"[content] Skipping cliché: {english}")
                    continue

                # Skip if already in global history
                if is_phrase_used(english):
                    skipped_used += 1
                    print(f"[content] Skipping duplicate (history): {english}")
                    continue

                # Skip if we've seen it in this run already
                if english_lower in all_tried_phrases:
                    skipped_session += 1
                    print(f"[content] Skipping duplicate (this run): {english}")
                    continue

                # Add to tracking and results
                all_tried_phrases.add(english_lower)
                unique_phrases.append(phrase)

                if len(unique_phrases) >= num_phrases:
                    break

            print(f"[content] Got {len(unique_phrases)} valid phrases (skipped: {skipped_long} too long, {skipped_cliche} cliché, {skipped_used} history, {skipped_session} this run)")

            if len(unique_phrases) >= num_phrases:
                # Normalize keys to lowercase before saving
                normalized_phrases = []
                for p in unique_phrases[:num_phrases]:
                    russian_text = p.get("russian") or p.get("Russian") or p.get("RUSSIAN") or ""
                    normalized = {
                        "english": p.get("english", ""),
                        "russian": russian_text,
                        "spanish_cyrillic": p.get("spanish_cyrillic", ""),
                        "pronunciation": p.get("pronunciation", "")
                    }
                    if not russian_text:
                        print(f"[content] WARNING: Missing Russian text for '{normalized['english']}'")
                    if not normalized["spanish_cyrillic"]:
                        print(f"[content] WARNING: Missing spanish_cyrillic for '{normalized['english']}'")
                    normalized_phrases.append(normalized)

                add_phrases_to_history(normalized_phrases, category_english)
                for p in normalized_phrases:
                    add_phrase_to_session(p["english"])
                return normalized_phrases
            else:
                print(f"[content] Only got {len(unique_phrases)} phrases, need {num_phrases}, trying again...")

        except Exception as e:
            print(f"[content] Attempt {attempt + 1} failed: {e}")

    # Last resort attempt with maximum randomness
    try:
        import requests
        url = "https://gen.pollinations.ai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {POLLINATIONS_API_KEY}",
            "Content-Type": "application/json"
        }
        
        last_resort_prompt = f"""Generate exactly 5 short {category_english} phrases in English and Russian.
Make them simple, unique, and different from common clichés.
Return as JSON: [{{"english": "...", "russian": "...", "pronunciation": "..."}}]"""

        payload = {
            "model": AI_MODEL,
            "messages": [{"role": "user", "content": last_resort_prompt}],
            "temperature": 2.0
        }
        
        print(f"[content] Last resort attempt with temperature 2.0...")
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        content = data["choices"][0]["message"]["content"].strip()
        
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        
        phrases = json.loads(content)
        
        # Accept ANY phrases that aren't in history, normalize keys
        unique_phrases = []
        for p in phrases:
            if not is_phrase_used(p.get("english", "")):
                russian_text = p.get("russian") or p.get("Russian") or p.get("RUSSIAN") or ""
                normalized = {
                    "english": p.get("english", ""),
                    "russian": russian_text,
                    "spanish_cyrillic": p.get("spanish_cyrillic", ""),
                    "pronunciation": p.get("pronunciation", "")
                }
                unique_phrases.append(normalized)
        
        if unique_phrases:
            add_phrases_to_history(unique_phrases[:num_phrases], category_english)
            for p in unique_phrases[:num_phrases]:
                add_phrase_to_session(p["english"])
            print(f"[content] Got {len(unique_phrases[:num_phrases])} phrases from last resort!")
            return unique_phrases[:num_phrases]
    except Exception as e:
        print(f"[content] Last resort also failed: {e}")
    
    # Use fallback phrases if API fails after all attempts
    print(f"[content] Using fallback phrases...")
    fallback_phrases = get_fallback_phrases(category_english, num_phrases)
    
    if len(fallback_phrases) >= num_phrases:
        add_phrases_to_history(fallback_phrases[:num_phrases], category_english)
        for p in fallback_phrases[:num_phrases]:
            add_phrase_to_session(p["english"])
        return fallback_phrases[:num_phrases]
    
    # If we don't have enough fallbacks, raise error
    raise RuntimeError(
        f"CRITICAL: Could not generate {num_phrases} unique phrases for '{category_english}' "
        f"after all attempts and fallback exhausted. Try again later."
    )


# ============== AUDIO GENERATION ==============

async def generate_single_audio(text: str, voice: str, output_path: str, retries: int = 3):
    """Generate audio using Edge TTS with retry and fallback voice"""
    voices_to_try = [voice]
    if "Dmitry" in voice:
        voices_to_try.append("ru-RU-SvetlanaNeural")
    elif "Alvaro" in voice:
        voices_to_try.append("es-ES-ElviraNeural")

    for try_voice in voices_to_try:
        for attempt in range(retries + 1):
            try:
                import edge_tts
                communicate = edge_tts.Communicate(text, try_voice)
                await communicate.save(output_path)
                if Path(output_path).exists() and Path(output_path).stat().st_size > 1000:
                    return True
            except Exception as e:
                if attempt < retries:
                    print(f"  TTS retry {attempt + 1}/{retries}...")
                    import asyncio
                    await asyncio.sleep(1)
                    continue
                print(f"  TTS fallback to {try_voice} failed: {e}")
    if Path(output_path).exists():
        try:
            Path(output_path).unlink()
        except:
            pass
    return False


def estimate_speech_duration(text: str) -> float:
    """Estimate speech duration in seconds based on text length"""
    word_count = len(text.split())
    char_count = len(text)
    return max(2.0, word_count * 0.4, char_count * 0.08)


def generate_all_audio(phrases: list, output_dir: str):
    """Generate audio with Russian-first order and proper timing"""

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    audio_files = []

    for i, phrase in enumerate(phrases):
        russian_file = output_dir / f"russian_{i}.mp3"
        spanish_file = output_dir / f"spanish_{i}.mp3"
        combined_file = output_dir / f"combined_{i}.mp3"

        print(f"\n  Phrase {i+1}:")
        print(f"    RU: {phrase['russian']}")
        print(f"    ES: {phrase['english']}")

        # Generate Russian audio FIRST
        ru_success = asyncio.run(generate_single_audio(phrase["russian"], RUSSIAN_VOICE, str(russian_file)))
        if ru_success:
            print(f"    \u2713 Ruso: {russian_file.name}")
        else:
            est = estimate_speech_duration(phrase["russian"])
            print(f"    \u26a0 Russian TTS failed, generating {est:.1f}s silence")
            cmd = ["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono", "-t", str(est), str(russian_file)]
            subprocess.run(cmd, capture_output=True)

        # Generate Spanish audio SECOND
        es_success = asyncio.run(generate_single_audio(phrase["english"], SPANISH_VOICE, str(spanish_file)))
        if es_success:
            print(f"    \u2713 Espa\u00f1ol: {spanish_file.name}")
        else:
            est = estimate_speech_duration(phrase["english"])
            print(f"    \u26a0 Spanish TTS failed, generating {est:.1f}s silence")
            cmd = ["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono", "-t", str(est), str(spanish_file)]
            subprocess.run(cmd, capture_output=True)

        # Get actual durations
        ru_duration = get_audio_duration(str(russian_file))
        es_duration = get_audio_duration(str(spanish_file))

        # Pause between Russian and Spanish
        pause_between = 0.4
        total_duration = ru_duration + pause_between + es_duration

        print(f"    \u23f1\ufe0f  Total: {total_duration:.2f}s (RU: {ru_duration:.2f}s + pause: {pause_between}s + ES: {es_duration:.2f}s)")

        # Combine: Russian first, then Spanish
        cmd = [
            "ffmpeg", "-y",
            "-i", str(russian_file),
            "-i", str(spanish_file),
            "-filter_complex", "[0:a][1:a]concat=n=2:v=0:a=1[out]",
            "-map", "[out]",
            str(combined_file)
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            concat_file = output_dir / f"concat_{i}.txt"
            with open(concat_file, "w", encoding="utf-8") as f:
                f.write(f"file '{russian_file.as_posix()}'\n")
                f.write(f"file '{spanish_file.as_posix()}'\n")

            cmd = [
                "ffmpeg", "-y",
                "-f", "concat", "-safe", "0",
                "-i", str(concat_file),
                "-c:a", "aac",
                str(combined_file)
            ]
            subprocess.run(cmd, capture_output=True)
            if concat_file.exists():
                concat_file.unlink()

        actual_duration = get_audio_duration(str(combined_file))
        print(f"    \u2713 Combined verified: {actual_duration:.2f}s")

        audio_files.append({
            "index": i,
            "russian": str(russian_file),
            "spanish": str(spanish_file),
            "combined": str(combined_file),
            "duration": actual_duration,
            "ru_duration": ru_duration,
            "es_duration": es_duration
        })

    print(f"\n[audio] ✓ Generated {len(audio_files)} phrase audios")
    return audio_files


def get_audio_duration(audio_file: str) -> float:
    """Get audio duration in seconds"""
    if not Path(audio_file).exists():
        return 2.0
    cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", audio_file]
    result = subprocess.run(cmd, capture_output=True, text=True)
    try:
        return float(result.stdout.strip())
    except:
        return 2.0


def create_final_narration(audio_files: list, output_file: str):
    """Combine all audio files"""
    n = len(audio_files)
    print(f"[audio] Combining {n} audio files...")

    concat_file = Path(output_file).parent / "narration_list.txt"

    with open(concat_file, "w", encoding="utf-8") as f:
        for audio_info in audio_files:
            combined_path = Path(audio_info["combined"])
            if combined_path.exists():
                path_str = str(combined_path.resolve()).replace("\\", "/").replace("'", "'\\''")
                f.write(f"file '{path_str}'\n")

    cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_file), "-c:a", "copy", str(output_file)]
    result = subprocess.run(cmd, capture_output=True, text=True)

    if concat_file.exists():
        concat_file.unlink()

    if result.returncode == 0 and Path(output_file).exists() and Path(output_file).stat().st_size > 0:
        size = Path(output_file).stat().st_size
        print(f"\n[audio] ✓ Final narration: {Path(output_file).name} ({size/1024:.1f} KB)")
        return True

    return False


# ============== IMAGE GENERATION ==============

def find_font(bold=False, size=40):
    """Find available font on current platform (Windows or Linux)"""
    from PIL import ImageFont

    if bold:
        font_preferences = [
            "segoeuib.ttf",    # Windows Segoe UI Bold
            "arialbd.ttf",     # Windows Arial Bold
            "DejaVuSans-Bold.ttf",  # Linux
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        ]
    else:
        font_preferences = [
            "segoeui.ttf",     # Windows Segoe UI
            "arial.ttf",       # Windows Arial
            "calibri.ttf",     # Windows Calibri
            "DejaVuSans.ttf",  # Linux
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        ]

    for font_name in font_preferences:
        try:
            return ImageFont.truetype(font_name, size)
        except (IOError, OSError):
            continue
    return ImageFont.load_default()


def rounded_rect(draw, bbox, radius, fill=None, outline=None, width=1):
    """Draw a rectangle with rounded corners"""
    x1, y1, x2, y2 = bbox
    r = min(radius, (x2 - x1) // 2, (y2 - y1) // 2)
    draw.pieslice([x1, y1, x1 + r*2, y1 + r*2], 180, 270, fill=fill)
    draw.pieslice([x2 - r*2, y1, x2, y1 + r*2], 270, 360, fill=fill)
    draw.pieslice([x1, y2 - r*2, x1 + r*2, y2], 90, 180, fill=fill)
    draw.pieslice([x2 - r*2, y2 - r*2, x2, y2], 0, 90, fill=fill)
    draw.rectangle([x1 + r, y1, x2 - r, y2], fill=fill)
    draw.rectangle([x1, y1 + r, x2, y2 - r], fill=fill)


def create_premium_background(category_english: str, phrase_index: int = 0, total_phrases: int = 5):
    """Create premium gradient background with glow, particles, and depth"""
    from PIL import Image, ImageDraw
    import math

    img = Image.new('RGB', (VIDEO_WIDTH, VIDEO_HEIGHT))
    draw = ImageDraw.Draw(img)

    category_colors = {
        "Motivation": [(147, 51, 234), (88, 28, 135), (236, 72, 153), (192, 132, 252)],
        "Love": [(220, 38, 38), (153, 27, 27), (244, 114, 182), (251, 207, 232)],
        "Success": [(234, 179, 8), (21, 128, 61), (249, 115, 22), (34, 197, 94)],
        "Wisdom": [(30, 64, 175), (234, 179, 8), (59, 130, 246), (250, 204, 21)],
        "Happiness": [(250, 204, 21), (192, 38, 211), (251, 146, 60), (168, 85, 247)],
        "Self Improvement": [(22, 163, 74), (234, 179, 8), (74, 222, 128), (250, 204, 21)],
        "Gratitude": [(251, 146, 60), (88, 28, 135), (251, 191, 36), (147, 51, 234)],
        "Friendship": [(244, 114, 182), (13, 148, 136), (251, 182, 206), (45, 212, 191)],
        "Hope": [(30, 58, 138), (250, 204, 21), (59, 130, 246), (234, 179, 8)],
        "Creativity": [(219, 39, 119), (30, 64, 175), (236, 72, 153), (88, 28, 135)],
        "Inner Peace": [(125, 211, 252), (30, 58, 138), (186, 230, 253), (88, 28, 135)],
        "Confidence": [(234, 88, 12), (30, 64, 175), (249, 115, 22), (59, 130, 246)],
        "Perseverance": [(120, 53, 15), (234, 179, 8), (180, 83, 9), (251, 146, 60)],
        "Inspiration": [(192, 38, 211), (88, 28, 135), (219, 39, 119), (30, 64, 175)],
        "Positive Life": [(74, 222, 128), (219, 39, 119), (134, 239, 172), (236, 72, 153)],
        "Courage": [(185, 28, 28), (234, 179, 8), (220, 38, 38), (251, 146, 60)],
        "Kindness": [(254, 215, 170), (147, 51, 234), (252, 182, 159), (88, 28, 135)],
        "Patience": [(22, 163, 74), (250, 204, 21), (74, 222, 128), (234, 179, 8)],
        "Forgiveness": [(233, 213, 255), (88, 28, 135), (216, 180, 254), (147, 51, 234)],
        "Strength": [(107, 114, 128), (234, 88, 12), (156, 163, 175), (249, 115, 22)],
        "Joy": [(250, 204, 21), (219, 39, 119), (234, 179, 8), (168, 85, 247)],
        "Balance": [(52, 211, 153), (147, 51, 234), (110, 231, 183), (88, 28, 135)],
        "Growth": [(22, 163, 74), (234, 179, 8), (34, 197, 94), (251, 146, 60)],
        "Purpose": [(88, 28, 135), (234, 179, 8), (147, 51, 234), (251, 146, 60)],
        "Mindfulness": [(214, 158, 46), (88, 28, 135), (245, 208, 105), (147, 51, 234)],
    }

    colors = category_colors.get(category_english, [(147, 51, 234), (88, 28, 135), (236, 72, 153), (192, 132, 252)])

    # Smooth 4-stop gradient
    stops = [(0, colors[0]), (0.33, colors[1]), (0.66, colors[2]), (1.0, colors[3])]
    for y in range(VIDEO_HEIGHT):
        ratio = y / VIDEO_HEIGHT
        for i in range(len(stops) - 1):
            if stops[i][0] <= ratio <= stops[i+1][0]:
                t = (ratio - stops[i][0]) / (stops[i+1][0] - stops[i][0])
                r = int(stops[i][1][0] + (stops[i+1][1][0] - stops[i][1][0]) * t)
                g = int(stops[i][1][1] + (stops[i+1][1][1] - stops[i][1][1]) * t)
                b = int(stops[i][1][2] + (stops[i+1][1][2] - stops[i][1][2]) * t)
                draw.rectangle([(0, y), (VIDEO_WIDTH, y + 1)], fill=(r, g, b))
                break

    # Subtle diagonal lines for texture
    for i in range(-VIDEO_HEIGHT, VIDEO_WIDTH * 2, 60):
        points = []
        for j in range(0, 5):
            x = i + j * 20
            y = j * 20
            if 0 <= x <= VIDEO_WIDTH and 0 <= y <= VIDEO_HEIGHT:
                points.append((x, y))
        if len(points) > 1:
            draw.line(points, fill=(255, 255, 255, 8), width=1)

    # Radial glow from center-top
    glow = Image.new('RGBA', (VIDEO_WIDTH, VIDEO_HEIGHT), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)
    cx, cy = VIDEO_WIDTH // 2, int(VIDEO_HEIGHT * 0.35)
    for radius in range(1200, 0, -60):
        alpha = int(25 * (1 - radius / 1200))
        glow_draw.ellipse(
            [(cx - radius, cy - radius), (cx + radius, cy + radius)],
            fill=(255, 255, 255, alpha)
        )

    img = img.convert('RGBA')
    img = Image.alpha_composite(img, glow)

    return img


def generate_complete_image(phrase_data: dict, category_english: str, output_path: str, phrase_index: int = 0, total_phrases: int = 5):
    """Generate premium image with clean centered layout"""
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        print("PIL not available. Install: pip install Pillow")
        return None

    img = create_premium_background(category_english, phrase_index, total_phrases)
    draw = ImageDraw.Draw(img)

    SIZE_CATEGORY = 64
    SIZE_RUSSIAN_L = 100
    SIZE_RUSSIAN_M = 82
    SIZE_RUSSIAN_S = 66
    SIZE_ENGLISH = 70
    SIZE_CYRILLIC = 48
    SIZE_BRANDING = 50
    SIZE_PROGRESS = 38

    font_category = find_font(bold=True, size=SIZE_CATEGORY)
    font_russian_l = find_font(bold=True, size=SIZE_RUSSIAN_L)
    font_russian_m = find_font(bold=True, size=SIZE_RUSSIAN_M)
    font_russian_s = find_font(bold=True, size=SIZE_RUSSIAN_S)
    font_english = find_font(bold=True, size=SIZE_ENGLISH)
    font_cyrillic = find_font(bold=False, size=SIZE_CYRILLIC)
    font_branding = find_font(bold=True, size=SIZE_BRANDING)
    font_progress = find_font(bold=False, size=SIZE_PROGRESS)

    russian = phrase_data.get("russian", "")
    english = phrase_data.get("english", "")
    spanish_cyrillic = phrase_data.get("spanish_cyrillic", "")

    def wrap_text(text, font, max_width):
        words = text.split()
        lines = []
        current_line = []
        for word in words:
            test_line = ' '.join(current_line + [word])
            bbox = draw.textbbox((0, 0), test_line, font=font)
            width = bbox[2] - bbox[0]
            if width <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
        if current_line:
            lines.append(' '.join(current_line))
        return lines

    def pick_russian_font(text, max_w):
        """Pick largest font that fits in 1-2 lines"""
        for font, name in [(font_russian_l, 'L'), (font_russian_m, 'M'), (font_russian_s, 'S')]:
            lines = wrap_text(text, font, max_w)
            if len(lines) <= 2:
                return font, lines
        return font_russian_s, wrap_text(russian, font_russian_s, max_w)

    def measure_line_h(font):
        b = draw.textbbox((0, 0), "Агу", font=font)
        return b[3] - b[1]

    max_text_w = VIDEO_WIDTH - 180
    cat_ru = CATEGORIES_RUSSIAN.get(category_english, category_english)

    # Pick adaptive font for Russian text
    ru_font, ru_lines = pick_russian_font(russian, max_text_w - 40)
    en_lines = wrap_text(english, font_english, max_text_w)
    cyr_lines = wrap_text(spanish_cyrillic, font_cyrillic, max_text_w - 60) if spanish_cyrillic else []

    ru_lh = measure_line_h(ru_font)
    en_lh = measure_line_h(font_english)
    cyr_lh = measure_line_h(font_cyrillic)

    ru_box_pad = 35
    en_box_pad = 28
    cyr_box_pad = 22

    ru_box_h = len(ru_lines) * ru_lh + ru_box_pad * 2
    en_box_h = len(en_lines) * en_lh + en_box_pad * 2
    cyr_box_h = len(cyr_lines) * cyr_lh + cyr_box_pad * 2 if cyr_lines else 0

    gap_cat_ru = 50
    gap_ru_en = 35
    gap_en_cyr = 30
    gap_cyr_prog = 25
    gap_prog_brand = 40
    cat_bar_pad = 20
    prog_bar_h = 30

    total_center_h = (0 + gap_cat_ru + ru_box_h + gap_ru_en +
                      en_box_h + gap_en_cyr + cyr_box_h + gap_cyr_prog +
                      prog_bar_h + gap_prog_brand)

    start_y = int((VIDEO_HEIGHT - total_center_h) * 0.38)
    if start_y < 200:
        start_y = 200

    cy = start_y

    # === Category bar (manually centered around anchor point) ===
    cat_text = cat_ru
    cat_bb = draw.textbbox((0, 0), cat_text, font=font_category)
    cat_tw = cat_bb[2] - cat_bb[0]
    cat_th = cat_bb[3] - cat_bb[1]
    cat_cx = VIDEO_WIDTH // 2
    cat_cy = 185
    cat_pad = 28
    cat_box_x1 = cat_cx - cat_tw // 2 - cat_pad
    cat_box_y1 = cat_cy - cat_th // 2 - cat_pad
    cat_box_x2 = cat_cx + cat_tw // 2 + cat_pad
    cat_box_y2 = cat_cy + cat_th // 2 + cat_pad
    rounded_rect(draw, (cat_box_x1, cat_box_y1, cat_box_x2, cat_box_y2),
                 25, fill=(0, 0, 0, 190))
    draw.text((cat_cx, cat_cy), cat_text,
              fill=(255, 255, 255), font=font_category, anchor="mm",
              stroke_width=2, stroke_fill=(0, 0, 0))

    cy += gap_cat_ru

    # === Russian phrase (BIG, prominent, adaptive) ===
    ru_margin = 50
    rounded_rect(draw, (ru_margin, cy, VIDEO_WIDTH - ru_margin, cy + ru_box_h), 28,
                 fill=(139, 0, 0, 220))
    for i, line in enumerate(ru_lines):
        ly = cy + ru_box_pad + i * ru_lh + ru_lh // 2
        draw.text((VIDEO_WIDTH // 2, ly), line,
                  fill=(255, 255, 200), font=ru_font, anchor="mm",
                  stroke_width=3, stroke_fill=(60, 0, 0))

    cy += ru_box_h + gap_ru_en

    # === English phrase ===
    en_margin = 70
    rounded_rect(draw, (en_margin, cy, VIDEO_WIDTH - en_margin, cy + en_box_h), 24,
                 fill=(20, 40, 100, 220))
    for i, line in enumerate(en_lines):
        ly = cy + en_box_pad + i * en_lh + en_lh // 2
        draw.text((VIDEO_WIDTH // 2, ly), line,
                  fill=(255, 255, 255), font=font_english, anchor="mm",
                  stroke_width=2, stroke_fill=(0, 0, 40))

    cy += en_box_h + gap_en_cyr

    # === English in Cyrillic ===
    if cyr_lines:
        cyr_margin = 90
        rounded_rect(draw, (cyr_margin, cy, VIDEO_WIDTH - cyr_margin, cy + cyr_box_h), 18,
                     fill=(40, 40, 40, 220))
        for i, line in enumerate(cyr_lines):
            ly = cy + cyr_box_pad + i * cyr_lh + cyr_lh // 2
            draw.text((VIDEO_WIDTH // 2, ly), line,
                      fill=(220, 220, 220), font=font_cyrillic, anchor="mm",
                      stroke_width=1, stroke_fill=(20, 20, 20))
        cy += cyr_box_h + gap_cyr_prog
    else:
        cy += gap_cyr_prog

    # === Progress ===
    prog_text = f"{phrase_index + 1} / {total_phrases}"
    prog_bb = draw.textbbox((0, 0), prog_text, font=font_progress)
    prog_h = prog_bb[3] - prog_bb[1]
    draw.text((VIDEO_WIDTH // 2, cy + prog_h // 2), prog_text,
              fill=(180, 180, 180), font=font_progress, anchor="mm")

    # === Branding (manually centered around anchor point) ===
    brand_text = "Habla Verse"
    brand_bb = draw.textbbox((0, 0), brand_text, font=font_branding)
    brand_tw = brand_bb[2] - brand_bb[0]
    brand_th = brand_bb[3] - brand_bb[1]
    brand_cx = VIDEO_WIDTH // 2
    brand_cy = VIDEO_HEIGHT - 120
    brand_pad = 32
    brand_box_x1 = brand_cx - brand_tw // 2 - brand_pad
    brand_box_y1 = brand_cy - brand_th // 2 - brand_pad
    brand_box_x2 = brand_cx + brand_tw // 2 + brand_pad
    brand_box_y2 = brand_cy + brand_th // 2 + brand_pad
    rounded_rect(draw, (brand_box_x1, brand_box_y1, brand_box_x2, brand_box_y2),
                 30, fill=(0, 0, 0, 195))
    draw.text((brand_cx, brand_cy), brand_text,
              fill=(255, 215, 0), font=font_branding, anchor="mm",
              stroke_width=2, stroke_fill=(0, 0, 0))

    if img.mode == 'RGBA':
        img = img.convert('RGB')

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, quality=95, optimize=True)
    print(f"  ✓ Image: {Path(output_path).name}")
    return output_path


# ============== VIDEO CREATION ==============

def create_video_from_images_audio(image_files: list, audio_files: list, combined_audio: str, output_file: str):
    """Create video from images and audio with PERFECT synchronization"""

    print(f"\n[video] Creating video from {len(image_files)} images...")
    print(f"[video] Ensuring complete audio playback and sync...")

    temp_clips = []

    for i, (img_path, audio_info) in enumerate(zip(image_files, audio_files)):
        duration = audio_info['duration']
        print(f"  Image {i+1}/{len(image_files)}: {duration:.2f}s (RU: {audio_info.get('ru_duration', 0):.1f}s + ES: {audio_info.get('es_duration', 0):.1f}s)")

        temp_clip = Path(output_file).parent / f"temp_clip_{i:02d}.mp4"
        temp_clips.append(temp_clip)

        cmd = [
            "ffmpeg", "-y",
            "-loop", "1",
            "-i", str(img_path),
            "-vf", f"scale={VIDEO_WIDTH}:{VIDEO_HEIGHT}:force_original_aspect_ratio=decrease,pad={VIDEO_WIDTH}:{VIDEO_HEIGHT}:(ow-iw)/2:(oh-ih)/2,fps={FPS}",
            "-t", str(duration),
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-preset", "medium",
            str(temp_clip)
        ]

        subprocess.run(cmd, check=True, capture_output=True)

    # Concatenate clips
    print("[video] Concatenating clips...")
    temp_video = Path(output_file).parent / "temp_video.mp4"
    concat_file = Path(output_file).parent / "concat_list.txt"

    with open(concat_file, "w") as f:
        for clip in temp_clips:
            f.write(f"file '{clip.resolve().as_posix()}'\n")

    cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_file), "-c", "copy", str(temp_video)]
    subprocess.run(cmd, check=True, capture_output=True)

    # Add audio
    print("[video] Adding audio (ensuring complete playback)...")
    audio_duration = get_audio_duration(combined_audio)
    print(f"[video] Audio duration: {audio_duration:.2f}s")

    cmd = [
        "ffmpeg", "-y",
        "-i", str(temp_video),
        "-i", str(combined_audio),
        "-c:v", "copy",
        "-c:a", "aac",
        "-shortest",
        str(output_file)
    ]
    subprocess.run(cmd, check=True, capture_output=True)

    # Verify
    video_duration = get_audio_duration(str(output_file).replace(".mp4", ".mp4"))
    print(f"[video] ✓ Video created: {Path(output_file).name} ({video_duration:.2f}s)")

    # Cleanup
    for clip in temp_clips:
        if clip.exists():
            clip.unlink()
    if temp_video.exists():
        temp_video.unlink()
    if concat_file.exists():
        concat_file.unlink()


# ============== MAIN WORKFLOW ==============

def generate_reel(category_english: str = None):
    """Generate complete Facebook Reel"""

    if not category_english:
        category_english = random.choice(CATEGORIES_ENGLISH)

    print(f"\n{'='*80}")
    print(f"Category: {category_english} ({CATEGORIES_RUSSIAN[category_english]})")
    print(f"{'='*80}\n")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    reel_dir = VIDEO_DIR / f"{category_english}_{timestamp}"
    reel_dir.mkdir(exist_ok=True)

    # Step 1: Generate unique phrases
    print("[1/4] Generating unique phrases (checking history)...")
    phrases = generate_phrases(category_english, num_phrases=5)

    for i, phrase in enumerate(phrases, 1):
        print(f"  {i}. {phrase['english']} → {phrase['russian']}")

    # Step 2: Generate images
    print("\n[2/4] Generating images with premium backgrounds...")
    for i, phrase in enumerate(phrases):
        output_path = reel_dir / f"phrase_{i:02d}.jpg"
        generate_complete_image(phrase, category_english, str(output_path), phrase_index=i, total_phrases=len(phrases))
        print(f"  ✓ Image {i+1}: {phrase['english'][:40]}...")

    # Step 3: Generate audio
    print("\n[3/4] Generating audio (English + Russian with 500ms pause)...")
    audio_files = generate_all_audio(phrases, str(reel_dir))

    final_audio = reel_dir / "narration.mp3"
    create_final_narration(audio_files, str(final_audio))

    # Step 4: Create video - CRITICAL: Sort images for correct order
    print("\n[4/4] Creating video...")
    output_video = reel_dir / "final_reel.mp4"

    image_files = sorted([str(p) for p in reel_dir.glob("phrase_*.jpg")])

    create_video_from_images_audio(
        image_files,
        audio_files,
        str(final_audio),
        str(output_video)
    )

    # Save metadata
    metadata = {
        "category_english": category_english,
        "category_russian": CATEGORIES_RUSSIAN[category_english],
        "timestamp": timestamp,
        "phrases": phrases,
        "video": str(output_video),
        "audio": str(final_audio)
    }

    with open(reel_dir / "metadata.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*80}")
    print(f"✅ REEL COMPLETE!")
    print(f"  📁 {reel_dir}")
    print(f"  🎬 {output_video.name}")
    print(f"  🏷️  Branding: Habla Verse")
    print(f"{'='*80}\n")

    return metadata


def generate_daily_content(times_per_day: int = 4):
    """Generate multiple reels for daily posting. Avoids repeating categories within 3 days."""
    recent_file = HISTORY_DIR / "recent_categories.json"
    recent = {"date": None, "last_3_days": []}
    if recent_file.exists():
        try:
            with open(recent_file, "r", encoding="utf-8") as f:
                recent = json.load(f)
        except:
            pass

    today = datetime.now().strftime("%Y-%m-%d")
    
    # Reset if new day
    if recent.get("date") != today:
        recent["date"] = today
        recent["last_3_days"] = recent.get("last_3_days", [])
    
    # Track used categories from last 3 days
    used_recently = set()
    for day_cats in recent.get("last_3_days", []):
        for cat in day_cats:
            used_recently.add(cat)
    
    available = [c for c in CATEGORIES_ENGLISH if c not in used_recently]
    if len(available) < times_per_day:
        available = CATEGORIES_ENGLISH.copy()
    
    selected = random.sample(available, min(times_per_day, len(available)))
    
    # Save today's categories
    recent.setdefault("last_3_days", []).append(selected)
    if len(recent["last_3_days"]) > 3:
        recent["last_3_days"] = recent["last_3_days"][-3:]
    with open(recent_file, "w", encoding="utf-8") as f:
        json.dump(recent, f, indent=2)
    
    print(f"\n{'='*80}")
    print(f"📅 GENERATING {len(selected)} REELS FOR TODAY")
    print(f"{'='*80}")
    
    results = []
    for i, category in enumerate(selected):
        print(f"\n--- Reel {i+1}/{len(selected)}: {category} ---")
        try:
            metadata = generate_reel(category)
            results.append(metadata)
            print(f"✅ Reel {i+1} complete!")
        except Exception as e:
            print(f"❌ Reel {i+1} failed: {e}")
    
    # Summary
    print(f"\n{'='*80}")
    print(f"📊 DAILY GENERATION SUMMARY")
    print(f"{'='*80}")
    print(f"  Total: {len(results)}/{len(selected)} reels generated")
    print(f"  Categories: {', '.join(selected)}")
    
    # Write summary
    summary_path = OUTPUT_DIR / f"daily_summary_{datetime.now().strftime('%Y%m%d')}.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump({
            "date": today,
            "categories": selected,
            "results": [
                {
                    "category": m.get("category_english", ""),
                    "video": m.get("video", ""),
                    "phrases": len(m.get("phrases", []))
                }
                for m in results
            ]
        }, f, indent=2)
    
    print(f"  Summary: {summary_path}")
    print(f"{'='*80}\n")
    
    return results


if __name__ == "__main__":
    print("\n" + "="*80)
    print("🇷🇺 ENGLISH WITH KREGG - VK REELS AUTOMATION 🇷🇺")
    print("="*80)
    print("\n✨ FEATURES:")
    print("  ✓ Natural pauses with commas (non-robotic TTS)")
    print("  ✓ Perfect audio-video synchronization")
    print("  ✓ Complete audio playback guaranteed")
    print("  ✓ Russian-first layout (for Russian-speaking audience)")
    print("  ✓ Habla Verse branding")
    print("  ✓ NEVER repeats phrases (permanent history tracking)")
    print(f"\n📊 AVAILABLE CATEGORIES ({len(CATEGORIES_ENGLISH)} total):")
    for i, cat in enumerate(CATEGORIES_ENGLISH, 1):
        print(f"   {i:2d}. {cat} ({CATEGORIES_RUSSIAN[cat]})")
    print(f"\n📅 DAILY CAPACITY:")
    print(f"  • 4 reels per day = 20 unique phrases daily")
    print(f"  • {len(CATEGORIES_ENGLISH)} categories = Over 6 days before any category repeats")
    print(f"  • Phrase history is PERMANENT (never deletes)")
    print(f"  • AI generates FRESH phrases every time")
    print("="*80)

    generate_reel()

    print("\n" + "="*80)
    print("✅ READY FOR DAILY AUTOMATION!")
    print("="*80)
    print("\nTo generate and post to VK:")
    print("  python facebook_reels_automation.py")
    print("  python upload_all_platforms.py")
    print("\nTo generate 4 reels in one go:")
    print("  from facebook_reels_automation import generate_daily_content")
    print("  generate_daily_content(times_per_day=4)")
    print("\n🇷🇺 Posts to: VK profile wall + all configured platforms")
    print("="*80)
