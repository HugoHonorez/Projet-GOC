import statistics
import threading
import time

from goc import circuit_data, source_bridge

MAX_RUNS = 50
_lock = threading.Lock()


class MappingError(ValueError):
    pass


def validate_mapping(mapping, n, m):
    if not isinstance(mapping, list) or not all(isinstance(v, int) and not isinstance(v, bool) for v in mapping):
        raise MappingError("Mapping must be a list of integers.")
    if len(mapping) != n:
        raise MappingError(f"Mapping must contain exactly {n} values (got {len(mapping)}).")
    outside = [v for v in mapping if not 0 <= v < m]
    if outside:
        raise MappingError(f"Value {outside[0]} is outside 0..{m - 1}.")
    if len(set(mapping)) != n:
        duplicate = next(v for v in mapping if mapping.count(v) > 1)
        raise MappingError(f"Physical qubit {duplicate} is used more than once.")


def routed_sample(instance, mapping):
    routed = source_bridge.routed_circuit(mapping, instance.circuit, instance.backend)
    return {
        **circuit_data.summary(routed),
        "operations": circuit_data.operations(routed),
        "finalLayout": final_layout(routed, instance.n),
    }


def final_layout(routed, n):
    try:
        return list(routed.layout.final_index_layout())[:n]
    except Exception:
        return None


def evaluate(instance, mapping, runs):
    validate_mapping(mapping, instance.n, instance.m)
    runs = max(1, min(int(runs), MAX_RUNS))
    with _lock:
        start = time.perf_counter()
        costs = [source_bridge.fitness(mapping, instance.circuit, instance.backend) for _ in range(runs)]
        seconds = time.perf_counter() - start
        routed = routed_sample(instance, mapping)
    return {
        "instance": instance.instance_id,
        "mapping": mapping,
        "costs": costs,
        "min": min(costs),
        "max": max(costs),
        "mean": statistics.fmean(costs),
        "stdev": statistics.pstdev(costs),
        "seconds": seconds,
        "routed": routed,
    }
