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


class PersonaRepairEngine:

    def __init__(self, threshold=0.90, max_attempts=3):

        self.threshold = threshold
        self.max_attempts = max_attempts

    def repair(
        self,
        persona,
        user_message,
        response,
        stability_score
    ):

        if stability_score >= self.threshold:
            return response, False, 0

        repaired_response = response

        for attempt in range(self.max_attempts):

            prompt = f"""
You are the SPASM++ Persona Repair Engine.

Your task is to improve the assistant response while preserving its meaning.

CURRENT PERSONA

Role:
{persona["role"]}

Tone:
{persona["tone"]}

Goal:
{persona["goal"]}

Current Stability

{stability_score:.2f}

User Message

{user_message}

Current Response

{repaired_response}

YOUR OBJECTIVE

Increase persona stability.

The rewritten response MUST satisfy ALL of these:

1. Behave ONLY as a {persona["role"]}

2. Maintain a {persona["tone"]} tone.

3. Achieve the goal:
{persona["goal"]}

4. Keep the same meaning.

5. Never answer outside the persona.

6. Use previous user information when appropriate.

7. Be more helpful.

8. Be more complete.

9. Sound natural.

10. Never mention AI, persona or repair.

11. End with one professional recommendation if appropriate.

Return ONLY the rewritten response.
"""

            repaired_response = generate(prompt, num_predict=180).strip()

        return repaired_response, True, self.max_attempts


# --------------------------------------------------
# TEST
# --------------------------------------------------

if __name__ == "__main__":

    engine = PersonaRepairEngine()

    persona = {
        "role": "Doctor",
        "tone": "Professional",
        "goal": "Help patients"
    }

    reply, repaired, attempts = engine.repair(
        persona,
        "I have diabetes.",
        "Eat healthy.",
        0.45
    )

    print("Repaired :", repaired)
    print("Attempts :", attempts)
    print("\nResponse:\n")
    print(reply)