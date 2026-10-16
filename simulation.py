"""Deterministic batch simulation. Units: work units and seconds."""
from dataclasses import dataclass
import math
import random


@dataclass(frozen=True)
class Task:
    id: int
    work_units: float
    sensitive: bool


@dataclass(frozen=True)
class Node:
    name: str
    speed: float
    network_delay: float
    trusted: bool


DEFAULT_NODES = (
    Node('edge_device', 10, 0, True),
    Node('edge_server', 25, 0.02, True),
    Node('cloud', 50, 0.10, False),
)


def generate_tasks(count, sensitive_fraction, seed):
    if type(count) is not int or count < 1:
        raise ValueError('Task count must be a positive integer')
    if not 0 <= sensitive_fraction <= 1:
        raise ValueError('Sensitive fraction must be between 0 and 1')
    # Separate randomness preserves work sizes across sensitivity scenarios.
    work_rng = random.Random(seed)
    ids = list(range(count))
    random.Random(seed + 100000).shuffle(ids)
    sensitive = set(ids[:round(count * sensitive_fraction)])
    return [Task(i, work_rng.randint(10, 100), i in sensitive) for i in range(count)]


def allowed_destinations(task, nodes=DEFAULT_NODES):
    return [i for i, node in enumerate(nodes) if not task.sensitive or node.trusted]


def validate(tasks, nodes):
    if not tasks or not nodes:
        raise ValueError('Tasks and nodes cannot be empty')
    if len({t.id for t in tasks}) != len(tasks):
        raise ValueError('Task IDs must be unique')
    if len({n.name for n in nodes}) != len(nodes):
        raise ValueError('Node names must be unique')
    for node in nodes:
        if not math.isfinite(node.speed) or node.speed <= 0:
            raise ValueError('Node speed must be finite and positive')
        if not math.isfinite(node.network_delay) or node.network_delay < 0:
            raise ValueError('Network delay must be finite and nonnegative')
        if type(node.trusted) is not bool:
            raise ValueError('Trusted must be boolean')
    for task in tasks:
        if not math.isfinite(task.work_units) or task.work_units <= 0:
            raise ValueError('Task work must be finite and positive')
        if type(task.sensitive) is not bool:
            raise ValueError('Sensitive must be boolean')
        if not allowed_destinations(task, nodes):
            raise ValueError('No eligible destination for task')


def audit_policy(tasks, assignment, nodes=DEFAULT_NODES):
    """Independent check of assignments; returns violations instead of hiding them."""
    if len(tasks) != len(assignment):
        raise ValueError('Exactly one destination is required per task')
    violations = []
    for task, dest in zip(tasks, assignment):
        if type(dest) is not int or not 0 <= dest < len(nodes):
            raise ValueError('Invalid destination index')
        if task.sensitive and not nodes[dest].trusted:
            violations.append(task.id)
    return violations


def evaluate(tasks, assignment, nodes=DEFAULT_NODES):
    """All tasks arrive at time zero; fixed input order is preserved per worker."""
    validate(tasks, nodes)
    violations = audit_policy(tasks, assignment, nodes)
    if violations:
        raise ValueError(f'Policy violation for tasks {violations}')
    available = [0.0] * len(nodes)
    rows = []
    for task, dest in zip(tasks, assignment):
        node = nodes[dest]
        arrival = node.network_delay / 2
        start = max(arrival, available[dest])
        finish = start + task.work_units / node.speed
        available[dest] = finish
        rows.append(dict(task_id=task.id, work_units=task.work_units,
                         sensitive=task.sensitive, destination=node.name,
                         start_s=start, compute_finish_s=finish,
                         completion_s=finish + node.network_delay / 2,
                         policy_violation=False))
    times = sorted(row['completion_s'] for row in rows)
    return dict(mean_completion_s=sum(times) / len(times),
                p95_completion_s=times[math.ceil(0.95 * len(times)) - 1],
                makespan_s=max(times), policy_violations=len(violations), rows=rows)
