import json
import os
import sys

sys.path.append(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )
)

from scripts.llm import generate


class ResponseValidator:

    def __init__(self):
        pass

    def validate(
        self,
        persona,
        user_message,
        reply,
        analysis,
        graph_context,
        selected_context
    ):

        prompt = f"""
You are an expert AI evaluator.

Evaluate whether the assistant maintained its persona.

EXPECTED PERSONA

Role: {persona["role"]}
Tone: {persona["tone"]}
Goal: {persona["goal"]}

USER MESSAGE

{user_message}

ASSISTANT RESPONSE

{reply}

Return ONLY valid JSON.

{{
    "role":0.95,
    "tone":0.90,
    "goal":0.94,
    "memory":0.91,
    "context":0.92,
    "reason":"Persona maintained successfully."
}}
"""

        response = generate(prompt, num_predict=120).strip()

        if response.startswith("```json"):
            response = response.replace("```json", "")

        if response.startswith("```"):
            response = response.replace("```", "")

        if response.endswith("```"):
            response = response[:-3]

        response = response.strip()

        try:
            result = json.loads(response)

        except Exception:

            result = {
                "role": 0.80,
                "tone": 0.80,
                "goal": 0.80,
                "memory": 0.80,
                "context": 0.80,
                "reason": "Validation failed."
            }

        # Safe float conversion
        for key in ["role", "tone", "goal", "memory", "context"]:

            try:
                result[key] = float(result[key])
            except:
                result[key] = 0.80

        # Compute stability ourselves
        result["stability"] = round(
            (
                result["role"]
                + result["tone"]
                + result["goal"]
                + result["memory"]
                + result["context"]
            ) / 5,
            2
        )

        return result


if __name__ == "__main__":

    validator = ResponseValidator()

    persona = {
        "role": "Doctor",
        "tone": "Professional",
        "goal": "Help patients"
    }

    analysis = {
        "category": "Question",
        "intent": "Medical Advice",
        "emotion": "Concerned",
        "domain": "Healthcare"
    }

    reply = """
As a doctor,
I recommend consulting your physician.
Please monitor your blood sugar.
"""

    result = validator.validate(
        persona,
        "I have diabetes.",
        reply,
        analysis,
        ["Diabetes", "Blood Sugar"],
        [
            {
                "speaker": "User",
                "message": "I have diabetes."
            }
        ]
    )

    print(json.dumps(result, indent=4))