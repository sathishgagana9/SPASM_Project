import random

def generate_scenario():

    scenarios = [

        ("Doctor", "Patient"),

        ("Psychologist", "Patient"),

        ("Teacher", "Student"),

        ("Lawyer", "Client"),

        ("Bank Manager", "Customer"),

        ("Travel Guide", "Tourist"),

        ("Career Advisor", "Job Seeker"),

        ("Support Agent", "Customer Support User")
    ]

    return random.choice(scenarios)