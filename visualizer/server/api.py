import re

from ..core import evaluation, solutions


class ApiError(Exception):
    def __init__(self, status, message):
        super().__init__(message)
        self.status = status
        self.message = message


class Api:
    def __init__(self, settings, repository):
        self.settings = settings
        self.repository = repository
        self.get_routes = [
            (re.compile(r"^/api/instances$"), self.list_instances),
            (re.compile(r"^/api/instances/(\d+)$"), self.instance_details),
            (re.compile(r"^/api/instances/(\d+)/solutions$"), self.instance_solutions),
        ]
        self.post_routes = [
            (re.compile(r"^/api/instances/(\d+)/evaluate$"), self.evaluate),
        ]

    def handle(self, method, path, body=None):
        routes = self.get_routes if method == "GET" else self.post_routes
        for pattern, handler in routes:
            match = pattern.match(path)
            if match:
                return handler(*match.groups(), body) if method == "POST" else handler(*match.groups())
        raise ApiError(404, f"Unknown endpoint {method} {path}")

    def instance(self, instance_id):
        try:
            return self.repository.get(int(instance_id))
        except KeyError:
            raise ApiError(404, f"Instance {instance_id} not found")

    def list_instances(self):
        return {
            "instancesDir": str(self.settings.instances_dir),
            "solutionDirs": [str(p) for p in self.settings.solution_dirs],
            "instances": self.repository.overviews(),
        }

    def instance_details(self, instance_id):
        return self.instance(instance_id).details()

    def instance_solutions(self, instance_id):
        instance = self.instance(instance_id)
        return solutions.list_for_instance(self.settings.solution_dirs, instance.instance_id, instance.n, instance.m)

    def evaluate(self, instance_id, body):
        instance = self.instance(instance_id)
        if not isinstance(body, dict):
            raise ApiError(400, "Request body must be a JSON object.")
        try:
            return evaluation.evaluate(instance, body.get("mapping"), body.get("runs", 5))
        except (evaluation.MappingError, TypeError, ValueError) as error:
            raise ApiError(400, str(error))
