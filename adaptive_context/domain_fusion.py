import json


class DomainFusion:

    def __init__(self):
        pass

    def fuse(

        self,

        keyword_domain,
        keyword_confidence,

        llm_domain,
        llm_confidence

    ):

        result = {

            "domain": "General",

            "confidence": 0.0,

            "source": ""

        }

        # ----------------------------------------
        # Rule 1
        # High confidence keyword
        # ----------------------------------------

        if keyword_confidence >= 0.90:

            result["domain"] = keyword_domain

            result["confidence"] = keyword_confidence

            result["source"] = "Keyword"

            return result

        # ----------------------------------------
        # Rule 2
        # High confidence LLM
        # ----------------------------------------

        if llm_confidence >= keyword_confidence:

            result["domain"] = llm_domain

            result["confidence"] = llm_confidence

            result["source"] = "LLM"

        else:

            result["domain"] = keyword_domain

            result["confidence"] = keyword_confidence

            result["source"] = "Keyword"

        return result


# ----------------------------------------
# TEST
# ----------------------------------------

if __name__ == "__main__":

    fusion = DomainFusion()

    tests = [

        (
            "Healthcare",
            1.0,
            "Healthcare",
            0.95
        ),

        (
            "General",
            0.20,
            "Programming",
            0.99
        ),

        (
            "Programming",
            0.60,
            "Programming",
            0.95
        ),

        (
            "Travel",
            0.95,
            "Travel",
            0.80
        )

    ]

    for test in tests:

        print(

            json.dumps(

                fusion.fuse(*test),

                indent=4

            )

        )