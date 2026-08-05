def should_stop(message):

    stop_words = [
        "goodbye",
        "bye",
        "problem solved",
        "i feel better now",
        "my issue is resolved",
        "thanks doctor",
        "thank you doctor"
    ]

    message = message.lower()

    for word in stop_words:

        if word in message:
            return True

    return False