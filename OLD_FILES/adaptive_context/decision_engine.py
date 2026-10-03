import json


class DecisionEngine:

    def __init__(self):
        pass

    def decide(
        self,
        persona,
        analysis,
        importance,
        risk,
        graph_context
    ):

        decision = {

            "strategy": "GENERAL_GUIDANCE",

            "execution_mode": "FAST",

            "use_memory": False,

            "use_graph": False,

            "need_clarification": False,

            "repair_persona": False,

            "optimize_response": True,

            "allow_llm": True,

            "fallback_response": ""

        }

        # --------------------------------------------------
        # Memory Decision
        # --------------------------------------------------

        if (
            importance["importance"] >= 0.60
            and len(graph_context) > 0
        ):
            decision["use_memory"] = True

        # --------------------------------------------------
        # Graph Decision
        # --------------------------------------------------

        if len(graph_context) >= 2:
            decision["use_graph"] = True

        # --------------------------------------------------
        # Clarification Decision
        # --------------------------------------------------

        if (
            analysis["confidence"] < 0.60
            or analysis["intent"] == "Unknown"
        ):
            decision["need_clarification"] = True

        # --------------------------------------------------
        # Persona Repair
        # --------------------------------------------------

        if risk["risk"] in ["High", "Critical"]:
            decision["repair_persona"] = True

        # --------------------------------------------------
        # Persona Domain Policy
        # --------------------------------------------------

        allowed_domains = {

            "Doctor": [
                "Healthcare"
            ],

            "Teacher": [
                "Education",
                "Programming",
                "Mathematics"
            ],

            "Lawyer": [
                "Law"
            ],

            "Travel Guide": [
                "Travel"
            ]
        }

        role = persona["role"].strip()
        domain = analysis["domain"].strip()

        print("\n========== PERSONA POLICY ==========")
        print("Role :", role)
        print("Detected Domain :", domain)
        print("Allowed Domains :", allowed_domains.get(role, []))
        print("====================================")

        # --------------------------------------------------
        # Strict Persona Check
        # --------------------------------------------------

        if role in allowed_domains:

            if domain not in allowed_domains[role]:

                return {

                    "strategy": "OUT_OF_DOMAIN",

                    "execution_mode": "FAST",

                    "use_memory": False,

                    "use_graph": False,

                    "need_clarification": False,

                    "repair_persona": False,

                    "optimize_response": False,

                    "allow_llm": False,

                    "fallback_response":
                        f"I am currently acting as a {role}. "
                        f"Your question belongs to the {domain} domain, "
                        f"which is outside my assigned persona. "
                        f"Please switch to the appropriate persona."

                }

        # --------------------------------------------------
        # Response Strategy
        # --------------------------------------------------

        if risk["risk"] == "Critical":

            decision["strategy"] = "EMERGENCY"

        elif (
            analysis["intent"] in [
                "Report Symptom",
                "Seek Medical Advice"
            ]
            or analysis["category"] == "Medical History"
        ):

            decision["strategy"] = "ASK_AND_GUIDE"

        elif risk["risk"] == "High":

            decision["strategy"] = "REFER_SPECIALIST"

        else:

            decision["strategy"] = "GENERAL_GUIDANCE"

        # --------------------------------------------------
        # Execution Mode
        # --------------------------------------------------

        if (
            risk["risk"] in ["High", "Critical"]
            or analysis["category"] in ["Medical History", "Complaint"]
            or decision["need_clarification"]
        ):

            decision["execution_mode"] = "FULL"

        else:

            decision["execution_mode"] = "FAST"

        return decision


# --------------------------------------------------
# TEST
# --------------------------------------------------

if __name__ == "__main__":

    engine = DecisionEngine()

    persona = {
        "role": "Teacher"
    }

    analysis = {
        "domain": "Cooking",
        "confidence": 0.95,
        "intent": "Ask Information",
        "category": "Question"
    }

    importance = {
        "importance": 0.91
    }

    risk = {
        "risk": "Low"
    }

    graph = []

    print(
        json.dumps(
            engine.decide(
                persona,
                analysis,
                importance,
                risk,
                graph
            ),
            indent=4
        )
    )