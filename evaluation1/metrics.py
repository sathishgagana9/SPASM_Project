import time


class EvaluationMetrics:

    def __init__(self):

        self.results = []

    # ---------------------------------------

    def prompt_length(self, prompt):

        return len(prompt.split())

    # ---------------------------------------

    def memory_compression(

        self,

        selected_context,

        conversation

    ):

        if len(conversation) == 0:

            return 0

        return round(

            len(selected_context) /

            len(conversation),

            2

        )

    # ---------------------------------------

    def retrieval_precision(

        self,

        graph_context,

        entities

    ):

        if len(graph_context) == 0:

            return 0

        hit = 0

        for e in entities:

            if e in graph_context:

                hit += 1

        return round(

            hit /

            len(graph_context),

            2

        )

    # ---------------------------------------

    def response_time(

        self,

        start,

        end

    ):

        return round(

            end-start,

            3

        )

    # ---------------------------------------

    def add(

        self,

        persona,

        turns,

        result,

        response_time

    ):

        self.results.append({

            "persona":

                persona["role"],

            "turns":

                turns,

            "importance":

                result["importance"]["importance"],

            "risk":

                result["risk"]["risk"],

            "stability":

                result["persona_stability"]["stability"],

            "prompt_words":

                self.prompt_length(

                    result["prompt"]

                ),

            "memory_compression":

                self.memory_compression(

                    result["selected_context"],

                    result["conversation"]

                ),

            "retrieval_precision":

                self.retrieval_precision(

                    result["graph_context"],

                    result["analysis"]["entities"]

                ),

            "response_time":

                response_time

        })

    # ---------------------------------------

    def summary(self):

        return self.results