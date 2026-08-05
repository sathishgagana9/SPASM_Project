import json
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.llm import generate


class DependencyAnalyzer:

    def __init__(self):
        pass

    def analyze(self, conversation):

        prompt = f"""
You are a Conversation Dependency Analyzer.

Conversation:

{json.dumps(conversation, indent=2)}

Your task:

For each message, determine whether it depends on any previous message.

Examples:

Message:
"I have diabetes."

↓

Depends on:
None

-------------------------

Message:
"Can I take insulin?"

↓

Depends on:
"I have diabetes."

-------------------------

Return ONLY valid JSON.

Format:

{{
    "dependencies":[
        {{
            "turn":1,
            "depends_on":[]
        }},
        {{
            "turn":2,
            "depends_on":[1]
        }}
    ]
}}
"""

        response = generate(prompt)

        try:
            return json.loads(response)

        except Exception:

            return {

                "dependencies":[

                    {
                        "turn":i+1,
                        "depends_on":[]
                    }

                    for i in range(len(conversation))

                ]

            }


if __name__=="__main__":

    analyzer = DependencyAnalyzer()

    conversation=[

        {
            "speaker":"User",
            "message":"I have diabetes."
        },

        {
            "speaker":"Assistant",
            "message":"How long have you had diabetes?"
        },

        {
            "speaker":"User",
            "message":"Can I take insulin?"
        },

        {
            "speaker":"User",
            "message":"My sugar level is 320."
        }

    ]

    result = analyzer.analyze(conversation)

    print(json.dumps(result, indent=4))