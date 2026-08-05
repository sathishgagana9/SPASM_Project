import json
from llm import generate


# ---------------------------------------
# Analyze One Message
# ---------------------------------------

def analyze_message(persona, message):

    prompt = f"""
You are a Persona-Aware Conversation Context Analyzer.

Persona:

Role: {persona['role']}
Tone: {persona['tone']}
Goal: {persona['goal']}
Personality: {persona['personality']}

Conversation Message:

"{message}"

Tasks:

1. Classify the message into ONE category.

Categories:
- Greeting
- Persona Information
- User Profile
- User Goal
- User State
- Emotion
- Task
- Temporary Context
- Closing
- Small Talk
- Other

2. Give a Persona Relevance score between 0 and 1.
   1.0 = Extremely important for this persona.
   0.0 = Not important.

3. Give your confidence between 0 and 1.

Return ONLY valid JSON in this format:

{{
    "category":"...",
    "persona_relevance":0.0,
    "confidence":0.0,
    "reason":"..."
}}
"""

    response = generate(prompt)

    try:
        result = json.loads(response)
    except Exception:
        result = {
            "category": "Other",
            "persona_relevance": 0.0,
            "confidence": 0.0,
            "reason": "Unable to parse LLM response."
        }

    return result


# ---------------------------------------
# Analyze Whole Conversation
# ---------------------------------------

def analyze_conversation(persona, conversation):

    analyzed = []

    for turn, item in enumerate(conversation, start=1):

        result = analyze_message(persona, item["message"])

        analyzed.append({

            "turn": turn,

            "speaker": item["speaker"],

            "message": item["message"],

            "category": result["category"],

            "persona_relevance": result["persona_relevance"],

            "confidence": result["confidence"],

            "reason": result["reason"]

        })

    return analyzed


# ---------------------------------------
# Example
# ---------------------------------------

if __name__ == "__main__":

    persona = {
        "role": "Doctor",
        "tone": "Professional",
        "goal": "Help patients",
        "personality": "Empathetic"
    }

    conversation = [

        {
            "speaker": "User",
            "message": "Hello Doctor."
        },

        {
            "speaker": "Doctor",
            "message": "Hello. How can I help you today?"
        },

        {
            "speaker": "User",
            "message": "I have diabetes."
        },

        {
            "speaker": "User",
            "message": "I have chest pain."
        },

        {
            "speaker": "User",
            "message": "Can I take aspirin?"
        },

        {
            "speaker": "User",
            "message": "Thank you."
        }

    ]

    output = analyze_conversation(persona, conversation)

    print(json.dumps(output, indent=4))