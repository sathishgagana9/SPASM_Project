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
from domain_classifier import DomainClassifier
from domain_fusion import DomainFusion

class ContextAnalyzer:

    def __init__(self):

        self.domain_classifier = DomainClassifier()

        self.domain_fusion = DomainFusion()

    def analyze(self, persona, message):

        # ----------------------------------------
        # Quick Rule Based Detection
        # ----------------------------------------

        msg = message.lower().strip()

        medical_keywords = [
            "fever", "diabetes", "blood", "pain", "doctor", "medicine",
            "insulin", "headache", "cough", "cold", "infection",
            "heart", "sugar", "bp", "pressure", "hospital", "symptom"
        ]

        education_keywords = [
            "study", "teacher", "student", "exam", "school",
            "college", "university", "homework"
        ]

        programming_keywords = [
            "python", "java", "c", "cpp", "linked list",
            "array", "stack", "queue", "tree", "algorithm",
            "code", "program", "compiler", "pointer"
        ]

        math_keywords = [
            "math", "mathematics", "algebra",
            "calculus", "geometry", "equation",
            "integration", "derivative"
        ]

        law_keywords = [
            "court", "law", "legal", "judge",
            "crime", "police", "case", "lawyer"
        ]

        travel_keywords = [
            "travel", "trip", "hotel", "flight",
            "visa", "tour", "vacation", "tourism"
        ]

        finance_keywords = [
            "loan", "bank", "investment", "stock",
            "money", "salary", "tax", "insurance"
        ]


        sports_keywords = [
            "ipl",
            "cricket",
            "football",
            "match",
            "t20",
            "odi",
            "world cup",
            "wicket",
            "batsman",
            "bowler",
            "score",
            "rcb",
            "csk",
            "mi",
            "kkr",
            "srh",
            "gt",
            "rr",
            "pbks",
            "lsg"
        ]

        cooking_keywords = [
            "cook",
            "cooking",
            "recipe",
            "biryani",
            "cake",
            "rice",
            "vegetable",
            "food",
            "kitchen",
            "ingredient",
            "boil",
            "fry",
            "bake",
            "meal",
            "dish"
        ]

        entertainment_keywords = [
                "movie",
                "film",
                "cinema",
                "actor",
                "actress",
                "song",
                "music",
                "series",
                "show",
                "netflix",
                "amazon prime",
                "tv",
                "hollywood",
                "bollywood"
            ]


        greetings = [
            "hi",
            "hello",
            "hey",
            "good morning",
            "good evening",
            "hello doctor",
            "hi doctor"
        ]
        movie_keywords = [
            "movie",
            "film",
            "actor",
            "actress",
            "cinema"
        ]




        if msg in greetings:

            return {

                "category": "Greeting",

                "intent": "Greeting",

                "emotion": "Neutral",

                "urgency": "Low",

                "domain": "General",

                "entities": [],

                "keywords": [],

                "dependency": False,

                "novel_information": False,

                "persona_match": 1.0,

                "confidence": 1.0

            }
        
        import re

        tokens = re.findall(r"\b\w+\b", msg)

        domain = "General"

        keyword_confidence = 0.20

        # ----------------------------------------
        # Healthcare
        # ----------------------------------------

        if any(word in msg for word in medical_keywords):

            domain = "Healthcare"

            keyword_confidence = 1.00

        # ----------------------------------------
        # Education
        # ----------------------------------------

        elif any(word in msg for word in education_keywords):

            domain = "Education"

            keyword_confidence = 1.00

        # ----------------------------------------
        # Programming
        # ----------------------------------------

        elif any(word in msg for word in programming_keywords):

            domain = "Programming"

            keyword_confidence = 1.00

        # ----------------------------------------
        # Mathematics
        # ----------------------------------------

        elif any(word in msg for word in math_keywords):

            domain = "Mathematics"

            keyword_confidence = 1.00

        # ----------------------------------------
        # Law
        # ----------------------------------------

        elif any(word in msg for word in law_keywords):

            domain = "Law"

            keyword_confidence = 1.00

        # ----------------------------------------
        # Travel
        # ----------------------------------------

        elif any(word in msg for word in travel_keywords):

            domain = "Travel"

            keyword_confidence = 1.00

        # ----------------------------------------
        # Finance
        # ----------------------------------------

        elif any(word in msg for word in finance_keywords):

            domain = "Finance"

            keyword_confidence = 1.00

        # ----------------------------------------
        # Sports
        # ----------------------------------------

        elif any(word in msg for word in sports_keywords):

            domain = "Sports"

            keyword_confidence = 1.00

        # ----------------------------------------
        # Cooking
        # ----------------------------------------

        elif any(word in msg for word in cooking_keywords):

            domain = "Cooking"

            keyword_confidence = 1.00

        # ----------------------------------------
        # Entertainment
        # ----------------------------------------

        elif any(word in msg for word in entertainment_keywords):

            domain = "Entertainment"

            keyword_confidence = 1.00

        prompt = f"""
You are an expert Context Analysis Engine.

Your ONLY job is to analyze the user's message.

Never answer the user.

--------------------------------------------------

PERSONA

Role:
{persona["role"]}

Goal:
{persona["goal"]}

--------------------------------------------------

USER MESSAGE

{message}

Rule-Based Detected Domain:

{domain}

Prefer this detected domain unless it is clearly incorrect.
--------------------------------------------------

Return ONLY JSON.

Schema

{{
    "category":"",
    "intent":"",
    "emotion":"",
    "urgency":"",
    "domain":"",
    "entities":[],
    "keywords":[],
    "dependency":false,
    "novel_information":true,
    "persona_match":0.0,
    "confidence":0.0
}}

--------------------------------------------------

Allowed Domains

Healthcare
Education
Programming
Mathematics
Law
Travel
Finance
Sports
Cooking
General
--------------------------------------------------

Allowed Intent

Greeting
Seek Medical Advice
Request Explanation
Ask Information
Report Symptom
Provide Information
Casual Conversation

Never invent new intent names.

--------------------------------------------------

Allowed Domains

Healthcare
Education
Programming
Mathematics
Law
Travel
Finance
Sports
Cooking
General
Choose only one.

--------------------------------------------------

Emotion

Neutral
Happy
Concerned
Angry
Sad

--------------------------------------------------

Urgency

Low
Medium
High
Critical

--------------------------------------------------

Examples

hello doctor

{{
"category":"Greeting",
"intent":"Greeting",
"emotion":"Neutral",
"urgency":"Low",
"domain":"General"
}}

I have diabetes

{{
"category":"Medical History",
"intent":"Report Symptom",
"emotion":"Neutral",
"urgency":"Medium",
"domain":"Healthcare"
}}

Can you explain mathematics?

{{
"category":"Question",
"intent":"Request Explanation",
"emotion":"Neutral",
"urgency":"Low",
"domain":"Mathematics"
}}

Explain IPL match

{{
"category":"Question",
"intent":"Ask Information",
"emotion":"Neutral",
"urgency":"Low",
"domain":"Sports"
}}



Return ONLY JSON.
"""

        response = generate(prompt)


        

                # ----------------------------------------
        # Clean LLM Response
        # ----------------------------------------

        response = response.strip()

        response = re.sub(r"^```json", "", response)
        response = re.sub(r"^```", "", response)
        response = re.sub(r"```$", "", response)

        response = response.strip()

        # ----------------------------------------
        # Parse JSON
        # ----------------------------------------

        try:

            result = json.loads(response)

        except Exception:

            print("\n==============================")
            print("Context Analyzer JSON Error")
            print("==============================")
            print(response)
            print("==============================")

            result = {}

        # ----------------------------------------
        # Default Values
        # ----------------------------------------

        defaults = {

            "category": "Unknown",

            "intent": "Ask Information",

            "emotion": "Neutral",

            "urgency": "Low",

            "domain": "General",

            "entities": [],

            "keywords": [],

            "dependency": False,

            "novel_information": True,

            "persona_match": 0.90,

            "confidence": 0.90,

            "domain_confidence": 0.0,

            "domain_source": "Unknown",

        }

        # ----------------------------------------
        # Fill Missing Keys
        # ----------------------------------------

        for key, value in defaults.items():

            if key not in result:

                result[key] = value

        # ----------------------------------------
        # Type Safety
        # ----------------------------------------

        if not isinstance(result["entities"], list):

            result["entities"] = []

        if not isinstance(result["keywords"], list):

            result["keywords"] = []

        try:

            result["persona_match"] = float(result["persona_match"])

        except:

            result["persona_match"] = 0.90

        try:

            result["confidence"] = float(result["confidence"])

        except:

            result["confidence"] = 0.90


        try:
            result["domain_confidence"] = float(result["domain_confidence"])
        except:
            result["domain_confidence"] = 0.0


        # ----------------------------------------
        # Override incorrect LLM domain
        # ----------------------------------------

        # ----------------------------------------
        # Rule-based domain has higher priority
        # ----------------------------------------

        # ----------------------------------------
        # LLM Domain Prediction
        # ----------------------------------------

        prediction = self.domain_classifier.classify(message)

        llm_domain = prediction["domain"]

        llm_confidence = prediction["confidence"]

        # ----------------------------------------
        # Hybrid Domain Fusion
        # ----------------------------------------

        fusion = self.domain_fusion.fuse(

            domain,

            keyword_confidence,

            llm_domain,

            llm_confidence

        )

        result["domain"] = fusion["domain"]

        result["domain_confidence"] = fusion["confidence"]

        result["domain_source"] = fusion["source"]

                

        # ----------------------------------------
        # Entity Fallback
        # ----------------------------------------

        if len(result["entities"]) == 0:
            result["entities"] = list(set(result["keywords"]))




        print("Detected Domain:", result["domain"])

        # ----------------------------------------
        # Return
        # ----------------------------------------

        return result

# --------------------------------------------------
# TEST
# --------------------------------------------------

if __name__ == "__main__":

    analyzer = ContextAnalyzer()

    persona = {

        "role": "Doctor",

        "goal": "Help patients"

    }

    tests = [

        "Hello doctor",

        "I have diabetes",

        "I have fever",

        "Can I take insulin?",

        "Can you explain mathematics?",

        "What should I eat?"

    ]

    for message in tests:

        print("\n========================")
        print(message)
        print("========================")

        result = analyzer.analyze(

            persona,

            message

        )

        print(

            json.dumps(

                result,

                indent=4

            )

        )