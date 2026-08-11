import json
import random

doctor_cases = [
    {
        "query": "I have fever for two days.",
        "domain": "Healthcare",
        "intent": "Report Symptom",
        "risk": "Low",
        "strategy": "ASK_AND_GUIDE"
    },
    {
        "query": "My temperature is 104 degrees.",
        "domain": "Healthcare",
        "intent": "Report Symptom",
        "risk": "Critical",
        "strategy": "EMERGENCY"
    },
    {
        "query": "I have chest pain.",
        "domain": "Healthcare",
        "intent": "Report Symptom",
        "risk": "High",
        "strategy": "REFER_SPECIALIST"
    },
    {
        "query": "Suggest medicine for headache.",
        "domain": "Healthcare",
        "intent": "Medicine Request",
        "risk": "Medium",
        "strategy": "ASK_AND_GUIDE"
    },
    {
        "query": "I have diabetes.",
        "domain": "Healthcare",
        "intent": "Provide Information",
        "risk": "Medium",
        "strategy": "ASK_AND_GUIDE"
    }
]

teacher_cases = [
    {
        "query": "Explain recursion.",
        "domain": "Programming",
        "intent": "Request Explanation",
        "risk": "Low",
        "strategy": "GENERAL_GUIDANCE"
    },
    {
        "query": "Explain binary search.",
        "domain": "Programming",
        "intent": "Request Explanation",
        "risk": "Low",
        "strategy": "GENERAL_GUIDANCE"
    },
    {
        "query": "Explain Chitradurga history.",
        "domain": "History",
        "intent": "Request Explanation",
        "risk": "Low",
        "strategy": "GENERAL_GUIDANCE"
    },
    {
        "query": "What is Newton's First Law?",
        "domain": "Physics",
        "intent": "Request Explanation",
        "risk": "Low",
        "strategy": "GENERAL_GUIDANCE"
    },
    {
        "query": "How to make biryani?",
        "domain": "Cooking",
        "intent": "Request Instructions",
        "risk": "Low",
        "strategy": "OUT_OF_DOMAIN"
    }
]

lawyer_cases = [
    {
        "query": "Can my landlord evict me without notice?",
        "domain": "Legal",
        "intent": "Legal Advice",
        "risk": "Medium",
        "strategy": "GENERAL_GUIDANCE"
    },
    {
        "query": "How do I file an FIR?",
        "domain": "Legal",
        "intent": "Legal Advice",
        "risk": "Low",
        "strategy": "GENERAL_GUIDANCE"
    }
]

travel_cases = [
    {
        "query": "Plan a 3-day trip to Mysore.",
        "domain": "Travel",
        "intent": "Travel Planning",
        "risk": "Low",
        "strategy": "GENERAL_GUIDANCE"
    },
    {
        "query": "Best places to visit in Goa.",
        "domain": "Travel",
        "intent": "Travel Planning",
        "risk": "Low",
        "strategy": "GENERAL_GUIDANCE"
    }
]


dataset = []
id_counter = 1


def add_cases(persona, cases, repeat):
    global id_counter

    for _ in range(repeat):

        case = random.choice(cases)

        dataset.append({

            "id": id_counter,

            "persona": persona,

            "query": case["query"],

            "expected": {

                "domain": case["domain"],

                "intent": case["intent"],

                "risk": case["risk"],

                "strategy": case["strategy"]

            }

        })

        id_counter += 1


# Generate approximately 120 samples

add_cases("Doctor", doctor_cases, 40)

add_cases("Teacher", teacher_cases, 40)

add_cases("Lawyer", lawyer_cases, 20)

add_cases("Travel Guide", travel_cases, 20)


with open("benchmark_dataset.json", "w", encoding="utf-8") as f:

    json.dump(dataset, f, indent=4, ensure_ascii=False)


print("=" * 50)
print("Benchmark Dataset Generated Successfully")
print("Total Samples :", len(dataset))
print("File : benchmark_dataset.json")
print("=" * 50)