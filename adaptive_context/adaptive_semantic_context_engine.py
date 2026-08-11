import json

from adaptive_context.context_analyzer import ContextAnalyzer
from adaptive_context.domain_classifier import DomainClassifier
from adaptive_context.domain_fusion import DomainFusion
from adaptive_context.semantic_information_extractor import (
    SemanticInformationExtractor
)


class AdaptiveSemanticContextEngine:

    def __init__(self):

        self.context_analyzer = ContextAnalyzer()

        self.domain_classifier = DomainClassifier()

        self.domain_fusion = DomainFusion()

        self.semantic_extractor = SemanticInformationExtractor()

    # ----------------------------------------------------
    # Main Semantic Analysis
    # ----------------------------------------------------

    def analyze(self, persona, message):

        # ----------------------------------------
        # Step 1
        # Semantic Extraction
        # ----------------------------------------

        semantic = self.semantic_extractor.extract(message)

        # ----------------------------------------
        # Step 2
        # Context Analysis
        # ----------------------------------------

        analysis = self.context_analyzer.analyze(
            persona,
            message
        )

        # ----------------------------------------
        # Step 3
        # Domain Classification
        # ----------------------------------------

        prediction = self.domain_classifier.classify(
            message
        )

        # ----------------------------------------
        # Step 4
        # Domain Fusion
        # ----------------------------------------

        domain_result = self.domain_fusion.fuse(

            keyword_domain=analysis.get("domain", "General"),

            keyword_confidence=analysis.get(
                "domain_confidence",
                0.50
            ),

            llm_domain=prediction.get(
                "domain",
                "General"
            ),

            llm_confidence=prediction.get(
                "confidence",
                0.50
            )

        )

        # ----------------------------------------
        # Step 5
        # Semantic Context State
        # ----------------------------------------

        semantic_context = {

            "category":

                analysis.get(
                    "category",
                    ""
                ),

            "intent":

                semantic.get(
                    "intent",
                    analysis.get(
                        "intent",
                        ""
                    )
                ),

            "emotion":

                analysis.get(
                    "emotion",
                    "Neutral"
                ),

            "urgency":

                analysis.get(
                    "urgency",
                    "Low"
                ),

            "domain":

                domain_result.get(
                    "domain",
                    semantic.get(
                        "domain",
                        "General"
                    )
                ),

            "domain_confidence":

                domain_result.get(
                    "confidence",
                    0.50
                ),

            "domain_source":

                domain_result.get(
                    "source",
                    "Unknown"
                ),

            "entities":

                semantic.get(
                    "entities",
                    []
                ),

            "semantic_slots":

                semantic.get(
                    "slots",
                    {}
                ),

            "confidence":

                semantic.get(
                    "confidence",
                    analysis.get(
                        "confidence",
                        0.50
                    )
                )

        }

        return semantic_context


# ----------------------------------------------------
# TEST
# ----------------------------------------------------

if __name__ == "__main__":

    engine = AdaptiveSemanticContextEngine()

    persona = {

        "role": "Doctor",

        "tone": "Professional",

        "goal": "Help Patients"

    }

    tests = [

        "I have fever for two days.",

        "I've been burning up.",

        "Suggest medicine for headache.",

        "Explain linked list.",

        "Explain Chitradurga history.",

        "I want to visit Mysore."

    ]

    for msg in tests:

        print("\n========================================")
        print("USER :", msg)

        result = engine.analyze(
            persona,
            msg
        )

        print(

            json.dumps(

                result,

                indent=4

            )

        )