import re
import threading
from dataclasses import dataclass

from goc import circuit_data, source_bridge

from . import hardware

FILE_PATTERN = re.compile(r"^Instance_(\d+)\.qasm$")


@dataclass
class LoadedInstance:
    instance_id: int
    backend: object
    circuit: object
    n: int
    m: int

    def overview(self):
        circuit = circuit_data.summary(self.circuit)
        return {
            "id": self.instance_id,
            "n": self.n,
            "m": self.m,
            "hardware": self.backend.name,
            "depth": circuit["depth"],
            "twoQubitGates": circuit["twoQubitGates"],
        }

    def details(self):
        return {
            "id": self.instance_id,
            "file": f"Instance_{self.instance_id}.qasm",
            "n": self.n,
            "m": self.m,
            "circuit": {
                **circuit_data.summary(self.circuit),
                "operations": circuit_data.operations(self.circuit),
                "interactions": circuit_data.interactions(self.circuit),
            },
            "hardware": hardware.describe(self.backend),
        }


class InstanceRepository:
    def __init__(self, instances_dir):
        self.instances_dir = instances_dir
        self._cache = {}
        self._lock = threading.Lock()

    def available_ids(self):
        ids = []
        for path in self.instances_dir.glob("Instance_*.qasm"):
            match = FILE_PATTERN.match(path.name)
            if match and int(match.group(1)) in source_bridge.SUPPORTED_INSTANCES:
                ids.append(int(match.group(1)))
        return sorted(ids)

    def get(self, instance_id):
        if instance_id not in self.available_ids():
            raise KeyError(instance_id)
        with self._lock:
            if instance_id not in self._cache:
                backend, circuit, n, m = source_bridge.load_instance(instance_id, self.instances_dir)
                self._cache[instance_id] = LoadedInstance(instance_id, backend, circuit, n, m)
            return self._cache[instance_id]

    def overviews(self):
        return [self.get(instance_id).overview() for instance_id in self.available_ids()]
