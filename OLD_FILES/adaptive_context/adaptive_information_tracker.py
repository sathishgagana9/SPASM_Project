import json


class AdaptiveInformationTracker:

    def __init__(self):

        self.state = {}

    # -------------------------------------
    # Merge new semantic information
    # -------------------------------------

    def update(self, semantic_result):

        slots = semantic_result.get("slots", {})

        for key, value in slots.items():

            if value is None:
                continue

            if value == "":
                continue

            self.state[key] = value

        return self.state

    # -------------------------------------
    # Return stored information
    # -------------------------------------

    def get_state(self):

        return self.state

    # -------------------------------------
    # Clear conversation
    # -------------------------------------

    def reset(self):

        self.state = {}

    # -------------------------------------
    # Find missing information
    # -------------------------------------

    def missing_slots(self, required_slots):

        missing = []

        for slot in required_slots:

            if slot not in self.state:

                missing.append(slot)

        return missing


# -------------------------------------
# TEST
# -------------------------------------

if __name__ == "__main__":

    tracker = AdaptiveInformationTracker()

    print("\nTURN 1")

    semantic = {

        "slots": {

            "symptom": "fever"

        }

    }

    print(tracker.update(semantic))

    print("\nTURN 2")

    semantic = {

        "slots": {

            "duration": "2 days"

        }

    }

    print(tracker.update(semantic))

    print("\nTURN 3")

    semantic = {

        "slots": {

            "temperature": "102"

        }

    }

    print(tracker.update(semantic))

    print("\nTURN 4")

    semantic = {

        "slots": {

            "medicine": "Crocin"

        }

    }

    print(tracker.update(semantic))

    print("\nCURRENT STATE")

    print(

        json.dumps(

            tracker.get_state(),

            indent=4

        )

    )

    print("\nMISSING")

    print(

        tracker.missing_slots(

            [

                "symptom",

                "duration",

                "temperature",

                "medicine",

                "age"

            ]

        )

    )