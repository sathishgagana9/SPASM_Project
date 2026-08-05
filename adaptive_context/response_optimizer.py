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


class ResponseOptimizer:

    def __init__(self):
        pass

    def optimize(

        self,

        persona,

        user_message,

        response,

        analysis,

        stability

    ):

        prompt = f"""
You are the SPASM++ Response Optimizer.

Your job is NOT to change the meaning.

Improve the response.

-----------------------------------------

PERSONA

Role:
{persona["role"]}

Tone:
{persona["tone"]}

Goal:
{persona["goal"]}

-----------------------------------------

USER MESSAGE

{user_message}

-----------------------------------------

CURRENT RESPONSE

{response}

-----------------------------------------

ANALYSIS

Category:
{analysis["category"]}

Intent:
{analysis["intent"]}

Emotion:
{analysis["emotion"]}

Domain:
{analysis["domain"]}

-----------------------------------------

PERSONA STABILITY

{stability}

-----------------------------------------

RULES

1. Preserve the original meaning.

2. Stay in the persona.

3. Improve grammar.

4. Improve clarity.

5. Be professional.

6. Be concise.

7. Remove unnecessary words.

8. Never change the role.

9. Never answer outside the role.

10. Return ONLY the optimized response.

"""

        optimized = generate(prompt)

        return optimized


# ---------------------------------------------------
# TEST
# ---------------------------------------------------

if __name__ == "__main__":

    optimizer = ResponseOptimizer()

    persona = {

        "role":"Doctor",

        "tone":"Professional",

        "goal":"Help patients"

    }

    analysis = {

        "category":"Question",

        "intent":"Medical Advice",

        "emotion":"Concerned",

        "domain":"Healthcare"

    }

    response = """

You should drink plenty of water and
consult your physician if your fever
continues.

"""

    result = optimizer.optimize(

        persona,

        "I have fever.",

        response,

        analysis,

        0.91

    )

    print(result)