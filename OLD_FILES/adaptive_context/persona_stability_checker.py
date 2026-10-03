import json


class PersonaStabilityChecker:

    def __init__(self):

        self.weights = {
            "role": 0.30,
            "tone": 0.15,
            "goal": 0.25,
            "memory": 0.15,
            "context": 0.15
        }

    # -------------------------------------
    # Helper
    # -------------------------------------

    def similarity(self, expected, actual):

        expected = expected.lower().strip()
        actual = actual.lower().strip()

        if expected == "":
            return 1.0

        if expected in actual:
            return 1.0

        words = expected.split()

        matches = 0

        for word in words:
            if word in actual:
                matches += 1

        return round(matches / max(len(words), 1), 2)

    # -------------------------------------
    # Role Score
    # -------------------------------------

    def role_score(self, persona, reply):

        return self.similarity(
            persona["role"],
            reply
        )

    # -------------------------------------
    # Tone Score
    # -------------------------------------

    def tone_score(self, persona, reply):

        tone = persona["tone"].lower()
        reply = reply.lower()

        professional = [
            "recommend",
            "suggest",
            "please",
            "consult",
            "advise",
            "consider"
        ]

        friendly = [
            "happy",
            "glad",
            "😊",
            "great",
            "awesome"
        ]

        if tone == "professional":

            count = sum(
                1 for word in professional
                if word in reply
            )

            return min(count / 4, 1.0)

        if tone == "friendly":

            count = sum(
                1 for word in friendly
                if word in reply
            )

            return min(count / 4, 1.0)

        return 0.80

    # -------------------------------------
    # Goal Score
    # -------------------------------------

    def goal_score(self, persona, reply):

        return self.similarity(
            persona["goal"],
            reply
        )

    # -------------------------------------
    # Memory Score
    # -------------------------------------

    def memory_score(self, graph_context, reply):

        if len(graph_context) == 0:
            return 1.0

        count = 0

        reply = reply.lower()

        for item in graph_context:

            if item.lower() in reply:
                count += 1

        return round(
            count / len(graph_context),
            2
        )

    # -------------------------------------
    # Context Score
    # -------------------------------------

    def context_score(self, selected_context, reply):

        if len(selected_context) == 0:
            return 1.0

        reply = reply.lower()

        total = 0
        matched = 0

        for item in selected_context:

            words = item["message"].lower().split()

            total += len(words)

            for word in words:

                if word in reply:
                    matched += 1

        return round(
            matched / max(total, 1),
            2
        )

    # -------------------------------------
    # Final Stability
    # -------------------------------------

    def evaluate(
        self,
        persona,
        reply,
        selected_context,
        graph_context
    ):

        role = self.role_score(
            persona,
            reply
        )

        tone = self.tone_score(
            persona,
            reply
        )

        goal = self.goal_score(
            persona,
            reply
        )

        memory = self.memory_score(
            graph_context,
            reply
        )

        context = self.context_score(
            selected_context,
            reply
        )

        stability = (
            role * self.weights["role"] +
            tone * self.weights["tone"] +
            goal * self.weights["goal"] +
            memory * self.weights["memory"] +
            context * self.weights["context"]
        )

        return {

            "role": round(role, 2),

            "tone": round(tone, 2),

            "goal": round(goal, 2),

            "memory": round(memory, 2),

            "context": round(context, 2),

            "stability": round(stability, 2)

        }


# ------------------------------------------
# TEST
# ------------------------------------------

if __name__ == "__main__":

    checker = PersonaStabilityChecker()

    persona = {

        "role": "Doctor",

        "tone": "Professional",

        "goal": "Help patients"

    }

    graph = [

        "Diabetes",

        "Blood Sugar"

    ]

    context = [

        {

            "message":"I have diabetes."

        }

    ]

    reply = """
As a doctor,
I recommend monitoring your blood sugar
and consulting your physician.
"""

    result = checker.evaluate(

        persona,

        reply,

        context,

        graph

    )

    print(

        json.dumps(

            result,

            indent=4

        )

    )