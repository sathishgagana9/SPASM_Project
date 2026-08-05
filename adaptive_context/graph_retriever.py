import networkx as nx


class GraphRetriever:

    def __init__(self, graph):

        self.graph = graph

    # --------------------------------------
    # Search Node
    # --------------------------------------

    def search(self, keyword):

        keyword = keyword.lower()

        results = []

        for node in self.graph.nodes():

            if keyword in node.lower():

                results.append(node)

        return results

    # --------------------------------------
    # Get Neighbor Nodes
    # --------------------------------------

    def neighbors(self, node):

        if node not in self.graph:

            return []

        return list(self.graph.neighbors(node))

    # --------------------------------------
    # Retrieve Context
    # --------------------------------------

    def retrieve(self, keyword):

        nodes = self.search(keyword)

        context = set()

        for node in nodes:

            context.add(node)

            # Parent Nodes

            for parent in self.graph.predecessors(node):

                context.add(parent)

            # Child Nodes

            for child in self.graph.neighbors(node):

                context.add(child)

        return list(context)

    # --------------------------------------
    # Retrieve Multi-Hop Context
    # --------------------------------------

    def retrieve_multihop(self, keyword, depth=2):

        nodes = self.search(keyword)

        visited = set()

        for node in nodes:

            visited.add(node)

            current = {node}

            for _ in range(depth):

                nxt = set()

                for item in current:

                    nxt.update(self.graph.predecessors(item))
                    nxt.update(self.graph.neighbors(item))

                visited.update(nxt)
                current = nxt

        return list(visited)


# ---------------------------------------------------
# TEST
# ---------------------------------------------------

if __name__ == "__main__":

    G = nx.DiGraph()

    G.add_edge("Diabetes", "Blood Sugar")

    G.add_edge("Blood Sugar", "Insulin")

    G.add_edge("Insulin", "Medicine")

    G.add_edge("Medicine", "Hospital")

    retriever = GraphRetriever(G)

    print("\nSearch")

    print(retriever.search("Insulin"))

    print("\nNeighbors")

    print(retriever.neighbors("Blood Sugar"))

    print("\nContext")

    print(retriever.retrieve("Insulin"))

    print("\nMulti-Hop")

    print(retriever.retrieve_multihop("Insulin"))