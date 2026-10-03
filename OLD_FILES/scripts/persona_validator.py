def validate_persona(persona):

    required_fields = [

        "role_type",
        "age",
        "occupation",
        "location",
        "emotion",
        "context",
        "emotion_intensity",
        "expressiveness",
        "self_disclosure",
        "politeness_style",
        "assertiveness"
    ]

    # -----------------------------
    # Check Required Fields
    # -----------------------------

    for field in required_fields:

        if field not in persona:
            return False

        if persona[field] is None:
            return False

    # -----------------------------
    # Occupation → Role Validation
    # -----------------------------

    valid_roles = {

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

    occupation = persona["occupation"]
    role_type = persona["role_type"]

    if occupation in valid_roles:

        if valid_roles[occupation] != role_type:
            return False

    # -----------------------------
    # Occupation → Context Validation
    # -----------------------------

    valid_contexts = {

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

        "Pilot": [
            "Travel Planning",
            "Visa Problems"
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

        "Police Officer": [
            "Legal Dispute"
        ],

        "Civil Servant": [
            "Legal Dispute",
            "Tax Issues"
        ]
    }

    context = persona["context"]

    if occupation in valid_contexts:

        if context not in valid_contexts[occupation]:
            return False

    # -----------------------------
    # Age Validation
    # -----------------------------

    age = persona["age"]

    if age < 20 or age > 60:
        return False

    return True


if __name__ == "__main__":

    sample = {

        "role_type": "Healthcare",

        "age": 30,

        "occupation": "Doctor",

        "location": "Bangalore",

        "emotion": "Anxious",

        "context": "Health Issues",

        "emotion_intensity": "Severe",

        "expressiveness": "High",

        "self_disclosure": "Medium",

        "politeness_style": "Formal",

        "assertiveness": "High"
    }

    print(
        validate_persona(sample)
    )