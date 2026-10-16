"""CSV, Markdown and standalone SVG output without external dependencies."""
import csv
import html
import statistics
from collections import defaultdict

COLORS = {'round_robin': '#64748b', 'greedy': '#0891b2', 'pso': '#7c3aed'}


def write_csv(path, rows):
    if not rows:
        return
    with path.open('w', newline='', encoding='utf-8') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def summarize(rows):
    groups = defaultdict(list)
    for row in rows:
        groups[(row['task_count'], row['sensitive_fraction'], row['scheduler'])].append(row)
    summaries = []
    for (count, fraction, scheduler), group in sorted(groups.items()):
        means = [r['mean_completion_s'] for r in group]
        summaries.append(dict(task_count=count, sensitive_fraction=fraction,
            scheduler=scheduler, runs=len(group), mean_completion_s=statistics.mean(means),
            sd_completion_s=statistics.stdev(means) if len(means) > 1 else 0,
            mean_makespan_s=statistics.mean(r['makespan_s'] for r in group),
            mean_scheduler_ms=statistics.mean(r['scheduler_ms'] for r in group),
            policy_violations=sum(r['policy_violations'] for r in group)))
    return summaries


def chart(path, summaries, title, subtitle):
    """Horizontal bars; error bars show sample SD of run means, not confidence intervals."""
    width, height = 1000, 150 + 40 * len(summaries)
    max_value = max(r['mean_completion_s'] + r['sd_completion_s'] for r in summaries) * 1.12
    scale = 500 / max_value
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img">',
             f'<title>{html.escape(title)}</title>',
             '<rect width="100%" height="100%" fill="#f8fafc"/>',
             '<g font-family="Arial, sans-serif" fill="#0f172a">',
             f'<text x="30" y="35" font-size="23" font-weight="bold">{html.escape(title)}</text>',
             f'<text x="30" y="62" font-size="14">{html.escape(subtitle)}</text>']
    for tick in range(6):
        x = 300 + tick * 100
        parts.append(f'<line x1="{x}" y1="88" x2="{x}" y2="{height-35}" stroke="#e2e8f0"/>')
        parts.append(f'<text x="{x}" y="{height-12}" text-anchor="middle" font-size="12">{tick*100/scale:.1f}s</text>')
    for i, row in enumerate(summaries):
        y = 98 + i * 40
        mean, sd = row['mean_completion_s'], row['sd_completion_s']
        label = f"n={row['task_count']} | {row['sensitive_fraction']:.0%} sensitive | {row['scheduler']}"
        parts.append(f'<text x="28" y="{y+16}" font-size="13">{html.escape(label)}</text>')
        parts.append(f'<rect x="300" y="{y}" width="{mean*scale:.2f}" height="23" rx="3" fill="{COLORS[row["scheduler"]]}"/>')
        left, right = 300 + max(0, mean-sd)*scale, 300 + (mean+sd)*scale
        parts.append(f'<path d="M {left} {y+6} v 12 M {left} {y+12} H {right} M {right} {y+6} v 12" stroke="#0f172a" fill="none"/>')
        parts.append(f'<text x="{right+9}" y="{y+17}" font-size="12">{mean:.3f} ± {sd:.3f}</text>')
    parts.append('</g></svg>')
    path.write_text('\n'.join(parts), encoding='utf-8')


def report(output, rows, summaries, exact_result):
    pairs = defaultdict(dict)
    for r in rows:
        pairs[(r['task_count'], r['sensitive_fraction'], r['seed'])][r['scheduler']] = r
    wins = losses = ties = 0
    for group in pairs.values():
        delta = group['pso']['mean_completion_s'] - group['greedy']['mean_completion_s']
        if abs(delta) < 1e-9:
            ties += 1
        elif delta < 0:
            wins += 1
        else:
            losses += 1
    text = ['# Experiment report', '',
        'Generated from this run. All task times are simulated seconds. Scheduler runtimes are measured on the executing machine.', '',
        '## Method', '',
        'All requests arrive together at time zero. Each worker has one execution slot. '
        'Input order is fixed within each worker; only destination assignment is optimised. '
        'Transmission takes half the configured round-trip delay in each direction, with no bandwidth contention. '
        'Both local nodes are trusted by assumption; sensitive data cannot be placed on untrusted nodes. '
        'Each algorithm receives exactly the same tasks for each scenario and seed. '
        'Sensitivity is assigned to a rounded number of tasks; actual counts are included in runs.csv. '
        'PSO uses random initialisation and optimises mean completion time only.', '',
        '## Results', '',
        f'Across {len(pairs)} paired workloads, PSO beat greedy {wins} times, tied {ties} times and lost {losses} times (tolerance 1e-9 seconds).', '',
        f'Total policy violations: {sum(r["policy_violations"] for r in rows)}.', '',
        '| Tasks | Sensitive | Scheduler | Mean completion (s) | SD across seeds (s) | Mean scheduler (ms) |',
        '|---:|---:|---|---:|---:|---:|']
    for r in summaries:
        text.append(f'| {r["task_count"]} | {r["sensitive_fraction"]:.0%} | {r["scheduler"]} | {r["mean_completion_s"]:.4f} | {r["sd_completion_s"]:.4f} | {r["mean_scheduler_ms"]:.3f} |')
    text += ['', '![Scheduler comparison](comparison.svg)', '', '![Security sensitivity](sensitivity.svg)', '',
        '## Tiny-instance exact check', '',
        f'For five tasks, the optimum is {exact_result["optimum_s"]:.6f}s and PSO achieves {exact_result["pso_s"]:.6f}s '
        f'(gap {exact_result["gap_percent"]:.3f}%). This is an exhaustive optimum over valid placements with fixed task order.', '',
        '## Interpretation and limitations', '',
        'PSO is a heuristic, not a guarantee of improvement. Greedy is a strong baseline for this simple model. '
        'The score-to-destination mapping is discontinuous and PSO can stagnate, especially as the task count grows. '
        'A higher sensitive fraction removes cloud choices, reducing available capacity; this is not encryption overhead.', '',
        'Reported completion times exclude scheduler runtime to keep simulation outputs reproducible. '
        'The separate mean_with_scheduler_s field adds the measured one-off batch scheduling time to every task. '
        'It is a hybrid estimate, not measured distributed-system latency. Runtime varies by machine and timing noise.', '',
        'No real inference, network, cloud billing or power measurements are performed. No energy or cost claims are made. '
        'The security mechanism is a simulated placement policy; it does not provide encryption, authentication, '
        'tamper-proof logs or protection against a malicious host or false sensitivity labels. '
        'The experiment uses synthetic batches, exact runtime estimates, no failures and no task migration. '
        'SD error bars describe seed variability, not statistical significance or confidence intervals.', '',
        '## Reproduce', '',
        'Use the command recorded in metadata.json with the saved config.json. '
        'Assignments and simulated metrics are deterministic for the same code, config and seeds; timing are not. '
        'Source SHA-256 hashes and Python/platform details are recorded in metadata.json.', '']
    (output / 'REPORT.md').write_text('\n'.join(text), encoding='utf-8')
