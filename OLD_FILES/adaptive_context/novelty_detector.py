import json
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.llm import generate


class NoveltyDetector:

    def __init__(self):
        pass

    def detect(self, conversation):

        prompt = f"""
You are a Novel Information Detector.

Conversation

{json.dumps(conversation, indent=2)}

Task

For every message determine whether it introduces NEW information
or simply repeats previous information.

Return ONLY JSON.

Format

{{
    "novelty":[

        {{
            "turn":1,
            "novel":true,
            "reason":"Introduces new information."
        }},

        {{
            "turn":2,
            "novel":false,
            "reason":"Repeats previous information."
        }}

    ]
}}
"""

        response = generate(prompt)

        try:

            return json.loads(response)

        except Exception:

            return {

                "novelty":[

                    {

                        "turn":i+1,

                        "novel":True,

                        "reason":"Fallback"

                    }

                    for i in range(len(conversation))

                ]

            }


if __name__=="__main__":

    detector = NoveltyDetector()

    conversation=[

        {

            "speaker":"User",

            "message":"I have diabetes."

        },

        {

            "speaker":"User",

            "message":"I have diabetes."

        },

        {

            "speaker":"User",

            "message":"My sugar level is 320."

        },

        {

            "speaker":"User",

            "message":"Can I take insulin?"

        }

    ]

    result = detector.detect(conversation)

    print(json.dumps(result,indent=4))