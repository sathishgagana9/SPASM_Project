import random

def generate_persona():

    occupation_role_map = {

        "Doctor": "Healthcare",
        "Psychologist": "Healthcare",

        "Teacher": "Education",
        "Professor": "Education",

        "Bank Manager": "Finance",

        "Lawyer": "Legal",

        "Travel Guide": "Travel",
        "Pilot": "Travel",

        "Police Officer": "Government",
        "Civil Servant": "Government",

        "Software Engineer": "Technology",
        "Data Scientist": "Technology",

        "Salesperson": "Customer Service",
        "Shop Owner": "Customer Service"
    }

    occupation_context_map = {

        "Doctor": [
            "Health Issues",
            "Mental Health Issues"
        ],

        "Psychologist": [
            "Mental Health Issues",
            "Relationship Problems"
        ],

        "Teacher": [
            "Exam Stress",
            "Career Problems"
        ],

        "Professor": [
            "Exam Stress",
            "Career Problems"
        ],

        "Bank Manager": [
            "Investment Decisions",
            "Customer Complaints",
            "Tax Issues"
        ],

        "Lawyer": [
            "Legal Dispute",
            "Tax Issues"
        ],

        "Travel Guide": [
            "Travel Planning",
            "Visa Problems"
        ],

        "Police Officer": [
            "Legal Dispute"
        ],

        "Software Engineer": [
            "Career Problems"
        ],

        "Data Scientist": [
            "Career Problems"
        ],

        "Salesperson": [
            "Customer Complaints"
        ],

        "Shop Owner": [
            "Customer Complaints",
            "Investment Decisions"
        ],

        "Pilot": [
            "Travel Planning",
            "Visa Problems"
        ],

        "Civil Servant": [
            "Legal Dispute",
            "Tax Issues"
        ]
    }

    locations = [
        "Chennai",
        "Bangalore",
        "Mumbai",
        "Delhi",
        "Singapore",
        "London",
        "New York",
        "Paris",
        "Berlin",
        "Dubai"
    ]

    emotions = [
        "Happy",
        "Sad",
        "Anxious",
        "Calm",
        "Frustrated",
        "Excited",
        "Lonely",
        "Confused"
    ]

    emotion_intensity = [
        "Mild",
        "Moderate",
        "Severe"
    ]

    expressiveness = [
        "Low",
        "Medium",
        "High"
    ]

    self_disclosure = [
        "Low",
        "Medium",
        "High"
    ]

    politeness_style = [
        "Formal",
        "Neutral",
        "Casual",
        "Blunt"
    ]

    assertiveness = [
        "Low",
        "Medium",
        "High"
    ]

    occupation = random.choice(
        list(occupation_role_map.keys())
    )

    role_type = occupation_role_map[
        occupation
    ]

    context = random.choice(
        occupation_context_map[
            occupation
        ]
    )

    persona = {

        "role_type":
            role_type,

        "age":
            random.choice(
                [20, 25, 30, 35, 40, 45, 50, 55, 60]
            ),

        "occupation":
            occupation,

        "location":
            random.choice(
                locations
            ),

        "emotion":
            random.choice(
                emotions
            ),

        "context":
            context,

        "emotion_intensity":
            random.choice(
                emotion_intensity
            ),

        "expressiveness":
            random.choice(
                expressiveness
            ),

        "self_disclosure":
            random.choice(
                self_disclosure
            ),

        "politeness_style":
            random.choice(
                politeness_style
            ),

        "assertiveness":
            random.choice(
                assertiveness
            )
    }

    return persona


if __name__ == "__main__":

    persona = generate_persona()

    print("\nGenerated Persona:")
    print(persona)