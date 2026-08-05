import json


class ImportanceScorer:

    def __init__(self):
        pass

    # --------------------------------------------------
    # Convert Category to Score
    # --------------------------------------------------

    def category_score(self, category):

        scores = {

            "Greeting":0.10,

            "Small Talk":0.10,

            "Question":0.50,

            "User Goal":0.90,

            "User State":0.90,

            "Medical History":1.00,

            "Complaint":0.95

        }

        return scores.get(category,0.50)

    # --------------------------------------------------
    # Convert Urgency
    # --------------------------------------------------

    def urgency_score(self, urgency):

        scores = {

            "Low":0.20,

            "Medium":0.60,

            "High":0.90,

            "Critical":1.00

        }

        return scores.get(urgency,0.50)

    # --------------------------------------------------
    # Domain Score
    # --------------------------------------------------

    def domain_score(self, domain):

        important_domains = [

            "Healthcare",

            "Medicine",

            "Cardiology",

            "Emergency",

            "Mental Health"

        ]

        if domain in important_domains:

            return 1.0

        if domain == "":

            return 0.40

        return 0.70

    # --------------------------------------------------
    # Emotion Score
    # --------------------------------------------------

    def emotion_score(self, emotion):

        scores = {

            "Neutral":0.50,

            "Happy":0.20,

            "Concerned":1.00,

            "Sad":0.80,

            "Angry":0.70

        }

        return scores.get(emotion,0.50)

    # --------------------------------------------------
    # Main Importance Function
    # --------------------------------------------------

    def score(self, analysis):

        category = self.category_score(

            analysis["category"]

        )

        urgency = self.urgency_score(

            analysis["urgency"]

        )

        domain = self.domain_score(

            analysis["domain"]

        )

        emotion = self.emotion_score(

            analysis["emotion"]

        )

        dependency = 1.0 if analysis["dependency"] else 0.5

        novelty = 1.0 if analysis["novel_information"] else 0.4

        persona = analysis["persona_match"]

        confidence = analysis["confidence"]

        importance = (

            category*0.20 +

            urgency*0.20 +

            domain*0.10 +

            emotion*0.10 +

            dependency*0.10 +

            novelty*0.10 +

            persona*0.10 +

            confidence*0.10

        )

        # ------------------------------------------------
        # Medical History Bonus
        # ------------------------------------------------

        if analysis["category"] == "Medical History":

            importance += 0.15

        # ------------------------------------------------
        # Complaint Bonus
        # ------------------------------------------------

        if analysis["category"] == "Complaint":

            importance += 0.10

        # ------------------------------------------------
        # Emergency Bonus
        # ------------------------------------------------

        if analysis["urgency"] == "Critical":

            importance += 0.10

        importance = min(

            round(importance,2),

            1.0

        )

        return {

            "category_score":category,

            "urgency_score":urgency,

            "domain_score":domain,

            "emotion_score":emotion,

            "dependency_score":dependency,

            "novelty_score":novelty,

            "persona_match":persona,

            "confidence":confidence,

            "importance":importance

        }


# -------------------------------------------------------
# TEST
# -------------------------------------------------------

if __name__=="__main__":

    scorer = ImportanceScorer()

    tests = [

        {

            "category":"Greeting",

            "urgency":"Low",

            "domain":"",

            "emotion":"Neutral",

            "dependency":False,

            "novel_information":True,

            "persona_match":0.80,

            "confidence":0.90

        },

        {

            "category":"Medical History",

            "urgency":"Low",

            "domain":"Healthcare",

            "emotion":"Concerned",

            "dependency":False,

            "novel_information":True,

            "persona_match":0.95,

            "confidence":0.95

        },

        {

            "category":"Complaint",

            "urgency":"Critical",

            "domain":"Healthcare",

            "emotion":"Concerned",

            "dependency":False,

            "novel_information":True,

            "persona_match":1.00,

            "confidence":1.00

        }

    ]

    for item in tests:

        print()

        print(

            json.dumps(

                scorer.score(item),

                indent=4

            )

        )