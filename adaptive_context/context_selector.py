import json


class AdaptiveContextSelector:

    def __init__(self, memory_budget=5):
        self.memory_budget = memory_budget

    # --------------------------------------------------
    # Risk Score
    # --------------------------------------------------

    def risk_score(self, risk):

        scores = {
            "Low": 0.30,
            "Medium": 0.60,
            "High": 0.90,
            "Critical": 1.00
        }

        return scores.get(risk, 0.50)

    # --------------------------------------------------
    # Recency Score
    # --------------------------------------------------

    def recency_score(self, index, total):

        if total <= 1:
            return 1.0

        return round((index + 1) / total, 2)

    # --------------------------------------------------
    # Adaptive Context Selection
    # --------------------------------------------------

    def select(
        self,
        conversation,
        analysis_history,
        importance_history,
        dependency,
        novelty,
        risk_history
    ):

        memory = []

        # -----------------------------------------
        # Only USER messages
        # -----------------------------------------

        user_messages = [
            msg
            for msg in conversation
            if msg["speaker"] == "User"
        ]

        total = min(

            len(user_messages),

            len(analysis_history),

            len(importance_history),

            len(risk_history),

            len(novelty.get("novelty", []))

        )

        if total == 0:
            return []

        # -----------------------------------------
        # Build Adaptive Memory
        # -----------------------------------------

        for i in range(total):

            importance = importance_history[i].get(
                "importance",
                0.5
            )

            risk = self.risk_score(

                risk_history[i].get(
                    "risk",
                    "Low"
                )

            )

            recency = self.recency_score(

                i,

                total

            )

            novel = (

                1.0

                if novelty["novelty"][i].get(
                    "novel",
                    False
                )

                else 0.4

            )

            dependency_bonus = 0.10

            if i < len(dependency.get("dependencies", [])):

                if dependency["dependencies"][i].get(
                    "depends_on",
                    []
                ):

                    dependency_bonus = 0.20

            memory_score = (

                importance * 0.45 +

                risk * 0.25 +

                recency * 0.15 +

                novel * 0.10 +

                dependency_bonus * 0.05

            )

            memory.append({

                "turn": i + 1,

                "speaker": user_messages[i]["speaker"],

                "message": user_messages[i]["message"],

                "importance": round(

                    importance,

                    2

                ),

                "risk": risk_history[i]["risk"],

                "memory_score": round(

                    memory_score,

                    2

                ),

                "category": analysis_history[i]["category"]

            })

        # -----------------------------------------
        # Rank Memory
        # -----------------------------------------

        memory.sort(

            key=lambda x: x["memory_score"],

            reverse=True

        )

        selected = memory[:self.memory_budget]

        # -----------------------------------------
        # Always Keep Latest User Message
        # -----------------------------------------

        latest = memory[-1]

        exists = any(

            item["turn"] == latest["turn"]

            for item in selected

        )

        if not exists:

            selected.append(

                latest

            )

        # -----------------------------------------
        # Restore Conversation Order
        # -----------------------------------------

        selected.sort(

            key=lambda x: x["turn"]

        )

        return selected


# ------------------------------------------------------
# TEST
# ------------------------------------------------------

if __name__ == "__main__":

    selector = AdaptiveContextSelector(memory_budget=3)

    conversation = [

        {"speaker":"User","message":"Hello"},

        {"speaker":"Assistant","message":"Hello"},

        {"speaker":"User","message":"I have diabetes."},

        {"speaker":"Assistant","message":"Okay."},

        {"speaker":"User","message":"My sugar level is 320."},

        {"speaker":"Assistant","message":"That is high."},

        {"speaker":"User","message":"Can I take insulin?"}

    ]

    analysis = [

        {"category":"Greeting"},

        {"category":"Medical History"},

        {"category":"Complaint"},

        {"category":"Question"}

    ]

    importance = [

        {"importance":0.20},

        {"importance":0.87},

        {"importance":0.98},

        {"importance":0.91}

    ]

    dependency = {

        "dependencies":[

            {"depends_on":[]},

            {"depends_on":[1]},

            {"depends_on":[2]},

            {"depends_on":[3]}

        ]

    }

    novelty = {

        "novelty":[

            {"novel":True},

            {"novel":True},

            {"novel":True},

            {"novel":False}

        ]

    }

    risk = [

        {"risk":"Low"},

        {"risk":"Low"},

        {"risk":"High"},

        {"risk":"Medium"}

    ]

    result = selector.select(

        conversation,

        analysis,

        importance,

        dependency,

        novelty,

        risk

    )

    print(json.dumps(result, indent=4))