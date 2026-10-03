CONCERN_PROBES = [

    "What is your main concern right now?",

    "What issue are you currently facing?",

    "What problem are you trying to solve?"
]


EMOTION_PROBES = [

    "How are you feeling emotionally?",

    "Describe your emotional state.",

    "What emotions are you experiencing right now?"
]


MOTIVATION_PROBES = [

    "What is your current goal?",

    "What are you hoping to achieve?",

    "What outcome do you want most?"
]


def get_all_probes():

    return {

        "concern":
            CONCERN_PROBES,

        "emotion":
            EMOTION_PROBES,

        "motivation":
            MOTIVATION_PROBES
    }


if __name__ == "__main__":

    probes = get_all_probes()

    for category, questions in probes.items():

        print("\n" + category.upper())

        for q in questions:

            print("-", q)