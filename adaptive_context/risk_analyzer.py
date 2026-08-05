import json
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.llm import generate


class RiskAnalyzer:

    def __init__(self):
        pass

    def analyze(self, persona, message):

        prompt = f"""
You are a Persona-Aware Risk Analyzer.

Persona

Role : {persona["role"]}

Goal : {persona["goal"]}

User Message

"{message}"

Determine the risk level.

Return ONLY JSON.

Format

{{
    "risk":"Low | Medium | High | Critical",
    "priority":0.0,
    "reason":"..."
}}

Rules

Doctor
- Chest pain -> Critical
- Fever -> Medium
- Difficulty breathing -> Critical

Teacher
- Exam tomorrow -> High
- Homework -> Low

Lawyer
- Court hearing -> High
- Legal advice -> Medium

Travel Guide
- Lost passport -> High
- Hotel booking -> Low

Customer Support
- Payment failed -> High
- Product inquiry -> Low
"""

        response = generate(prompt)

        try:
            return json.loads(response)

        except Exception:

            return {

                "risk":"Low",

                "priority":0.30,

                "reason":"Fallback"

            }


if __name__=="__main__":

    analyzer = RiskAnalyzer()

    persona={

        "role":"Doctor",

        "goal":"Help patients"

    }

    message="I have severe chest pain."

    result=analyzer.analyze(persona,message)

    print(json.dumps(result,indent=4))