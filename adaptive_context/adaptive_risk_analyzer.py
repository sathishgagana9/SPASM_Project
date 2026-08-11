import json


class AdaptiveRiskAnalyzer:

    def __init__(self):
        pass

    def analyze(self, semantic_context, tracker_state):

        risk = {
            "risk": "Low",
            "priority": 0.20,
            "reason": "No significant risk detected."
        }

        # ---------------------------------------------------
        # Information
        # ---------------------------------------------------

        slots = semantic_context.get("semantic_slots", {})

        intent = semantic_context.get("intent", "")

        urgency = semantic_context.get("urgency", "Low")

        symptom = (
            tracker_state.get("symptom")
            or slots.get("symptom")
            or ""
        ).lower()

        condition = (
            tracker_state.get("condition")
            or slots.get("condition")
            or ""
        ).lower()

        temperature = (
            tracker_state.get("temperature")
            or slots.get("temperature")
        )

        breathing = (
            tracker_state.get("breathing_problem")
            or slots.get("breathing_problem")
        )

        chest_pain = (
            tracker_state.get("chest_pain")
            or slots.get("chest_pain")
        )

        medicine = (
            tracker_state.get("medicine")
            or slots.get("medicine")
        )

        # ---------------------------------------------------
        # Critical Risk
        # ---------------------------------------------------

        if chest_pain and breathing:

            return {

                "risk": "Critical",

                "priority": 1.00,

                "reason":
                "Chest pain with breathing difficulty."

            }

        if symptom == "chest pain" and breathing:

            return {

                "risk": "Critical",

                "priority": 1.00,

                "reason":
                "Chest pain with breathing difficulty."

            }

        # ---------------------------------------------------
        # Temperature
        # ---------------------------------------------------

        if temperature:

            try:

                temp = float(str(temperature).replace("°", ""))

                if temp >= 104:

                    return {

                        "risk": "Critical",

                        "priority": 1.00,

                        "reason":
                        "Very high temperature."

                    }

                elif temp >= 102:

                    risk["risk"] = "High"

                    risk["priority"] = 0.80

                    risk["reason"] = "High fever."

            except:

                pass

        # ---------------------------------------------------
        # Chest Pain
        # ---------------------------------------------------

        if symptom == "chest pain" or chest_pain:

            risk["risk"] = "High"

            risk["priority"] = 0.90

            risk["reason"] = "Chest pain requires prompt attention."

        # ---------------------------------------------------
        # Serious Conditions
        # ---------------------------------------------------

        dangerous_conditions = [

            "heart attack",

            "stroke",

            "diabetes",

            "hypertension",

            "cancer"

        ]

        if condition in dangerous_conditions:

            if risk["priority"] < 0.70:

                risk["risk"] = "Medium"

                risk["priority"] = 0.60

                risk["reason"] = (
                    f"Known medical condition: {condition}."
                )

        # ---------------------------------------------------
        # Medicine Request
        # ---------------------------------------------------

        if intent == "Medicine Request":

            if not symptom:

                risk["risk"] = "Medium"

                risk["priority"] = 0.50

                risk["reason"] = (
                    "Medicine requested before symptom identified."
                )

        # ---------------------------------------------------
        # Urgency
        # ---------------------------------------------------

        if urgency == "High":

            if risk["priority"] < 0.80:

                risk["risk"] = "High"

                risk["priority"] = 0.80

                risk["reason"] = (
                    "High urgency detected."
                )

        elif urgency == "Critical":

            risk["risk"] = "Critical"

            risk["priority"] = 1.00

            risk["reason"] = (
                "Critical urgency detected."
            )

        return risk


# ----------------------------------------------------
# TEST
# ----------------------------------------------------

if __name__ == "__main__":

    analyzer = AdaptiveRiskAnalyzer()

    tests = [

        (

            {

                "intent": "Report Symptom",

                "urgency": "Low",

                "semantic_slots": {

                    "symptom": "fever"

                }

            },

            {

                "symptom": "fever"

            }

        ),

        (

            {

                "intent": "Report Symptom",

                "urgency": "Medium",

                "semantic_slots": {

                    "symptom": "chest pain",

                    "breathing_problem": True

                }

            },

            {

                "symptom": "chest pain",

                "breathing_problem": True

            }

        ),

        (

            {

                "intent": "Report Symptom",

                "urgency": "Medium",

                "semantic_slots": {

                    "temperature": "104"

                }

            },

            {

                "temperature": "104"

            }

        ),

        (

            {

                "intent": "Medicine Request",

                "urgency": "Low",

                "semantic_slots": {}

            },

            {}

        )

    ]

    for semantic, tracker in tests:

        print("\n==============================")

        print(json.dumps(

            analyzer.analyze(

                semantic,

                tracker

            ),

            indent=4

        ))