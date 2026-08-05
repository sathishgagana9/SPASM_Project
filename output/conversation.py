from ecp import create_ecp
import google.generativeai as genai
import time

# -----------------------------
# Gemini Configuration
# -----------------------------

API_KEY = "AQ.Ab8RN6IpHybaa3ejGWeDpBHQBzVK0qR-HXCbMH--uzjNaiMghg"

genai.configure(api_key=API_KEY)

model = genai.GenerativeModel(
    "gemini-2.5-flash"
)

# -----------------------------
# Load Personas
# -----------------------------

with open(
    "../personas/doctor.txt",
    "r",
    encoding="utf-8"
) as f:
    doctor_persona = f.read()

with open(
    "../personas/patient.txt",
    "r",
    encoding="utf-8"
) as f:
    patient_persona = f.read()

# -----------------------------
# Conversation Memory
# -----------------------------

memory = []

# Starting Message

doctor_message = "Hello, what brings you here today?"

# -----------------------------
# Conversation Loop
# -----------------------------

for turn in range(2):

    print("\n" + "=" * 50)

    print("\nDOCTOR:")
    print(doctor_message)

    memory.append(
        {
            "speaker": "Doctor",
            "message": doctor_message
        }
    )

    # -------------------------
    # Patient ECP Context
    # -------------------------

    patient_context = create_ecp(
        memory,
        "Patient"
    )

    patient_prompt = f"""
Persona:

{patient_persona}

Conversation History:

{patient_context}

Respond as the patient.
"""

    patient_response = model.generate_content(
        patient_prompt
    ).text

    print("\nPATIENT:")
    print(patient_response)

    memory.append(
        {
            "speaker": "Patient",
            "message": patient_response
        }
    )

    time.sleep(5)

    # -------------------------
    # Doctor ECP Context
    # -------------------------

    doctor_context = create_ecp(
        memory,
        "Doctor"
    )

    doctor_prompt = f"""
Persona:

{doctor_persona}

Conversation History:

{doctor_context}

Respond as the doctor.
"""

    doctor_message = model.generate_content(
        doctor_prompt
    ).text

    time.sleep(5)

# -----------------------------
# Print Memory
# -----------------------------

print("\n")
print("=" * 50)
print("MEMORY CONTENTS")
print("=" * 50)

for item in memory:

    print(
        f"{item['speaker']} : {item['message']}"
    )

with open(
    "../outputs/conversation.txt",
    "w",
    encoding="utf-8"
) as f:

    for item in memory:

        f.write(
            f"{item['speaker']} : {item['message']}\n\n"
        )

print("\nConversation Saved!")