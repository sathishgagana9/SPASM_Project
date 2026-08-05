import json
import os
import re
import sys

sys.path.append(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )
)

from scripts.llm import generate
from domain_fusion import DomainFusion


class UnifiedAnalyzer:
    """
    Replaces 5 separate LLM calls per turn:
        - ContextAnalyzer.analyze()
        - DomainClassifier.classify()
        - RiskAnalyzer.analyze()
        - DependencyAnalyzer.analyze()   (per-turn slice only)
        - NoveltyDetector.detect()       (per-turn slice only)

    with ONE LLM call that returns every field in a single JSON object.

    NOTE on dependency/novelty:
    The old pipeline re-ran DependencyAnalyzer / NoveltyDetector over the
    ENTIRE conversation on every single turn (O(n) work recomputed n times,
    with a growing prompt each time). That is unnecessary: dependency and
    novelty for turns 1..n-1 do not change once computed. This class only
    asks the LLM to judge the CURRENT message against a short window of
    recent history; the engine is responsible for caching/appending the
    per-turn result instead of recomputing history every turn.
    """

    def __init__(self, history_window=3):
        self.domain_fusion = DomainFusion()
        self.history_window = history_window

        self.medical_keywords = [
            "fever", "diabetes", "blood", "pain", "doctor", "medicine",
            "insulin", "headache", "cough", "cold", "infection",
            "heart", "sugar", "bp", "pressure", "hospital", "symptom"
        ]
        self.education_keywords = [
            "study", "teacher", "student", "exam", "school",
            "college", "university", "homework"
        ]
        self.programming_keywords = [
            "python", "java", "c", "cpp", "linked list",
            "array", "stack", "queue", "tree", "algorithm",
            "code", "program", "compiler", "pointer"
        ]
        self.math_keywords = [
            "math", "mathematics", "algebra",
            "calculus", "geometry", "equation",
            "integration", "derivative"
        ]
        self.law_keywords = [
            "court", "law", "legal", "judge",
            "crime", "police", "case", "lawyer"
        ]
        self.travel_keywords = [
            "travel", "trip", "hotel", "flight",
            "visa", "tour", "vacation", "tourism"
        ]
        self.finance_keywords = [
            "loan", "bank", "investment", "stock",
            "money", "salary", "tax", "insurance"
        ]
        self.sports_keywords = [
            "ipl", "cricket", "football", "match", "t20", "odi",
            "world cup", "wicket", "batsman", "bowler", "score",
            "rcb", "csk", "mi", "kkr", "srh", "gt", "rr", "pbks", "lsg"
        ]
        self.cooking_keywords = [
            "cook", "cooking", "recipe", "biryani", "cake", "rice",
            "vegetable", "food", "kitchen", "ingredient", "boil",
            "fry", "bake", "meal", "dish"
        ]
        self.entertainment_keywords = [
            "movie", "film", "cinema", "actor", "actress", "song",
            "music", "series", "show", "netflix", "amazon prime",
            "tv", "hollywood", "bollywood"
        ]
        self.greetings = [
            "hi", "hello", "hey", "good morning", "good evening",
            "hello doctor", "hi doctor"
        ]

    # --------------------------------------------------
    # Rule-based keyword domain (no LLM, instant)
    # --------------------------------------------------

    def _keyword_domain(self, msg):

        keyword_sets = [
            (self.medical_keywords, "Healthcare"),
            (self.education_keywords, "Education"),
            (self.programming_keywords, "Programming"),
            (self.math_keywords, "Mathematics"),
            (self.law_keywords, "Law"),
            (self.travel_keywords, "Travel"),
            (self.finance_keywords, "Finance"),
            (self.sports_keywords, "Sports"),
            (self.cooking_keywords, "Cooking"),
            (self.entertainment_keywords, "Entertainment"),
        ]

        # Whole-word match only - plain "word in msg" substring checks let
        # short keywords like "c" or "mi" match inside unrelated words
        # (e.g. "exercise" contains "c"), misrouting the persona.
        for keywords, domain in keyword_sets:
            if any(
                re.search(r"\b" + re.escape(word) + r"\b", msg)
                for word in keywords
            ):
                return domain, 1.00

        return "General", 0.20

    # --------------------------------------------------
    # Main entry point
    # --------------------------------------------------

    def analyze(self, persona, message, recent_user_history=None):

        msg = message.lower().strip()

        # ---- Instant greeting shortcut: zero LLM calls ----
        if msg in self.greetings:
            return {
                "category": "Greeting",
                "intent": "Greeting",
                "emotion": "Neutral",
                "urgency": "Low",
                "domain": "General",
                "domain_confidence": 1.0,
                "domain_source": "Keyword",
                "entities": [],
                "keywords": [],
                "persona_match": 1.0,
                "confidence": 1.0,
                "risk": "Low",
                "risk_priority": 0.10,
                "risk_reason": "Greeting",
                "dependency": False,
                "novel_information": False,
                "novelty_reason": "Greeting",
            }

        keyword_domain, keyword_confidence = self._keyword_domain(msg)

        recent_user_history = recent_user_history or []
        history_snippet = recent_user_history[-self.history_window:]

        role_risk_rules = {
            "Doctor": "Chest pain/difficulty breathing -> Critical. Fever -> Medium.",
            "Teacher": "Exam tomorrow -> High. Homework -> Low.",
            "Lawyer": "Court hearing -> High. Legal advice -> Medium.",
            "Travel Guide": "Lost passport -> High. Hotel booking -> Low.",
        }.get(persona["role"], "Urgent/harmful situations -> High or Critical. Routine questions -> Low.")

        prompt = f"""Analyze this message. Return ONLY one JSON object, no other text.

Persona: {persona["role"]} (goal: {persona["goal"]})
Recent user messages: {history_snippet}
Current message: "{message}"
Likely domain (prefer unless clearly wrong): {keyword_domain}

Risk rule for this persona: {role_risk_rules}

JSON schema (fill every field, do not leave any blank):
{{
"category": "short label",
"intent": "one of: Greeting, Seek Medical Advice, Request Explanation, Ask Information, Report Symptom, Provide Information, Casual Conversation",
"emotion": "one of: Neutral, Happy, Concerned, Angry, Sad",
"urgency": "one of: Low, Medium, High, Critical",
"domain": "one of: Healthcare, Education, Programming, Mathematics, Law, Travel, Finance, Sports, Cooking, Entertainment, General",
"domain_confidence": 0.0,
"entities": ["key nouns from the message"],
"keywords": ["key nouns from the message"],
"persona_match": 0.0,
"confidence": 0.0,
"risk": "Low, Medium, High, or Critical",
"risk_priority": 0.0,
"risk_reason": "short reason",
"dependency": true if the current message only makes sense given a recent message above, else false,
"novel_information": true if current message adds new info vs recent messages, else false,
"novelty_reason": "short reason"
}}"""

        response = generate(prompt)

        response = response.strip()
        response = re.sub(r"^```json", "", response)
        response = re.sub(r"^```", "", response)
        response = re.sub(r"```$", "", response)
        response = response.strip()

        try:
            result = json.loads(response)
        except Exception:
            print("\n==============================")
            print("Unified Analyzer JSON Error")
            print("==============================")
            print(response)
            print("==============================")
            result = {}

        defaults = {
            "category": "Unknown",
            "intent": "Ask Information",
            "emotion": "Neutral",
            "urgency": "Low",
            "domain": "General",
            "domain_confidence": 0.0,
            "entities": [],
            "keywords": [],
            "persona_match": 0.90,
            "confidence": 0.90,
            "risk": "Low",
            "risk_priority": 0.30,
            "risk_reason": "Fallback",
            "dependency": False,
            "novel_information": True,
            "novelty_reason": "Fallback",
        }

        for key, value in defaults.items():
            if key not in result or result[key] is None:
                result[key] = value

        if not isinstance(result["entities"], list):
            result["entities"] = []
        if not isinstance(result["keywords"], list):
            result["keywords"] = []

        for key in ("persona_match", "confidence", "risk_priority", "domain_confidence"):
            try:
                result[key] = float(result[key])
            except Exception:
                result[key] = defaults[key]

        if len(result["entities"]) == 0:
            result["entities"] = list(set(result["keywords"]))

        # ---- Domain fusion (rule-based keyword vs LLM opinion), no extra call ----
        fusion = self.domain_fusion.fuse(
            keyword_domain,
            keyword_confidence,
            result["domain"],
            result["domain_confidence"],
        )
        result["domain"] = fusion["domain"]
        result["domain_confidence"] = fusion["confidence"]
        result["domain_source"] = fusion["source"]

        print("Detected Domain:", result["domain"])

        return result


# --------------------------------------------------
# TEST
# --------------------------------------------------

if __name__ == "__main__":

    analyzer = UnifiedAnalyzer()

    persona = {"role": "Doctor", "goal": "Help patients"}

    history = []
    tests = [
        "Hello doctor",
        "I have diabetes",
        "Can I take insulin?",
    ]

    for message in tests:
        print("\n========================")
        print(message)
        print("========================")

        result = analyzer.analyze(persona, message, history)
        print(json.dumps(result, indent=4))

        history.append(message)