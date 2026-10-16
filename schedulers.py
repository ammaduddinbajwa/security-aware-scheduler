"""Three policy-aware schedulers and a tiny-instance exact reference."""
import itertools
import random
from simulation import DEFAULT_NODES, allowed_destinations, evaluate, validate


def round_robin(tasks, nodes=DEFAULT_NODES):
    validate(tasks, nodes)
    result, cursor = [], 0
    for task in tasks:
        eligible = allowed_destinations(task, nodes)
        while cursor % len(nodes) not in eligible:
            cursor += 1
        result.append(cursor % len(nodes))
        cursor += 1
    return result


def greedy(tasks, nodes=DEFAULT_NODES):
    validate(tasks, nodes)
    available, result = [0.0] * len(nodes), []
    for task in tasks:
        def completion(dest):
            node = nodes[dest]
            return max(available[dest], node.network_delay / 2) + task.work_units / node.speed + node.network_delay / 2
        dest = min(allowed_destinations(task, nodes), key=completion)
        available[dest] = completion(dest) - nodes[dest].network_delay / 2
        result.append(dest)
    return result


def pso(tasks, nodes=DEFAULT_NODES, seed=0, particles=20, iterations=30,
        inertia=0.7, cognitive=1.5, social=1.5):
    """Continuous score PSO decoded by argmax over eligible nodes only.

    Random initialisation: no greedy warm start or hidden local search.
    The task ordering is fixed; PSO searches destination assignments only.
    """
    validate(tasks, nodes)
    if type(particles) is not int or particles < 1 or type(iterations) is not int or iterations < 1:
        raise ValueError('Particles and iterations must be positive integers')
    import math
    if any(not math.isfinite(x) or x < 0 for x in (inertia, cognitive, social)):
        raise ValueError('PSO coefficients must be finite and nonnegative')
    rng = random.Random(seed)
    width, dims = len(nodes), len(tasks) * len(nodes)
    eligible = [allowed_destinations(task, nodes) for task in tasks]

    def decode(position):
        return [max(options, key=lambda j: position[i * width + j])
                for i, options in enumerate(eligible)]

    def fitness(position):
        return evaluate(tasks, decode(position), nodes)['mean_completion_s']

    positions = [[rng.uniform(-1, 1) for _ in range(dims)] for _ in range(particles)]
    velocities = [[rng.uniform(-0.1, 0.1) for _ in range(dims)] for _ in range(particles)]
    personal = [p[:] for p in positions]
    scores = [fitness(p) for p in positions]
    best_index = min(range(particles), key=lambda i: scores[i])
    best, best_score = personal[best_index][:], scores[best_index]
    history = [best_score]
    for _ in range(iterations):
        # Synchronous generation: every particle sees the same global best.
        generation_best = best[:]
        for k in range(particles):
            for d in range(dims):
                v = (inertia * velocities[k][d]
                     + cognitive * rng.random() * (personal[k][d] - positions[k][d])
                     + social * rng.random() * (generation_best[d] - positions[k][d]))
                velocities[k][d] = max(-2, min(2, v))
                positions[k][d] = max(-5, min(5, positions[k][d] + velocities[k][d]))
            score = fitness(positions[k])
            if score < scores[k]:
                personal[k], scores[k] = positions[k][:], score
            if score < best_score:
                best, best_score = positions[k][:], score
        history.append(best_score)
    return decode(best), history


def exact(tasks, nodes=DEFAULT_NODES):
    validate(tasks, nodes)
    if len(tasks) > 8:
        raise ValueError('Exact enumeration is limited to 8 tasks')
    choices = itertools.product(*(allowed_destinations(t, nodes) for t in tasks))
    assignment = min(choices, key=lambda a: evaluate(tasks, a, nodes)['mean_completion_s'])
    return list(assignment)
