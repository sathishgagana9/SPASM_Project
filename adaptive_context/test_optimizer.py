from response_optimizer import AdaptiveResponseOptimizer

optimizer = AdaptiveResponseOptimizer()

persona = {

    "role": "Doctor",

    "tone": "Professional",

    "goal": "Help patients"

}

selected_context = [

    {

        "message": "I have diabetes."

    }

]

responses = [

    "Monitor your blood sugar regularly.",

    "Monitor your blood sugar regularly.",

    "Exercise daily and eat a balanced diet.",

    "Consult your doctor before taking insulin."

]

for r in responses:

    print("\n==============================")

    print("Candidate:")

    print(r)

    result = optimizer.optimize(

        r,

        persona,

        selected_context

    )

    for k, v in result.items():

        print(f"{k:25}: {v}")