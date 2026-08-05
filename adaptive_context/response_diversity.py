import json
import difflib


class ResponseDiversityEngine:

    def __init__(self, threshold=0.85):

        # Similarity threshold
        self.threshold = threshold

        # Store assistant responses
        self.response_history = []

    # --------------------------------------------------
    # Add Assistant Response
    # --------------------------------------------------

    def add_response(self, response):

        if response.strip():

            self.response_history.append(response.strip())

    # --------------------------------------------------
    # Similarity
    # --------------------------------------------------

    def similarity(self, response1, response2):

        return difflib.SequenceMatcher(

            None,

            response1.lower(),

            response2.lower()

        ).ratio()

    # --------------------------------------------------
    # Compare with Previous Responses
    # --------------------------------------------------

    def analyze(self, candidate_response):

        # First response
        if len(self.response_history) == 0:

            return {

                "similarity": 0.0,

                "most_similar": "",

                "is_repeated": False,

                "diversity_score": 1.0

            }

        highest_similarity = 0

        closest_response = ""

        for previous in self.response_history:

            score = self.similarity(

                candidate_response,

                previous

            )

            if score > highest_similarity:

                highest_similarity = score

                closest_response = previous

        repeated = highest_similarity >= self.threshold

        diversity = round(

            1 - highest_similarity,

            2

        )

        return {

            "similarity": round(

                highest_similarity,

                2

            ),

            "most_similar": closest_response,

            "is_repeated": repeated,

            "diversity_score": diversity

        }

    # --------------------------------------------------
    # Process Response
    # --------------------------------------------------

    def process(self, candidate_response):

        result = self.analyze(

            candidate_response

        )

        self.add_response(

            candidate_response

        )

        return result


# ------------------------------------------------------
# TEST
# ------------------------------------------------------

if __name__ == "__main__":

    engine = ResponseDiversityEngine()

    responses = [

        "You should monitor your blood sugar regularly.",

        "Please monitor your blood sugar regularly.",

        "Drink more water.",

        "You should monitor your blood sugar regularly.",

        "Consult your doctor before taking insulin."

    ]

    for r in responses:

        print("\n====================================")

        print("Candidate:")

        print(r)

        result = engine.process(

            r

        )

        print(

            json.dumps(

                result,

                indent=4

            )

        )