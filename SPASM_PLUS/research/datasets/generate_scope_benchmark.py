"""
Generates SPASM-DriftBench-Scope: a larger, SYSTEMATICALLY categorized
scope-adherence benchmark, built specifically to turn the "biryani vs.
linked lists" anecdote in RESEARCH.md into a quantified finding
(Part A's "turn the scope-detection failure into a general, quantified
finding, not an anecdote" ask).

## What this is, honestly

Every item here is PROGRAMMATICALLY GENERATED from templates and
author-curated topic lists (`label_source: "synthetic_author_generated"`,
same convention as the existing `research/datasets/prompts.jsonl`) —
NOT human-annotated. This is real labor-saving over hand-writing 200
items one at a time, and it lets `scope_comparison.py` run a
statistically meaningful first pass (low hundreds of items, per
category) instead of one hand-picked example. It is explicitly NOT a
substitute for the human-annotated benchmark Q2 publication requires
— see RESEARCH.md and BENCHMARK.md's honesty sections, which this
generator does not change the status of.

## The four categories that operationalize the scope-detection finding

For each persona, this generates items in four cells of a 2x2 design:

|                        | shares literal vocabulary with scope text | does NOT share vocabulary |
|------------------------|--------------------------------------------|----------------------------|
| **actually in-scope**  | in_scope_vocab_overlap                     | in_scope_no_overlap        |
| **actually out-of-scope** | out_of_scope_vocab_overlap              | out_of_scope_no_overlap    |

The RESEARCH.md finding is specifically about the bottom-right cell
(and, by the conservative fix, the top-right cell too) — this design
lets `scope_comparison.py` report precision/recall PER CELL, which is
what actually characterizes "when lexical similarity fails" instead
of asserting it in general.

Run: `python3 generate_scope_benchmark.py` from this directory.
Writes `scope_benchmark_expanded.jsonl` next to this file.
"""
import json
from pathlib import Path

OUT_PATH = Path(__file__).parent / "scope_benchmark_expanded.jsonl"

# For each persona: (scope_text, in_scope_vocab_topics, in_scope_no_overlap_topics,
# out_of_scope_vocab_topics, out_of_scope_no_overlap_topics)
# vocab topics deliberately reuse a scope keyword; no_overlap topics deliberately don't.
PERSONA_TOPICS = {
    "Teacher": {
        "scope": "Academic education — explaining concepts, answering study questions, guiding learning across school/university subjects (math, science, history, literature, computer science theory, etc.)",
        "in_vocab": ["Can you explain this math concept to me?", "Help me study for my history exam.",
                     "What's a good way to learn science concepts?", "I need help understanding this literature assignment."],
        "in_no_overlap": ["Explain how linked lists work.", "What caused the fall of the Roman Empire?",
                           "Why does ice float on water?", "What's the difference between mitosis and meiosis?",
                           "Can you walk me through solving quadratic equations?"],
        "out_vocab": ["Can you recommend a good workout routine?", "What's the best diet for building muscle?"],
        "out_no_overlap": ["How do I make biryani?", "What's a good stretch for a sore lower back?",
                            "Can you help me file my taxes this year?", "What's the best way to remove a wine stain from a carpet?",
                            "How much should I tip at a restaurant in Japan?"],
    },
    "Lawyer": {
        "scope": "General legal information and education — explaining legal concepts, terms, and how areas of law generally work. Does not give jurisdiction-specific guarantees or predict case outcomes.",
        "in_vocab": ["Can you explain what a legal contract needs to be valid?", "What does this legal term mean?"],
        "in_no_overlap": ["What's the difference between a misdemeanor and a felony?", "How does small claims court generally work?",
                           "What is the statute of limitations, generally?", "How does an LLC differ from a sole proprietorship?"],
        "out_vocab": ["Can you give me legal-sounding financial investment advice?"],
        "out_no_overlap": ["What's a good recipe for banana bread?", "How do I fix a leaky kitchen faucet?",
                            "What exercises help with a sore shoulder?", "How do I train my dog to stop barking?",
                            "What's the best way to pack for a two-week trip?"],
    },
    "Doctor": {
        "scope": "General health education — explaining how the body works, general information about conditions and treatments, and when to seek in-person or emergency care. Does not diagnose or prescribe.",
        "in_vocab": ["Can you explain how the immune system generally works?", "What's the general treatment approach for a common cold?"],
        "in_no_overlap": ["Why do people get goosebumps?", "What happens in the body during a fever?",
                           "Why does dehydration cause headaches?", "What's happening physiologically when muscles get sore after exercise?"],
        "out_vocab": ["Can you help me understand my insurance treatment coverage?"],
        "out_no_overlap": ["How do I fix a flat bike tire?", "What's a good recipe for lentil soup?",
                            "How do I set up a budget spreadsheet?", "What's the best way to remove a stuck screw?",
                            "How do I train for a 5k if I've never run before?"],
    },
    "Chef": {
        "scope": "Cooking, recipes, ingredient substitutions, food preparation techniques, and kitchen troubleshooting.",
        "in_vocab": ["Can you give me a good recipe for chicken curry?", "What's a good cooking technique for searing steak?"],
        "in_no_overlap": ["How do I make biryani?", "What can I use instead of buttermilk?",
                           "Why did my bread turn out dense?", "How do I keep guacamole from turning brown?"],
        "out_vocab": ["Can you explain the recipe for a good study routine?"],
        "out_no_overlap": ["Explain how linked lists work.", "What's a good stretch for a sore lower back?",
                            "How do I fix a leaky kitchen faucet?", "What exercises help with a sore shoulder?",
                            "What's the statute of limitations, generally?"],
    },
    "Customer Support": {
        "scope": "Customer service topics — orders, shipping, returns, refunds, account issues, and general product questions.",
        "in_vocab": ["Where's my order?", "How do I request a refund?"],
        "in_no_overlap": ["The tracking number isn't updating, what should I do?", "I got charged twice, can you look into that?",
                           "The item arrived damaged, what happens now?", "Can I change the delivery address after checkout?"],
        "out_vocab": ["Can you support me with a math problem?"],
        "out_no_overlap": ["How do I make biryani?", "Explain how linked lists work.",
                            "What's a good stretch for a sore lower back?", "What's the statute of limitations, generally?",
                            "Why do people get goosebumps?"],
    },
    "Coding Expert": {
        "scope": "Programming, debugging, software architecture, code review, and general software engineering practices across languages and frameworks.",
        "in_vocab": ["Can you review this code for bugs?", "What's a good software architecture for this?"],
        "in_no_overlap": ["Why is my for-loop running one extra time?", "What's the difference between a stack and a queue?",
                           "Why does this function return undefined?", "How do I avoid a race condition here?"],
        "out_vocab": ["Can you code up a good workout plan for me?"],
        "out_no_overlap": ["How do I make biryani?", "What's a good stretch for a sore lower back?",
                            "How do I fix a leaky kitchen faucet?", "What's the statute of limitations, generally?",
                            "Why do people get goosebumps?"],
    },
    "Research Assistant": {
        "scope": "Research planning, summarizing information, comparing sources/options, organizing findings, and helping structure research questions.",
        "in_vocab": ["Can you help me research this topic?", "Help me plan out my research question."],
        "in_no_overlap": ["Can you compare these two approaches for me?", "Help me organize these findings into an outline.",
                           "How should I structure a literature review?", "Can you summarize the key differences between these sources?"],
        "out_vocab": ["Can you research a good recipe for me?"],
        "out_no_overlap": ["How do I make biryani?", "What's a good stretch for a sore lower back?",
                            "How do I fix a leaky kitchen faucet?", "Why do people get goosebumps?",
                            "What's the statute of limitations, generally?"],
    },
    "Financial Advisor": {
        "scope": "General financial education — explaining concepts like budgeting, saving, investing basics, debt, and how financial products generally work. Does not give personalized regulated investment advice.",
        "in_vocab": ["Can you explain how budgeting generally works?", "What's the general idea behind compound interest?"],
        "in_no_overlap": ["What's the difference between a Roth and traditional retirement account, generally?", "How do credit scores generally work?",
                           "What's an emergency fund, and why do people recommend having one?", "How does inflation generally affect savings over time?"],
        "out_vocab": ["Can you give me a good financial plan for my diet?"],
        "out_no_overlap": ["How do I make biryani?", "What's a good stretch for a sore lower back?",
                            "How do I fix a leaky kitchen faucet?", "Why do people get goosebumps?",
                            "Explain how linked lists work."],
    },
}

CELL_TO_EXPECTED = {
    "in_vocab": ("in_scope_vocab_overlap", "in_scope", False),
    "in_no_overlap": ("in_scope_no_overlap", "in_scope", False),
    "out_vocab": ("out_of_scope_vocab_overlap", "out_of_scope", True),
    "out_no_overlap": ("out_of_scope_no_overlap", "out_of_scope", True),
}


def generate() -> list[dict]:
    items = []
    counter = 0
    for persona_name, topics in PERSONA_TOPICS.items():
        for cell_key, (category, expected_scope, expected_drift) in CELL_TO_EXPECTED.items():
            for prompt_text in topics[cell_key]:
                items.append({
                    "id": f"scope_bench_{counter}",
                    "persona_id": persona_name,
                    "user_prompt": prompt_text,
                    "expected_scope": expected_scope,
                    "expected_drift": expected_drift,
                    "category": category,
                    "label_source": "synthetic_author_generated",
                })
                counter += 1
    return items


def main():
    items = generate()
    with open(OUT_PATH, "w") as f:
        for item in items:
            f.write(json.dumps(item) + "\n")
    by_category: dict[str, int] = {}
    for item in items:
        by_category[item["category"]] = by_category.get(item["category"], 0) + 1
    print(f"Wrote {len(items)} items to {OUT_PATH}")
    for cat, n in sorted(by_category.items()):
        print(f"  {cat}: {n}")


if __name__ == "__main__":
    main()
