# def backup():
#     graph1 = ""
#     graph2 = ''

#     query_all = "MATCH (n) RETURN n"
#     results_all = graph1.run(query_all)

#     nodes = {}
#     for record in results_all:
#         node = record["n"]
#         node_id = node.identity
#         if node_id not in nodes:
#             new_node = Node(*(node.labels), **dict(node))
#             nodes[node_id] = new_node
#         graph2.create(new_node)

#     query_rel = "MATCH ()-[r]->() RETURN r"
#     results_rel = graph1.run(query_rel)

#     for record in results_rel:
#         rel = record["r"]
#         start_node = nodes.get(rel.start_node.identity)
#         end_node = nodes.get(rel.end_node.identity)
#         rel_type = type(rel).__name__
#         new_rel = Relationship(start_node, rel_type, end_node, **dict(rel))
#         graph2.create(new_rel)

#     return {'test': dict(rel)}