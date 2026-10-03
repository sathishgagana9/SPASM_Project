import json


class ImportanceScorer:

    def __init__(self):

        self.category_weight = {

            "Greeting":0.20,
            "User State":0.95,
            "User Goal":0.95,
            "Task":0.90,
            "Emotion":0.75,
            "Persona Information":0.85,
            "Closing":0.10,
            "Small Talk":0.20,
            "Other":0.30

        }

        self.urgency_weight = {

            "Low":0.20,
            "Medium":0.50,
            "High":0.85,
            "Critical":1.00

        }

        self.domain_weight = {

            "Healthcare":1.00,
            "Education":0.80,
            "Law":0.90,
            "Programming":0.80,
            "Travel":0.70,
            "Customer Support":0.75,
            "General":0.50

        }

    def score(self, analysis):

        category = analysis["category"]

        urgency = analysis.get("urgency", "Low")

        domain = analysis["domain"]

        persona_match = analysis["persona_match"]

        dependency = analysis["dependency"]

        novelty = analysis["novel_information"]

        confidence = analysis["confidence"]

        category_score = self.category_weight.get(category,0.30)

        urgency_score = self.urgency_weight.get(urgency,0.30)

        domain_score = self.domain_weight.get(domain,0.50)

        dependency_score = 1.0 if dependency else 0.50

        novelty_score = 1.0 if novelty else 0.30

        final_score = (

            0.25 * category_score +

            0.20 * urgency_score +

            0.20 * persona_match +

            0.15 * dependency_score +

            0.10 * novelty_score +

            0.05 * domain_score +

            0.05 * confidence

        )

        return {

            "category_score":round(category_score,2),

            "urgency_score":round(urgency_score,2),

            "domain_score":round(domain_score,2),

            "dependency_score":round(dependency_score,2),

            "novelty_score":round(novelty_score,2),

            "persona_match":round(persona_match,2),

            "confidence":round(confidence,2),

            "importance":round(final_score,2)

        }


if __name__=="__main__":

    scorer = ImportanceScorer()

    analysis = {

        "category":"User Goal",

        "intent":"Emergency Health Concern",

        "emotion":"Concerned",

        "urgency":"High",

        "domain":"Healthcare",

        "entities":[],

        "keywords":["chest pain"],

        "dependency":False,

        "novel_information":True,

        "persona_match":0.95,

        "confidence":0.95

    }

    result = scorer.score(analysis)

    print(json.dumps(result,indent=4))