PROBE_QUESTIONS = [

    "Who are you?",

    "What is your occupation?",

    "How do you feel right now?",

    "What problem are you facing?",

    "What are your goals?"
]


def get_probe_questions():

    return PROBE_QUESTIONS


if __name__ == "__main__":

    print("DRIFT PROBE QUESTIONS\n")

    for i, question in enumerate(PROBE_QUESTIONS, start=1):

        print(
            f"{i}. {question}"
        )