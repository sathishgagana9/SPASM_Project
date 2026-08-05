def detect_echoing(
    doctor_response,
    patient_response
):

    doctor_words = set(
        doctor_response.lower().split()
    )

    patient_words = set(
        patient_response.lower().split()
    )

    overlap = doctor_words.intersection(
        patient_words
    )

    score = (
        len(overlap)
        /
        max(
            len(patient_words),
            1
        )
    )

    return score


doctor = """
I understand your fever.
Tell me more.
"""

patient = """
I have fever.
I am worried.
"""

score = detect_echoing(
    doctor,
    patient
)

print(
    "Echoing Score:",
    score
)