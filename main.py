"""Run: python3 main.py --output results"""
import argparse
import hashlib
import json
import math
import platform
import sys
from dataclasses import asdict
from pathlib import Path
from time import perf_counter

from simulation import Node, generate_tasks, evaluate, audit_policy
from schedulers import round_robin, greedy, pso, exact
from reporting import write_csv, summarize, chart, report

ROOT = Path(__file__).resolve().parent


def load_config(path):
    config = json.loads(path.read_text(encoding='utf-8'))
    for key in ('task_counts', 'sensitive_fractions', 'seeds'):
        if not isinstance(config[key], list) or not config[key] or len(set(config[key])) != len(config[key]):
            raise ValueError(f'{key} must be a nonempty list of unique values')
    if any(type(n) is not int or n < 1 for n in config['task_counts']):
        raise ValueError('Task counts must be positive integers')
    if any(type(s) is not int for s in config['seeds']):
        raise ValueError('Seeds must be integers')
    if any(not isinstance(f, (int, float)) or not math.isfinite(f) or not 0 <= f <= 1 for f in config['sensitive_fractions']):
        raise ValueError('Sensitive fractions must be finite and between 0 and 1')
    nodes = tuple(Node(**node) for node in config['nodes'])
    # Exercise validation before creating output files.
    pso(generate_tasks(1, 1, 0), nodes, seed=0, **config['pso'])
    return config, nodes


def run(config, nodes, output):
    output.mkdir(parents=True, exist_ok=True)
    (output / 'config.json').write_text(json.dumps(config, indent=2) + '\n')
    metrics, audit, convergence, task_rows = [], [], [], []
    for count in config['task_counts']:
        for fraction in config['sensitive_fractions']:
            for seed in config['seeds']:
                tasks = generate_tasks(count, fraction, seed)
                context = dict(task_count=count, sensitive_fraction=fraction, seed=seed)
                task_rows.extend({**context, **asdict(t)} for t in tasks)
                for name in ('round_robin', 'greedy', 'pso'):
                    begin = perf_counter()
                    if name == 'pso':
                        assignment, history = pso(tasks, nodes, seed=seed + 200000, **config['pso'])
                    else:
                        assignment = {'round_robin': round_robin, 'greedy': greedy}[name](tasks, nodes)
                        history = []
                    elapsed = perf_counter() - begin
                    result = evaluate(tasks, assignment, nodes)
                    assert not audit_policy(tasks, assignment, nodes)
                    metrics.append({**context, 'sensitive_count': sum(t.sensitive for t in tasks),
                        'scheduler': name, **{k: v for k, v in result.items() if k != 'rows'},
                        'scheduler_ms': elapsed * 1000,
                        'mean_with_scheduler_s': result['mean_completion_s'] + elapsed})
                    audit.extend({**context, 'scheduler': name, **r} for r in result['rows'])
                    convergence.extend({**context, 'iteration': i, 'best_mean_s': score}
                                       for i, score in enumerate(history))
            print(f'Finished n={count}, sensitive={fraction:.0%}', flush=True)
    summaries = summarize(metrics)
    for filename, rows in [('runs.csv', metrics), ('summary.csv', summaries), ('audit.csv', audit),
                           ('tasks.csv', task_rows), ('convergence.csv', convergence)]:
        write_csv(output / filename, rows)
    chosen_fraction = min(config['sensitive_fractions'], key=lambda f: abs(f-0.3))
    chosen_count = min(config['task_counts'], key=lambda n: abs(n-20))
    chart(output / 'comparison.svg', [r for r in summaries if r['sensitive_fraction'] == chosen_fraction],
          'Scheduling performance', f'{chosen_fraction:.0%} sensitive tasks · simulated mean completion ± sample SD · lower is better')
    chart(output / 'sensitivity.svg', [r for r in summaries if r['task_count'] == chosen_count],
          'Effect of the placement policy', f'{chosen_count} tasks · simulated mean completion ± sample SD · lower is better')
    tiny = generate_tasks(5, 0.4, 42)
    optimum = evaluate(tiny, exact(tiny, nodes), nodes)['mean_completion_s']
    assignment, _ = pso(tiny, nodes, seed=42, **config['pso'])
    achieved = evaluate(tiny, assignment, nodes)['mean_completion_s']
    check = dict(optimum_s=optimum, pso_s=achieved, gap_percent=100*(achieved-optimum)/optimum)
    (output / 'exact_check.json').write_text(json.dumps(check, indent=2) + '\n')
    report(output, metrics, summaries, check)
    metadata = dict(python=sys.version,
                    platform=platform.platform(), argv=sys.argv,
                    source_sha256={p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(ROOT.glob('*.py'))},
                    note='Simulated metrics are deterministic; measured runtimes vary.')
    (output / 'metadata.json').write_text(json.dumps(metadata, indent=2) + '\n')
    print(f'Completed {len(metrics)} runs. Report: {output / "REPORT.md"}')


def main():
    parser = argparse.ArgumentParser(description='Security-aware edge/cloud batch scheduling simulator')
    parser.add_argument('--config', type=Path, default=ROOT / 'configs/default.json')
    parser.add_argument('--output', type=Path, default=ROOT / 'results')
    parser.add_argument('--quick', action='store_true', help='Run one 20-task workload for a fast demonstration')
    args = parser.parse_args()
    try:
        config, nodes = load_config(args.config)
        if args.quick:
            config.update(task_counts=[20], sensitive_fractions=[0.3], seeds=[0])
        run(config, nodes, args.output)
    except (ValueError, KeyError, TypeError, OSError) as error:
        parser.exit(2, f'Error: {error}\n')


if __name__ == '__main__':
    main()
