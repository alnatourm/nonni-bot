from .ai import ai_provider
from .config import settings
from .database import get_history
from .memory import (
    detect_language,
    get_user_memory_context,
)


BASE_PROMPT_AR = """
أنت نوني، مساعد ذكاء اصطناعي متقدم.

أنت مساعد عام قوي ومتخصص في:
- البرمجة والتطوير
- الأعمال وريادة الأعمال
- التسويق
- تحليل المشاريع
- التكنولوجيا والذكاء الاصطناعي
- الطبخ
- المعرفة العامة
- العلوم الإسلامية

قواعدك:
- أجب بالعربية إذا كان المستخدم يكتب بالعربية.
- أجب بالإنجليزية إذا كان المستخدم يكتب بالإنجليزية.
- كن دقيقًا ولا تخترع معلومات.
- إذا لم تكن متأكدًا، قل ذلك بوضوح.
- لا تدّعي أنك استخدمت أداة لم تستخدمها.
- لا تدّعي أنك بحثت في الإنترنت إذا لم يتم إجراء بحث.
"""


BASE_PROMPT_EN = """
You are Nonni, an advanced AI assistant.

You are highly capable in:
- Programming and software development
- Business and entrepreneurship
- Marketing
- Project analysis
- Technology and AI
- Cooking
- General knowledge
- Islamic knowledge

Rules:
- Reply in Arabic when the user writes Arabic.
- Reply in English when the user writes English.
- Be accurate and do not invent facts.
- If uncertain, clearly say so.
- Never claim to have used a tool that was not actually used.
- Never claim to have searched the web unless a real search was performed.
"""


def detect_intent(text: str) -> str:
    value = text.lower()

    coding_words = [
        "python", "javascript", "typescript", "php", "laravel",
        "react", "flutter", "api", "code", "coding", "bug", "error",
        "function", "class", "database", "sql", "git",
        "برمجة", "كود", "بايثون", "لارافيل", "خطأ", "دالة",
    ]

    business_words = [
        "business", "startup", "marketing", "sales", "market",
        "investment", "company", "revenue", "profit", "strategy",
        "مشروع", "شركة", "تسويق", "مبيعات", "استثمار", "سوق", "ربح",
    ]

    crypto_words = [
        "bitcoin", "ethereum", "crypto", "blockchain", "defi",
        "token", "nft", "trading", "binance",
        "عملة رقمية", "بتكوين", "بلوكتشين", "تداول",
    ]

    cooking_words = [
        "recipe", "cook", "cooking", "food", "meal", "ingredient",
        "وصفة", "طبخ", "طبخة", "طعام", "أكل", "مقادير",
    ]

    islamic_words = [
        "quran", "hadith", "islam", "islamic", "prayer", "fiqh",
        "قرآن", "حديث", "إسلام", "فقه", "سورة", "صلاة", "دعاء", "آية",
    ]

    if any(word in value for word in coding_words):
        return "coding"
    if any(word in value for word in business_words):
        return "business"
    if any(word in value for word in crypto_words):
        return "crypto"
    if any(word in value for word in cooking_words):
        return "cooking"
    if any(word in value for word in islamic_words):
        return "islamic"

    return "general"


def expert_prompt(intent: str) -> str:
    prompts = {
        "coding": """
You are Nonni Coding Expert.
Give practical, production-quality programming advice.
When providing code, make it complete and explain important implementation decisions.
Consider security, scalability, error handling and maintainability.
""",
        "business": """
You are Nonni Business Expert.
Think like a business strategist.
Analyze market, customers, pricing, competition, revenue and execution.
Clearly separate facts from assumptions.
""",
        "crypto": """
You are Nonni Blockchain and Crypto Expert.
Explain concepts carefully.
When current prices, news or market conditions are required,
do not invent them. They require a real-time data source.
""",
        "cooking": """
You are Nonni Cooking Expert.
Provide practical recipes with ingredients, quantities and steps.
Consider substitutions and cooking time when useful.
""",
        "islamic": """
You are Nonni Islamic Knowledge Expert.
Distinguish between Quran, authentic Hadith, scholarly interpretation and opinion.
Do not fabricate religious citations.
When a matter has legitimate scholarly disagreement, explain that clearly.
""",
        "general": """
You are Nonni General Expert.
Answer clearly, accurately and practically.
""",
    }

    return prompts.get(intent, prompts["general"])


async def generate_response(
    telegram_user_id: int,
    user_text: str,
) -> tuple[str, str]:

    language = detect_language(user_text)
    intent = detect_intent(user_text)

    system_prompt = (
        BASE_PROMPT_AR if language == "ar" else BASE_PROMPT_EN
    )

    system_prompt += "\n\n" + expert_prompt(intent)

    memory = await get_user_memory_context(telegram_user_id)

    if memory:
        system_prompt += "\n\nKnown user memory:\n" + memory

    history = await get_history(
        telegram_user_id,
        settings.max_history,
    )

    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(history)
    messages.append({"role": "user", "content": user_text})

    response = await ai_provider.chat(
        messages=messages,
        temperature=0.7,
        max_tokens=4096,
    )

    return response, intent
