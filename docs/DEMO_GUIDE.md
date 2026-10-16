# Five-minute demonstration

1. **Problem (30 seconds):** explain that faster cloud compute may be offset by network delays and that sensitive data must remain local under this project's policy.
2. **Inputs (45 seconds):** open `configs/default.json`. Show node speeds, delays, trust flags, task counts and seeds. Explain that these are synthetic assumptions.
3. **Run (45 seconds):** run `python3 main.py --quick`. Open `results/audit.csv`; sensitive tasks must have local destinations.
4. **Compare (one minute):** open `examples/results/comparison.svg` and `sensitivity.svg`. Explain the actual outcome, including any cases where greedy beats PSO. Error bars show seed variation.
5. **Security check (45 seconds):** run `python3 -m unittest discover -s tests -v`. Explain the deliberately invalid cloud assignment test.
6. **Research limits (one minute):** no actual ML model or network deployment; random synthetic batches; fixed task order; exact predicted runtimes; scheduler overhead measured separately. Suggest one next experiment.

## Questions you should be able to answer

**Why PSO?** The batch has many possible assignments, and PSO searches without enumerating all of them. It is not automatically better than a simple method.

**What does a particle mean?** A matrix of destination scores, with one row per task. Decode the highest-scoring eligible node in each row.

**What is optimised?** Mean simulated task completion time, subject to trusted-node placement restrictions.

**Why not just use cloud?** The placement policy excludes it for sensitive tasks, and its network delay can affect performance.

**What is the security contribution?** Enforced data placement and independent auditing. There is no encryption or attack detection.

**Why can greedy win?** This simple system suits immediate earliest-completion decisions; PSO's finite random search may stagnate and costs more computation.

**Is the optimum really exact?** For the five-task reference, all eligible destination assignments are evaluated, with fixed task order. It is not an optimum over task permutations or arbitrary distributed-system behaviour.

## Suggested submission structure

Problem and objectives; related research you personally review; system assumptions; scheduler methods; security scope; reproducible experiments; actual results; limitations; conclusion. Cite any external material and disclose AI assistance as your university requires.
