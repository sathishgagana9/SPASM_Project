import json
from scripts.llm import generate


class SemanticInformationExtractor:

    def __init__(self):
        pass

    def extract(self, message):

        prompt = f"""
You are an intelligent semantic information extractor.

Your task is to understand the MEANING of the user's message.

Do NOT rely on keywords.

Extract as much useful information as possible.

Return ONLY valid JSON.

Schema:

{{
    "domain":"",
    "intent":"",
    "topic":"",
    "entities":[],
    "slots":{{}},
    "confidence":0.0
}}

Examples

User:
I have had fever for two days.

Output:
{{
    "domain":"Healthcare",
    "intent":"Report Symptom",
    "topic":"Fever",
    "entities":["fever"],
    "slots":{{
        "symptom":"fever",
        "duration":"2 days"
    }},
    "confidence":0.98
}}

----------------------------

User:
Explain linked list.

Output:
{{
    "domain":"Programming",
    "intent":"Request Explanation",
    "topic":"Linked List",
    "entities":["Linked List"],
    "slots":{{}},
    "confidence":0.99
}}

----------------------------

User:
I want to visit Paris.

Output:
{{
    "domain":"Travel",
    "intent":"Travel Planning",
    "topic":"Paris",
    "entities":["Paris"],
    "slots":{{
        "destination":"Paris"
    }},
    "confidence":0.98
}}

----------------------------

User:
Suggest medicine for headache.

Output:
{{
    "domain":"Healthcare",
    "intent":"Medicine Request",
    "topic":"Headache",
    "entities":["headache"],
    "slots":{{
        "symptom":"headache"
    }},
    "confidence":0.98
}}

Now extract information from this message.

User:

{message}

Return ONLY JSON.
"""

        response = generate(prompt)

        try:
            start = response.find("{")
            end = response.rfind("}") + 1

            data = json.loads(response[start:end])

            return data

        except Exception:

            return {
                "domain": "Unknown",
                "intent": "Unknown",
                "topic": "",
                "entities": [],
                "slots": {},
                "confidence": 0.0
            }


if __name__ == "__main__":

    extractor = SemanticInformationExtractor()

    tests = [

        "I have fever for two days.",

        "Explain recursion.",

        "How to make biryani?",

        "I have chest pain.",

        "I want to visit Mysore.",

        "Explain Chitradurga history.",

        "Suggest medicine for headache."

    ]

    for t in tests:

        print("\n===========================")
        print(t)

        print(

            json.dumps(

                extractor.extract(t),

                indent=4

            )

        )