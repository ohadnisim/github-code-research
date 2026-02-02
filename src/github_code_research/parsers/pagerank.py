"""PageRank algorithm for ranking code symbols by importance."""

from typing import Dict, List

import networkx as nx

from ..utils.logger import setup_logger
from .base import Symbol

logger = setup_logger(__name__)


class SymbolRanker:
    """Rank symbols using PageRank algorithm."""

    # Boost factors for different symbol characteristics
    EXPORTED_BOOST = 1.5
    ENTRY_POINT_BOOST = 2.0
    CLASS_BOOST = 1.2

    # Entry point names that indicate importance
    ENTRY_POINTS = {
        "main", "__main__", "init", "__init__",
        "setup", "start", "run", "execute",
        "index", "default", "app"
    }

    def __init__(self, damping_factor: float = 0.85, max_iterations: int = 20):
        """
        Initialize symbol ranker.

        Args:
            damping_factor: PageRank damping factor (default: 0.85)
            max_iterations: Maximum PageRank iterations (default: 20)
        """
        self.damping_factor = damping_factor
        self.max_iterations = max_iterations

    def rank_symbols(
        self,
        symbols: List[Symbol],
        imports: List[str],
        calls: List[str]
    ) -> Dict[str, float]:
        """
        Rank symbols by importance using PageRank.

        Args:
            symbols: List of symbols to rank
            imports: List of import statements
            calls: List of function calls

        Returns:
            Dict mapping symbol names to scores (0.0 to 1.0)
        """
        if not symbols:
            return {}

        # Build dependency graph
        graph = self._build_dependency_graph(symbols, imports, calls)

        # Run PageRank
        try:
            pagerank_scores = nx.pagerank(
                graph,
                alpha=self.damping_factor,
                max_iter=self.max_iterations,
            )
        except Exception as e:
            logger.warning(f"PageRank failed: {e}, using default scores")
            pagerank_scores = {s.name: 1.0 for s in symbols}

        # Apply boosts
        boosted_scores = self._apply_boosts(symbols, pagerank_scores)

        # Normalize to [0, 1]
        normalized_scores = self._normalize_scores(boosted_scores)

        logger.debug(f"Ranked {len(symbols)} symbols")

        return normalized_scores

    def _build_dependency_graph(
        self,
        symbols: List[Symbol],
        imports: List[str],
        calls: List[str]
    ) -> nx.DiGraph:
        """
        Build directed graph of symbol dependencies.

        Edges represent:
        - Import relationships (weight: 1.0)
        - Function calls (weight: 2.0)
        - Inheritance (weight: 3.0)
        """
        graph = nx.DiGraph()

        # Add all symbols as nodes
        for symbol in symbols:
            graph.add_node(symbol.name, symbol=symbol)

        # Add edges based on calls
        for call in calls:
            # Extract base name from call (e.g., "module.func" -> "func")
            call_parts = call.split(".")
            call_name = call_parts[-1] if call_parts else call

            # Find matching symbols
            for symbol in symbols:
                if symbol.name == call_name:
                    # Add edge from callers to this symbol
                    # (we don't know the caller, so add from all other symbols)
                    for other_symbol in symbols:
                        if other_symbol.name != symbol.name:
                            # Check if the call might be from this symbol
                            # (simplified heuristic: assume any symbol could call any other)
                            if not graph.has_edge(other_symbol.name, symbol.name):
                                graph.add_edge(
                                    other_symbol.name,
                                    symbol.name,
                                    weight=2.0,
                                    type="call"
                                )

        # Add edges based on imports
        for import_stmt in imports:
            # Extract imported names
            imported_names = self._extract_imported_names(import_stmt)

            for imported_name in imported_names:
                for symbol in symbols:
                    if symbol.name == imported_name:
                        # This symbol is imported, increase its importance
                        # Add self-edge to boost score
                        graph.add_edge(
                            symbol.name,
                            symbol.name,
                            weight=1.0,
                            type="import"
                        )

        # Add edges based on class relationships
        class_symbols = [s for s in symbols if s.type == "class"]
        method_symbols = [s for s in symbols if s.type == "method"]

        for method in method_symbols:
            # Extract class name from method signature
            if "." in method.name:
                class_name = method.name.split(".")[0]
                if any(c.name == class_name for c in class_symbols):
                    # Method belongs to class
                    graph.add_edge(
                        method.name,
                        class_name,
                        weight=3.0,
                        type="inheritance"
                    )

        return graph

    def _extract_imported_names(self, import_stmt: str) -> List[str]:
        """Extract symbol names from import statement."""
        names = []

        # Handle different import formats
        if import_stmt.startswith("from"):
            # from module import name1, name2
            if " import " in import_stmt:
                parts = import_stmt.split(" import ", 1)
                if len(parts) == 2:
                    imports = parts[1].split(",")
                    for imp in imports:
                        name = imp.strip().split(" as ")[0].strip()
                        names.append(name)
        elif import_stmt.startswith("import"):
            # import module or import module as alias
            parts = import_stmt.replace("import ", "").split(",")
            for part in parts:
                name = part.strip().split(" as ")[0].strip()
                # Get last component of module path
                if "." in name:
                    name = name.split(".")[-1]
                names.append(name)

        return names

    def _apply_boosts(self, symbols: List[Symbol], scores: Dict[str, float]) -> Dict[str, float]:
        """Apply boost factors to scores based on symbol characteristics."""
        boosted_scores = scores.copy()

        for symbol in symbols:
            if symbol.name not in boosted_scores:
                continue

            base_score = boosted_scores[symbol.name]

            # Boost exported symbols
            if symbol.is_exported:
                base_score *= self.EXPORTED_BOOST

            # Boost entry points
            if symbol.name.lower() in self.ENTRY_POINTS:
                base_score *= self.ENTRY_POINT_BOOST

            # Boost classes
            if symbol.type == "class":
                base_score *= self.CLASS_BOOST

            boosted_scores[symbol.name] = base_score

        return boosted_scores

    def _normalize_scores(self, scores: Dict[str, float]) -> Dict[str, float]:
        """Normalize scores to [0, 1] range."""
        if not scores:
            return {}

        min_score = min(scores.values())
        max_score = max(scores.values())

        if max_score == min_score:
            # All scores are the same
            return {name: 1.0 for name in scores}

        normalized = {}
        for name, score in scores.items():
            normalized[name] = (score - min_score) / (max_score - min_score)

        return normalized
