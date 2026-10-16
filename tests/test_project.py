import tempfile
import unittest
from pathlib import Path
from simulation import Task, Node, DEFAULT_NODES, generate_tasks, evaluate, audit_policy
from schedulers import round_robin, greedy, pso, exact
from main import load_config, run, ROOT


class SchedulerTests(unittest.TestCase):
    def test_hand_calculated_network_and_queue(self):
        nodes = (Node('local', 10, 0.2, True),)
        result = evaluate([Task(0, 10, False), Task(1, 20, True)], [0, 0], nodes)
        self.assertAlmostEqual(result['rows'][0]['completion_s'], 1.2)
        self.assertAlmostEqual(result['rows'][1]['start_s'], 1.1)
        self.assertAlmostEqual(result['makespan_s'], 3.2)
        self.assertAlmostEqual(result['mean_completion_s'], 2.2)

    def test_policy_detects_and_rejects_violation(self):
        tasks = [Task(5, 10, True)]
        self.assertEqual(audit_policy(tasks, [2]), [5])
        with self.assertRaises(ValueError):
            evaluate(tasks, [2])

    def test_all_schedulers_obey_policy(self):
        for fraction in (0, 0.3, 1):
            tasks = generate_tasks(20, fraction, 1)
            assignments = [round_robin(tasks), greedy(tasks), pso(tasks, particles=5, iterations=4)[0]]
            for assignment in assignments:
                self.assertFalse(audit_policy(tasks, assignment))
                self.assertEqual(len(evaluate(tasks, assignment)['rows']), 20)

    def test_known_optimum(self):
        nodes = (Node('a', 1, 0, True), Node('b', 1, 0, True))
        tasks = [Task(0, 1, False), Task(1, 1, False)]
        self.assertEqual(evaluate(tasks, exact(tasks, nodes), nodes)['mean_completion_s'], 1)

    def test_exact_lower_bound_and_pso_monotonicity(self):
        tasks = generate_tasks(5, 0.4, 42)
        optimum = evaluate(tasks, exact(tasks))['mean_completion_s']
        assignment, history = pso(tasks, seed=42)
        self.assertGreaterEqual(evaluate(tasks, assignment)['mean_completion_s'] + 1e-12, optimum)
        self.assertTrue(all(b <= a for a, b in zip(history, history[1:])))
        self.assertAlmostEqual(history[-1], evaluate(tasks, assignment)['mean_completion_s'])

    def test_reproducibility(self):
        tasks = generate_tasks(10, 0.3, 3)
        self.assertEqual(tasks, generate_tasks(10, 0.3, 3))
        self.assertEqual(pso(tasks, seed=3), pso(tasks, seed=3))
        other = generate_tasks(10, 0.6, 3)
        self.assertEqual([t.work_units for t in tasks], [t.work_units for t in other])

    def test_invalid_inputs(self):
        for count, fraction in [(0, 0.3), (2, 1.1)]:
            with self.assertRaises(ValueError):
                generate_tasks(count, fraction, 0)
        tasks = [Task(0, 10, True)]
        for assignment in ([], [-1], [3]):
            with self.assertRaises(ValueError):
                evaluate(tasks, assignment)
        with self.assertRaises(ValueError):
            greedy(tasks, (Node('cloud', 10, 0, False),))
        with self.assertRaises(ValueError):
            pso(tasks, iterations=0)
        with self.assertRaises(ValueError):
            evaluate(tasks, [0], (Node('bad', 0, 0, True),))

    def test_end_to_end_exports(self):
        config, nodes = load_config(ROOT / 'configs/default.json')
        config.update(task_counts=[5], sensitive_fractions=[0.4], seeds=[0])
        config['pso'].update(particles=3, iterations=2)
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder)
            run(config, nodes, output)
            for filename in ('runs.csv', 'audit.csv', 'comparison.svg', 'REPORT.md', 'metadata.json', 'exact_check.json'):
                self.assertGreater((output / filename).stat().st_size, 0)


if __name__ == '__main__':
    unittest.main()
