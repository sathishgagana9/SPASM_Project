def create_ecp(memory, current_agent):

    context = ""

    for item in memory:

        speaker = item["speaker"]
        message = item["message"]

        if speaker == current_agent:

            context += (
                f"SELF: {message}\n\n"
            )

        else:

            context += (
                f"PARTNER: {message}\n\n"
            )

    return context


if __name__ == "__main__":

    memory = [

        {
            "speaker": "Agent1",
            "message": "Hello"
        },

        {
            "speaker": "Agent2",
            "message": "Hi"
        },

        {
            "speaker": "Agent1",
            "message": "How are you?"
        }
    ]

    print(
        create_ecp(
            memory,
            "Agent1"
        )
    )