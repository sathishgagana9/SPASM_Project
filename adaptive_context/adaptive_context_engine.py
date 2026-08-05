import os
import sys
import json
import time
import re

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from unified_analyzer import UnifiedAnalyzer
from importance_scorer import ImportanceScorer
from decision_engine import DecisionEngine
from context_selector import AdaptiveContextSelector
from conversation_graph import SemanticMemoryGraph
from graph_retriever import GraphRetriever
from prompt_builder import PromptBuilder
from response_validator import ResponseValidator
from response_optimizer import ResponseOptimizer
from persona_stability_checker import PersonaStabilityChecker
from persona_repair_engine import PersonaRepairEngine


from scripts.llm import generate


def _has_sufficient_symptom_detail(message):
    """
    Rule-based check (no LLM needed): does this message already contain
    the kind of information the canned ASK_AND_GUIDE questions ask for
    (duration, severity, other symptoms, medication)? If the user already
    volunteered 2+ of these, re-asking the same boilerplate questions is
    redundant and looks broken. Skip straight to real guidance instead.
    """
    msg = message.lower()

    duration = re.search(
        r"\b\d+\s*(day|days|hour|hours|week|weeks)\b|since (yesterday|last night|this morning)",
        msg
    )
    severity = re.search(
        r"\d+\s*(degree|degrees|°|f\b|c\b)|severe|mild|high fever|low fever|worsening|getting worse",
        msg
    )
    medication = re.search(
        r"\b(paracetamol|tablet|medicine|medication|took|taken|pill|dose)\b",
        msg
    )
    other_symptoms = re.search(
        r"\b(cough|vomit|nausea|headache|chills|body ache|sore throat|breathless|fatigue|weakness)\b",
        msg
    )

    signals = sum(bool(x) for x in [duration, severity, medication, other_symptoms])
    return signals >= 2


def _vital_sign_risk_override(message):
    """
    Rule-based safety net (no LLM needed): a small local model can miss
    that "temperature is 110 degrees" is a medical emergency. This scans
    for temperature-like numbers near relevant words and force-escalates
    risk to Critical when they're in a dangerous range, so the decision
    engine routes to EMERGENCY (a real, tailored LLM reply) instead of
    the generic ASK_AND_GUIDE template.
    """
    msg = message.lower()

    if not any(w in msg for w in ["temperature", "fever", "degree", "°"]):
        return None

    for n in re.findall(r"(\d{2,3}(?:\.\d+)?)", msg):
        try:
            val = float(n)
        except ValueError:
            continue

        # Crude Fahrenheit/Celsius guess based on magnitude
        if val > 50 and val >= 103:      # Fahrenheit danger zone
            return "Critical"
        if val <= 50 and val >= 39.4:    # Celsius danger zone
            return "Critical"

    return None


class AdaptiveContextEngine:

    def __init__(self):

        self.unified_analyzer = UnifiedAnalyzer()
        self.importance_scorer = ImportanceScorer()

        self.decision_engine = DecisionEngine()

        self.selector = AdaptiveContextSelector()

        self.graph = SemanticMemoryGraph()

        self.prompt_builder = PromptBuilder()

        self.validator = ResponseValidator()

        
        self.optimizer = ResponseOptimizer()

        self.persona_checker = PersonaStabilityChecker()

        self.persona_repair = PersonaRepairEngine(
            threshold=0.90,
            max_attempts=1   # was 3 - each attempt costs 2 more LLM calls
                              # (repair + re-validate); 1 is enough for a
                              # demo and keeps worst-case latency bounded
        )

        self.conversation = []
        self.analysis_history = []
        self.importance_history = []
        self.risk_history = []
        self.dependency_history = []   # appended once per turn, never recomputed
        self.novelty_history = []      # appended once per turn, never recomputed


    def process(self, persona, user_message):

        # ----------------------------
        # Store User Message
        # ----------------------------

        self.conversation.append({

            "speaker": "User",

            "message": user_message

        })

        turn = len(self.conversation)

        # ----------------------------
        # Analyze
        # ----------------------------

        start = time.time()

        previous_user_messages = [
            msg["message"]
            for msg in self.conversation
            if msg["speaker"] == "User"
        ][:-1]

        analysis = self.unified_analyzer.analyze(

            persona,

            user_message,

            previous_user_messages

        )

        print("Analyzer Time (merged context+domain+risk+dependency+novelty):",
              round(time.time() - start, 2), "seconds")
        print("\n========== ANALYSIS ==========")
        print(json.dumps(analysis, indent=4))

        self.analysis_history.append(

            analysis

        )

        # ----------------------------
        # Importance
        # ----------------------------

        importance = self.importance_scorer.score(

            analysis

        )

        self.importance_history.append(

            importance

        )

        # ----------------------------
        # Risk (now returned by the merged analysis call above)
        # ----------------------------

        risk = {
            "risk": analysis["risk"],
            "priority": analysis["risk_priority"],
            "reason": analysis["risk_reason"],
        }

        # Safety net: force-escalate risk for dangerous vital signs the
        # small local model might not judge correctly on its own.
        vital_override = _vital_sign_risk_override(user_message)
        if vital_override:
            risk["risk"] = vital_override
            risk["reason"] = (risk["reason"] or "") + " (escalated: dangerous vital sign detected)"

        self.risk_history.append(

            risk

        )

        # ----------------------------
        # Semantic Memory Graph
        # ----------------------------

        self.graph.add_memory(

            turn,

            "User",

            user_message,

            analysis,

            importance,

            risk

        )

        # ----------------------------
        # Dependency + Novelty
        # Now returned by the merged analysis call above and appended once
        # per turn, instead of being recomputed for the whole conversation
        # on every single turn.
        # ----------------------------

        self.dependency_history.append({
            "turn": turn,
            "depends_on": [turn - 1] if analysis["dependency"] else []
        })

        self.novelty_history.append({
            "turn": turn,
            "novel": analysis["novel_information"],
            "reason": analysis.get("novelty_reason", "")
        })

        dependency = {"dependencies": self.dependency_history}
        novelty = {"novelty": self.novelty_history}

        # ----------------------------
        # Adaptive Context Selection
        # ----------------------------

        selected = self.selector.select(

            self.conversation,

            self.analysis_history,

            self.importance_history,

            dependency,

            novelty,

            self.risk_history

        )

        # ----------------------------
        # Graph Retrieval
        # ----------------------------

        retriever = GraphRetriever(

            self.graph.graph

        )

        graph_context = []

        for entity in analysis.get("entities", []):

            graph_context.extend(

                retriever.retrieve_multihop(

                    entity

                )

            )

        graph_context = list(

            dict.fromkeys(graph_context)

        )
                # ----------------------------
        # Decision Engine
        # ----------------------------

        decision = self.decision_engine.decide(

    persona,

    analysis,

    importance,

    risk,

    graph_context

)
        print("\n========== DECISION ==========")
        print(json.dumps(decision, indent=4))


        # ----------------------------------
        # Ask-and-Guide Strategy (Rule-Based)
        # ----------------------------------

        if decision["strategy"] == "ASK_AND_GUIDE" and _has_sufficient_symptom_detail(user_message):

            # The user already volunteered duration/severity/other-symptom/
            # medication info in this message - asking the same 4 canned
            # questions again would just repeat itself. Route to a real,
            # generated response instead.
            decision["strategy"] = "GENERAL_GUIDANCE"
            decision["execution_mode"] = "FULL"
            decision["allow_llm"] = True

        if decision["strategy"] == "ASK_AND_GUIDE":

            if persona["role"] == "Doctor":

                assistant_reply = f"""
        I understand your concern.

        Before I can provide the most appropriate advice about "{user_message}", I need a little more information.

        1. When did the symptoms start?
        2. How severe are they?
        3. Do you have any other symptoms?
        4. Have you taken any medication already?

        Once you answer these questions, I'll provide appropriate guidance.
        """

                validation = {
                    "role": 1.0,
                    "tone": 1.0,
                    "goal": 1.0,
                    "memory": 1.0,
                    "context": 1.0,
                    "stability": 1.0,
                    "reason": "Rule-based Ask-and-Guide"
                }

                stability = validation
                repair_count = 0

                self.conversation.append({
                    "speaker": "Assistant",
                    "message": assistant_reply
                })

                return {
                    "reply": assistant_reply,
                    "analysis": analysis,
                    "importance": importance,
                    "risk": risk,
                    "decision": decision,
                    "validation": validation,
                    "repair_count": repair_count,
                    "selected_context": selected,
                    "graph_context": graph_context,
                    "graph_statistics": self.graph.statistics(),
                    "persona_stability": stability,
                    "prompt": "",
                    "conversation": self.conversation
                }

        print("\nDecision")
        print(decision)




        
        # ----------------------------
        # Prompt
        # ----------------------------

        prompt = self.prompt_builder.build(

    persona,

    user_message,

    selected,

    graph_context,

    analysis,

    importance,

    risk,

    decision["strategy"]

)
        # ----------------------------
        # LLM
        # ----------------------------

        print("\n========== DECISION ==========")
        print("Strategy :", decision["strategy"])
        print("Allow LLM:", decision["allow_llm"])

        if not decision["allow_llm"]:

            print(">>> USING FALLBACK RESPONSE <<<")

            assistant_reply = decision["fallback_response"]

        else:

            print(">>> USING LLM <<<")

            start = time.time()

            assistant_reply = generate(prompt, num_predict=180)

            print("LLM Time:", round(time.time() - start, 2), "seconds")
                

                # ----------------------------
        # Validation & Persona Repair
        # ----------------------------

        if decision["execution_mode"] == "FAST":

            validation = {
                "role": 1.0,
                "tone": 1.0,
                "goal": 1.0,
                "memory": 1.0,
                "context": 1.0,
                "stability": 1.0,
                "reason": "Fast Mode"
            }

            stability = validation
            repair_count = 0

        elif decision["allow_llm"]:

            start = time.time()

            validation = self.validator.validate(

                persona,
                user_message,
                assistant_reply,
                analysis,
                graph_context,
                selected

            )

            print("Validator Time:", round(time.time() - start, 2), "seconds")

            stability = validation
            repair_count = 0

            while stability["stability"] < 0.90 and repair_count < 3:

                start = time.time()

                assistant_reply, repaired, attempts = self.persona_repair.repair(

                    persona,
                    user_message,
                    assistant_reply,
                    stability["stability"]

                )
                
                print("Repair Time:", round(time.time() - start, 2), "seconds")

                validation = self.validator.validate(

                    persona,
                    user_message,
                    assistant_reply,
                    analysis,
                    graph_context,
                    selected

                )

                stability = validation
                repair_count += 1

            # ResponseOptimizer does a full extra LLM generation to polish
            # grammar/tone. It was running unconditionally on every FULL
            # turn even when validation already passed cleanly. Only worth
            # the extra ~15-20s if the reply was actually borderline.
            if stability["stability"] < 0.90:

                assistant_reply = self.optimizer.optimize(

                    persona,
                    user_message,
                    assistant_reply,
                    analysis,
                    stability["stability"]

                )

        else:

            validation = {
                "role": 1.0,
                "tone": 1.0,
                "goal": 1.0,
                "memory": 1.0,
                "context": 1.0,
                "stability": 1.0,
                "reason": "Fallback response"
            }

            stability = validation
            repair_count = 0
        
        # ----------------------------
        # Store Assistant Reply
        # ----------------------------

        self.conversation.append({

            "speaker": "Assistant",

            "message": assistant_reply

        })

         
        # ----------------------------
        # Store Assistant in Semantic Memory Graph
        # ----------------------------

        self.graph.add_memory(

            len(self.conversation),

            "Assistant",

            assistant_reply,

            analysis,          # <-- IMPORTANT: use analysis, NOT validation

            importance,

            risk

        )

      
       
       
        # ----------------------------
        # Return
        # ----------------------------

        return {

    "reply": assistant_reply,

    "analysis": analysis,

    "importance": importance,

    "risk": risk,

    "decision": decision,

    "validation": validation,

    "repair_count": repair_count,

    "selected_context": selected,

    "graph_context": graph_context,

    "graph_statistics": self.graph.statistics(),

    "persona_stability": stability,

    "prompt": prompt,

    "conversation": self.conversation

}

if __name__ == "__main__":

    engine = AdaptiveContextEngine()

    persona = {

        "role": "Doctor",

        "tone": "Professional",

        "goal": "Help patients"

    }

    result = engine.process(

        persona,

        "I have diabetes."

    )

    print(

        json.dumps(

            result,

            indent=4

        )

    )