import google.generativeai as genai

API_KEY = "xai-ZoWh6qUt2J5itcDAUKsKDMwlwNpFpqkwhwfl2xxNqm3WISzYJGZikL0w6KekcEmdBk5fIW4lPrNsM7v8"

genai.configure(api_key=API_KEY)

model = genai.GenerativeModel(
    "gemini-2.5-flash"
)

role = "Doctor"

response = """
I understand you're worried about your fever.
Could you tell me more about your symptoms?
"""

prompt = f"""
Role:

{role}

Response:

{response}

Rate how well this response follows the role.

Give a score from 1 to 10.

Answer ONLY the number.
"""

result = model.generate_content(prompt)

print(
    "Role Adherence Score:",
    result.text
)