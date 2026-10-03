import networkx as nx
import matplotlib.pyplot as plt
from datetime import datetime


class SemanticMemoryGraph:

    def __init__(self):

        self.graph = nx.DiGraph()

    # ----------------------------------------------------
    # Add Semantic Memory
    # ----------------------------------------------------

    def add_memory(
        self,
        turn,
        speaker,
        message,
        analysis,
        importance,
        risk
    ):

        entities = analysis.get("entities", [])

        if len(entities) == 0:

            entities = [f"Turn_{turn}"]

        for entity in entities:

            node = {

                "entity": entity,
                "turn": turn,
                "speaker": speaker,
                "message": message,
                "category": analysis["category"],
                "intent": analysis["intent"],
                "emotion": analysis["emotion"],
                "urgency": analysis["urgency"],
                "domain": analysis["domain"],
                "importance": importance["importance"],
                "risk": risk["risk"],
                "confidence": analysis["confidence"],
                "timestamp": str(datetime.now())

            }

            self.graph.add_node(entity, **node)

        # Connect entities in same message

        for i in range(len(entities)-1):

            self.graph.add_edge(

                entities[i],

                entities[i+1],

                relation="same_message"

            )

    # ----------------------------------------------------
    # Connect Nodes
    # ----------------------------------------------------

    def connect(self, source, target, relation):

        if source in self.graph and target in self.graph:

            self.graph.add_edge(

                source,

                target,

                relation=relation

            )

    # ----------------------------------------------------
    # Statistics
    # ----------------------------------------------------

    def statistics(self):

        return {

            "nodes": self.graph.number_of_nodes(),

            "edges": self.graph.number_of_edges()

        }

    # ----------------------------------------------------
    # Centrality
    # ----------------------------------------------------

    def centrality(self):

        return nx.degree_centrality(self.graph)

    # ----------------------------------------------------
    # PageRank
    # ----------------------------------------------------

    def pagerank(self):

        return nx.pagerank(self.graph)

    # ----------------------------------------------------
    # Retrieve Node
    # ----------------------------------------------------

    def get_memory(self, entity):

        if entity not in self.graph:

            return None

        return self.graph.nodes[entity]

    # ----------------------------------------------------
    # Retrieve Neighbours
    # ----------------------------------------------------

    def neighbours(self, entity):

        if entity not in self.graph:

            return []

        return list(self.graph.neighbors(entity))

    # ----------------------------------------------------
    # Print Graph
    # ----------------------------------------------------

    def print_graph(self):

        print("\n========== Nodes ==========\n")

        for node, data in self.graph.nodes(data=True):

            print(node)

            for k, v in data.items():

                print(f"{k}: {v}")

            print()

        print("\n========== Edges ==========\n")

        for u, v, data in self.graph.edges(data=True):

            print(f"{u} ---> {v} ({data['relation']})")

    # ----------------------------------------------------
    # Draw
    # ----------------------------------------------------

    def draw(self):

        plt.figure(figsize=(10,7))

        pos = nx.spring_layout(self.graph, seed=42)

        nx.draw_networkx_nodes(

            self.graph,

            pos,

            node_size=2500

        )

        nx.draw_networkx_edges(

            self.graph,

            pos,

            arrows=True

        )

        nx.draw_networkx_labels(

            self.graph,

            pos,

            font_size=10

        )

        edge_labels = nx.get_edge_attributes(

            self.graph,

            "relation"

        )

        nx.draw_networkx_edge_labels(

            self.graph,

            pos,

            edge_labels=edge_labels

        )

        plt.title(

            "SPASM++ Semantic Memory Graph"

        )

        plt.axis("off")

        plt.show()


# ----------------------------------------------------
# TEST
# ----------------------------------------------------

if __name__ == "__main__":

    graph = SemanticMemoryGraph()

    analysis = {

        "category":"Medical History",

        "intent":"Report Condition",

        "emotion":"Concerned",

        "urgency":"Low",

        "domain":"Healthcare",

        "entities":["Diabetes"],

        "confidence":0.95

    }

    importance = {

        "importance":0.91

    }

    risk = {

        "risk":"Low"

    }

    graph.add_memory(

        turn=1,

        speaker="User",

        message="I have diabetes.",

        analysis=analysis,

        importance=importance,

        risk=risk

    )

    analysis2 = {

        "category":"Complaint",

        "intent":"Medical Advice",

        "emotion":"Concerned",

        "urgency":"High",

        "domain":"Healthcare",

        "entities":["Blood Sugar","320"],

        "confidence":0.97

    }

    importance2 = {

        "importance":0.96

    }

    risk2 = {

        "risk":"High"

    }

    graph.add_memory(

        turn=2,

        speaker="User",

        message="My sugar level is 320.",

        analysis=analysis2,

        importance=importance2,

        risk=risk2

    )

    graph.connect(

        "Diabetes",

        "Blood Sugar",

        "causes"

    )

    print(graph.statistics())

    print()

    print(graph.centrality())

    print()

    print(graph.pagerank())

    print()

    print(graph.get_memory("Diabetes"))

    print()

    graph.print_graph()

    graph.draw()