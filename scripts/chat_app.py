from adaptive_context.adaptive_context_engine import AdaptiveContextEngine

# ----------------------------------------------------
# Create ONE Global Engine
# ----------------------------------------------------

engine = AdaptiveContextEngine()


def chat(user_message, role, tone, goal):

    persona = {

        "role": role,

        "tone": tone,

        "goal": goal

    }

    # ---------------------------------------------
    # Run SPASM++ Engine
    # ---------------------------------------------

    result = engine.process(

        persona,

        user_message

    )

    # ---------------------------------------------
    # Safe Values
    # ---------------------------------------------

    analysis = result.get("analysis", {})
    importance = result.get("importance", {})
    stability = result.get("persona_stability", {})
    risk = result.get("risk", {})

    # ---------------------------------------------
    # Return JSON for Frontend
    # ---------------------------------------------

    return {

        "reply": result.get("reply", ""),

        "analysis": {

            "category": analysis.get("category", "Unknown"),

            "intent": analysis.get("intent", "General"),

            "emotion": analysis.get("emotion", "Neutral"),

            "urgency": analysis.get("urgency", "Low"),

            "domain": analysis.get("domain", "General")

        },

        "importance": {

            "importance": importance.get("importance", 0)

        },

        "persona_stability": {

            "stability": stability.get("stability", 0)

        },

        "risk": {

            "risk": risk.get("risk", "Low"),

            "priority": risk.get("priority", 0),

            "reason": risk.get("reason", "")

        },

        "graph": result.get("graph_statistics", {}),

        "selected_context": result.get("selected_context", []),

        "graph_context": result.get("graph_context", []),

        "conversation": result.get("conversation", [])

    }


# ----------------------------------------------------
# TEST
# ----------------------------------------------------

if __name__ == "__main__":

    response = chat(

        user_message="I have diabetes.",

        role="Doctor",

        tone="Professional",

        goal="Help patients"

    )

    import json

    print(

        json.dumps(

            response,

            indent=4

        )

    )