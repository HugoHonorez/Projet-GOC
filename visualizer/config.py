from dataclasses import dataclass
from pathlib import Path

from goc.paths import PROJECT_ROOT, SOLUTIONS_ROOT, find_instances_dir

WEB_ROOT = Path(__file__).resolve().parent / "web"
DEFAULT_SOLUTION_DIRS = (PROJECT_ROOT, SOLUTIONS_ROOT)


@dataclass(frozen=True)
class Settings:
    instances_dir: Path
    solution_dirs: tuple[Path, ...]

    @classmethod
    def create(cls, instances_dir=None, solution_dirs=None):
        instances = Path(instances_dir) if instances_dir else find_instances_dir()
        solutions = tuple(Path(p) for p in solution_dirs) if solution_dirs else DEFAULT_SOLUTION_DIRS
        return cls(instances.resolve(), tuple(p.resolve() for p in solutions))
