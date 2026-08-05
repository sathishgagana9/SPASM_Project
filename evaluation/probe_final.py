import json

final_answers = {

    "Who are you?":
        "I am a Civil Servant.",

    "What is your occupation?":
        "Civil Servant",

    "How do you feel right now?":
        "Calm",

    "What problem are you facing?":
        "Tax Issues",

    "What are your goals?":
        "To resolve Tax Issues successfully."
}

with open(
    "final.json",
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        final_answers,
        f,
        indent=4
    )

print("Final Answers Saved")