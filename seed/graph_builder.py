"""
seed/graph_builder.py
Ontoloji → Typed ağırlıklı graf (NetworkX).
Graf backend soyutlanmış — ileride Neo4j'e geçiş şeffaf.
"""

import json
import logging
import yaml
from collections import defaultdict
from pathlib import Path

logger = logging.getLogger(__name__)

FACTORS_PATH = Path("config/propagation_factors.yaml")


class GraphBuilder:
    def __init__(self):
        self.propagation_factors = self._load_factors()

    def _load_factors(self) -> dict:
        if FACTORS_PATH.exists():
            return yaml.safe_load(FACTORS_PATH.read_text())
        return {}

    def build(self, ontology: dict) -> dict:
        entities = ontology.get("entities", [])
        relationships = ontology.get("relationships", [])
        id_set = {e["id"] for e in entities}
        degree_count = defaultdict(int)

        nodes = []
        for e in entities:
            nodes.append({
                "id": e["id"],
                "label": e["name"],
                "type": e.get("type", "concept"),
                "importance": e.get("importance", 1),
                "description": e.get("description", ""),
                "degree": 0,
                "community": None,
                "risk_score": 0.0,
            })

        edges = []
        for r in relationships:
            src, tgt = r.get("source"), r.get("target")
            if src not in id_set or tgt not in id_set:
                continue
            rel_type = r.get("relation", "IMPACTS")
            prop_factor = self.propagation_factors.get(
                "edge_propagation", {}
            ).get(rel_type, 0.5)

            edges.append({
                "source": src,
                "target": tgt,
                "relation": rel_type,
                "weight": r.get("weight", 0.5),
                "propagation_factor": prop_factor,
                "description": r.get("description", ""),
            })
            degree_count[src] += 1
            degree_count[tgt] += 1

        for node in nodes:
            node["degree"] = degree_count.get(node["id"], 0)

        _assign_communities(nodes, edges)

        graph = {
            "nodes": nodes,
            "edges": edges,
            "metadata": {
                "node_count": len(nodes),
                "edge_count": len(edges),
                "domain": ontology.get("domain", "general"),
                "summary": ontology.get("summary", ""),
                "key_themes": ontology.get("key_themes", []),
            },
        }
        logger.info(f"Graf: {len(nodes)} node, {len(edges)} edge")
        return graph

    def propagate_risk(self, graph: dict, trigger_node_id: str,
                       initial_delta: float, max_depth: int = 4) -> dict:
        """
        Sönümlü BFS risk propagasyonu.
        Negatif propagation_factor riski azaltır (MITIGATES).
        """
        cfg = self.propagation_factors.get("propagation", {})
        min_delta = cfg.get("min_delta_threshold", 0.05)
        dampening = cfg.get("dampening_per_hop", 0.80)
        max_depth = cfg.get("max_depth", max_depth)

        # Edge map
        edge_map = defaultdict(list)
        for e in graph["edges"]:
            edge_map[e["source"]].append(e)

        visited = {trigger_node_id: initial_delta}
        queue = [(trigger_node_id, initial_delta, 0)]

        while queue:
            node_id, delta, depth = queue.pop(0)
            if depth >= max_depth:
                continue
            for edge in edge_map.get(node_id, []):
                prop = edge["propagation_factor"] * edge["weight"]
                new_delta = delta * prop * (dampening ** depth)
                if abs(new_delta) < min_delta:
                    continue
                tgt = edge["target"]
                visited[tgt] = visited.get(tgt, 0) + new_delta
                queue.append((tgt, new_delta, depth + 1))

        return visited


def _assign_communities(nodes, edges):
    neighbors = defaultdict(set)
    for e in edges:
        neighbors[e["source"]].add(e["target"])
        neighbors[e["target"]].add(e["source"])

    community_id = 0
    assigned = {}

    for node in sorted(nodes, key=lambda n: n["degree"], reverse=True):
        nid = node["id"]
        if nid in assigned:
            node["community"] = assigned[nid]
            continue
        neighbor_communities = [assigned[n] for n in neighbors[nid] if n in assigned]
        if neighbor_communities:
            from collections import Counter
            node["community"] = Counter(neighbor_communities).most_common(1)[0][0]
        else:
            node["community"] = community_id
            community_id += 1
        assigned[nid] = node["community"]
