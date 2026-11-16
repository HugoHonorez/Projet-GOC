from goc.hardware import coordinates, coupling_edges


def describe(backend):
    edges = coupling_edges(backend)
    return {
        "name": backend.name,
        "numQubits": backend.num_qubits,
        "edges": [list(edge) for edge in edges],
        "coordinates": coordinates(backend.num_qubits, edges),
    }
