import json


def build_context(conversation, scores, top_k=5):
    """
    Select the most important messages from the conversation.
    """

    combined = []

    for msg, score in zip(conversation, scores):

        combined.append({

            "speaker": msg["speaker"],

            "message": msg["message"],

            "importance": score["importance"]

        })

    # Sort by importance
    combined.sort(

        key=lambda x: x["importance"],

        reverse=True

    )

    # Keep Top-K
    selected = combined[:top_k]

    # Restore original order
    selected.sort(

        key=lambda x: conversation.index({

            "speaker": x["speaker"],
            "message": x["message"]

        })

    )

    return selected


# -----------------------------------
# TEST
# -----------------------------------

if __name__ == "__main__":

    conversation = [

        {"speaker":"User","message":"Hello"},

        {"speaker":"User","message":"I have diabetes."},

        {"speaker":"User","message":"I have chest pain."},

        {"speaker":"User","message":"Thank you."},

        {"speaker":"User","message":"Can I take aspirin?"}

    ]

    scores = [

        {"importance":0.10},

        {"importance":0.95},

        {"importance":0.98},

        {"importance":0.05},

        {"importance":1.00}

    ]

    context = build_context(

        conversation,

        scores,

        top_k=3

    )

    print(json.dumps(context, indent=4))