import re

FILE_PATTERN = re.compile(r"^(?P<group>.+?)_(?:Challenge|Instance)_(?P<instance>\d+)\.txt$", re.IGNORECASE)
NUMBER_PATTERN = re.compile(r"-?\d+(?:\.\d+)?")


def solution_files(directories):
    seen = set()
    for directory in directories:
        if not directory.is_dir():
            continue
        for path in sorted(directory.glob("*.txt")):
            resolved = path.resolve()
            if resolved in seen or not FILE_PATTERN.match(path.name):
                continue
            seen.add(resolved)
            yield path


def parse_values(text):
    return [float(token) if "." in token else int(token) for token in NUMBER_PATTERN.findall(text)]


def interpret(values, n, m):
    if len(values) == n + 1:
        mapping, claimed = values[:n], values[n]
    elif len(values) == n:
        mapping, claimed = values, None
    else:
        return None, None, f"Expected {n} or {n + 1} numbers, found {len(values)}."
    if not all(isinstance(v, int) for v in mapping):
        return None, claimed, "Mapping values must be integers."
    if any(not 0 <= v < m for v in mapping):
        return None, claimed, f"Mapping values must be in 0..{m - 1}."
    if len(set(mapping)) != n:
        return None, claimed, "Mapping values must be distinct."
    return mapping, claimed, None


def list_for_instance(directories, instance_id, n, m):
    result = []
    for path in solution_files(directories):
        match = FILE_PATTERN.match(path.name)
        if int(match.group("instance")) != instance_id:
            continue
        mapping, claimed, error = interpret(parse_values(path.read_text(encoding="utf-8", errors="replace")), n, m)
        result.append({
            "file": path.name,
            "path": str(path),
            "group": match.group("group"),
            "modified": path.stat().st_mtime,
            "mapping": mapping,
            "claimedCost": claimed,
            "error": error,
        })
    return sorted(result, key=lambda s: s["modified"], reverse=True)
