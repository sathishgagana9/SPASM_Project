import os
import sys
import csv
import time

# -------------------------------------------------------
# Add project root
# -------------------------------------------------------

PROJECT_ROOT = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        ".."
    )
)

sys.path.insert(0, PROJECT_ROOT)

# -------------------------------------------------------

from adaptive_context.adaptive_context_engine import AdaptiveContextEngine
from metrics import EvaluationMetrics

# -------------------------------------------------------

engine = AdaptiveContextEngine()

metrics = EvaluationMetrics()

persona = {

    "role": "Doctor",

    "tone": "Professional",

    "goal": "Help patients"

}

conversation = [

    "I have diabetes.",

    "My sugar level is 320.",

    "Can I take insulin?",

    "I feel dizzy.",

    "What should I eat?"

]

# -------------------------------------------------------

for message in conversation:

    print("=" * 60)
    print("USER :", message)

    try:

        start = time.time()

        result = engine.process(

            persona,

            message

        )

        end = time.time()

        result["conversation"] = engine.conversation

        metrics.add(

            persona,

            len(engine.conversation),

            result,

            end - start

        )

        print("✓ Success")

    except Exception as e:

        print("✗ Failed")

        print(e)

        break

# -------------------------------------------------------

rows = metrics.summary()

os.makedirs("evaluation1", exist_ok=True)

if len(rows) > 0:

    with open(

        "evaluation1/results.csv",

        "w",

        newline=""

    ) as f:

        writer = csv.DictWriter(

            f,

            fieldnames=rows[0].keys()

        )

        writer.writeheader()

        writer.writerows(rows)

    print("\nEvaluation Finished")

    print(f"Saved {len(rows)} records")

else:

    print("\nNo results were generated.")