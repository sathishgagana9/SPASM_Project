import os
import sys
import json
import re

sys.path.append(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )
)

from scripts.llm import generate
class DomainClassifier:

    def __init__(self):
        pass

    def classify(self, message):

        prompt = f"""
You are a Domain Classification Engine.

Your ONLY job is to classify the user's message.

Do NOT answer the question.

Choose ONLY ONE domain.

Allowed Domains

Healthcare
Programming
Education
Mathematics
Law
Travel
Finance
Cooking
Sports
Entertainment
General

Return ONLY JSON.

Format:

{{
    "domain":"Programming",
    "confidence":0.95
}}

User Message:

{message}

Return ONLY JSON.
"""

        response = generate(prompt)

        response = response.strip()

        response = re.sub(r"^```json", "", response)
        response = re.sub(r"^```", "", response)
        response = re.sub(r"```$", "", response)

        try:

            result = json.loads(response)

        except:

            result = {
                "domain": "General",
                "confidence": 0.50
            }

        if "domain" not in result:
            result["domain"] = "General"

        if "confidence" not in result:
            result["confidence"] = 0.50

        return result


# ------------------------
# TEST
# ------------------------

if __name__ == "__main__":

    classifier = DomainClassifier()

    tests = [

        "I have fever",

        "Explain recursion",

        "How to make biryani",

        "Explain IPL",

        "What is Newton's law?",

        "I want to visit Paris"

    ]

    for t in tests:

        print("\n====================")
        print(t)

        print(classifier.classify(t))