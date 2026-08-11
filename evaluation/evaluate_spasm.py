import os
import sys
import json
import time


# ============================================================
# Add Project Root to Python Path
# ============================================================

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


# ============================================================
# Import SPASM++ Engine
# ============================================================

from adaptive_context.adaptive_context_engine import AdaptiveContextEngine


# ============================================================
# Load Benchmark Dataset
# ============================================================

BENCHMARK_PATH = os.path.join(
    CURRENT_DIR,
    "benchmark_dataset.json"
)

with open(BENCHMARK_PATH, "r", encoding="utf-8") as f:
    benchmark = json.load(f)


# ============================================================
# Evaluation Variables
# ============================================================

results = []

domain_correct = 0
intent_correct = 0
risk_correct = 0
strategy_correct = 0

total_time = 0.0


# ============================================================
# Start Evaluation
# ============================================================

print("=" * 70)
print("Running SPASM++ Evaluation")
print("=" * 70)

print(f"Total Benchmark Samples: {len(benchmark)}")
print()


# ============================================================
# Evaluate Each Benchmark Sample
# ============================================================

for sample in benchmark:

    print("-" * 70)

    # --------------------------------------------------------
    # Create a fresh engine for every benchmark sample
    # --------------------------------------------------------

    engine = AdaptiveContextEngine()


    # --------------------------------------------------------
    # Persona
    # --------------------------------------------------------

    persona = {
        "role": sample["persona"],
        "tone": "Professional",
        "goal": "Help User"
    }


    # --------------------------------------------------------
    # Query
    # --------------------------------------------------------

    query = sample["query"]


    # --------------------------------------------------------
    # Expected Answer
    # --------------------------------------------------------

    expected = sample["expected"]


    # --------------------------------------------------------
    # Start Timer
    # --------------------------------------------------------

    start = time.time()


    # --------------------------------------------------------
    # Run SPASM++
    # --------------------------------------------------------

    output = engine.process(
        persona,
        query
    )


    # --------------------------------------------------------
    # Response Time
    # --------------------------------------------------------

    elapsed = time.time() - start

    total_time += elapsed


    # ========================================================
    # Get Predictions
    # ========================================================

    predicted_domain = output["analysis"].get(
        "domain",
        ""
    )

    predicted_intent = output["analysis"].get(
        "intent",
        ""
    )

    predicted_risk = output["risk"].get(
        "risk",
        ""
    )

    predicted_strategy = output["decision"].get(
        "strategy",
        ""
    )


    # ========================================================
    # Compare With Expected
    # ========================================================

    expected_domain = expected.get(
        "domain",
        ""
    )

    expected_intent = expected.get(
        "intent",
        ""
    )

    expected_risk = expected.get(
        "risk",
        ""
    )

    expected_strategy = expected.get(
        "strategy",
        ""
    )


    domain_ok = (
        predicted_domain.lower()
        == expected_domain.lower()
    )

    intent_ok = (
        predicted_intent.lower()
        == expected_intent.lower()
    )

    risk_ok = (
        predicted_risk.lower()
        == expected_risk.lower()
    )

    strategy_ok = (
        predicted_strategy.lower()
        == expected_strategy.lower()
    )


    # ========================================================
    # Update Counters
    # ========================================================

    if domain_ok:
        domain_correct += 1

    if intent_ok:
        intent_correct += 1

    if risk_ok:
        risk_correct += 1

    if strategy_ok:
        strategy_correct += 1


    # ========================================================
    # Store Result
    # ========================================================

    results.append({

        "id": sample.get("id"),

        "persona": sample.get(
            "persona",
            ""
        ),

        "query": query,

        "expected": {
            "domain": expected_domain,
            "intent": expected_intent,
            "risk": expected_risk,
            "strategy": expected_strategy
        },

        "predicted": {
            "domain": predicted_domain,
            "intent": predicted_intent,
            "risk": predicted_risk,
            "strategy": predicted_strategy
        },

        "correct": {
            "domain": domain_ok,
            "intent": intent_ok,
            "risk": risk_ok,
            "strategy": strategy_ok
        },

        "response_time": round(
            elapsed,
            2
        )

    })


    # ========================================================
    # Print Current Result
    # ========================================================

    print(
        f"[{sample.get('id', 0):03d}] "
        f"{query[:45]:45} "
        f"Domain:{domain_ok} "
        f"Intent:{intent_ok} "
        f"Risk:{risk_ok} "
        f"Strategy:{strategy_ok} "
        f"Time:{elapsed:.2f}s"
    )


# ============================================================
# Calculate Accuracy
# ============================================================

n = len(benchmark)

if n > 0:

    domain_accuracy = (
        domain_correct / n
    ) * 100

    intent_accuracy = (
        intent_correct / n
    ) * 100

    risk_accuracy = (
        risk_correct / n
    ) * 100

    strategy_accuracy = (
        strategy_correct / n
    ) * 100

    average_response_time = (
        total_time / n
    )

else:

    domain_accuracy = 0
    intent_accuracy = 0
    risk_accuracy = 0
    strategy_accuracy = 0
    average_response_time = 0


# ============================================================
# Evaluation Summary
# ============================================================

summary = {

    "total_samples": n,

    "domain_accuracy": round(
        domain_accuracy,
        2
    ),

    "intent_accuracy": round(
        intent_accuracy,
        2
    ),

    "risk_accuracy": round(
        risk_accuracy,
        2
    ),

    "strategy_accuracy": round(
        strategy_accuracy,
        2
    ),

    "average_response_time": round(
        average_response_time,
        2
    )

}


# ============================================================
# Save Detailed Results
# ============================================================

RESULTS_PATH = os.path.join(
    CURRENT_DIR,
    "results.json"
)

with open(
    RESULTS_PATH,
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        results,
        f,
        indent=4
    )


# ============================================================
# Save Summary
# ============================================================

SUMMARY_PATH = os.path.join(
    CURRENT_DIR,
    "summary.json"
)

with open(
    SUMMARY_PATH,
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        summary,
        f,
        indent=4
    )


# ============================================================
# Print Final Report
# ============================================================

print()
print("=" * 70)
print("SPASM++ EVALUATION REPORT")
print("=" * 70)

print(
    f"Total Samples           : {n}"
)

print(
    f"Domain Accuracy         : "
    f"{domain_accuracy:.2f}%"
)

print(
    f"Intent Accuracy         : "
    f"{intent_accuracy:.2f}%"
)

print(
    f"Risk Accuracy           : "
    f"{risk_accuracy:.2f}%"
)

print(
    f"Strategy Accuracy       : "
    f"{strategy_accuracy:.2f}%"
)

print(
    f"Average Response Time   : "
    f"{average_response_time:.2f} sec"
)

print("=" * 70)

print()
print("Saved files:")
print("  results.json")
print("  summary.json")
print()