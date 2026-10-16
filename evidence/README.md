# Execution evidence

These are real browser screenshots of evidence pages built from an actual local Python execution. They are **not terminal screenshots**, cloud-console screenshots, or independent certification. The browser pages display captured stdout/stderr, actual CSV rows and generated SVG charts. No output has been invented.

## Screenshots

| Screenshot | What it shows | Underlying evidence |
|---|---|---|
| `screenshots/01-tests.jpg` | Eight automated tests passed | `tests.txt` |
| `screenshots/02-execution.jpg` | All 270 scheduler runs completed with exit code 0 | `execution.txt` |
| `screenshots/03-security-audit.jpg` | 7,200 assignments, 2,160 sensitive, zero sensitive-to-cloud placements | `results/audit.csv`, `audit_verification.json` |
| `screenshots/04-comparison.jpg` | Scheduler performance at 30% sensitivity | `results/summary.csv`, `results/comparison.svg` |
| `screenshots/05-sensitivity.jpg` | Effect of sensitive-data restrictions for 20 tasks | `results/summary.csv`, `results/sensitivity.svg` |

The screenshots were captured from a browser rendering these HTML pages without image editing. `build_pages.py` creates the pages from the logs and CSV data. Open the HTML files directly in a browser to inspect them.

## Reproduce from the project root

```bash
python3 -m unittest discover -s tests -v
python3 main.py --output evidence/results
```

To capture fresh logs on macOS/Linux:

```bash
python3 -m unittest discover -s tests -v > evidence/tests.txt 2>&1
python3 main.py --output evidence/results > evidence/execution.txt 2>&1
python3 evidence/build_pages.py
```

The originally captured logs also record the commands and subprocess exit codes. Rerunning produces new measured runtimes. Rebuilding the HTML does not refresh the existing screenshots; capture them again in your browser after regenerating results.

## Integrity and scope

`SHA256SUMS.txt` records hashes of this evidence bundle and the project source files at packaging time. Hashes help identify subsequent changes; they are not signed attestations or proof of authorship. Experiment metadata records source hashes, Python version, platform.

All completion times are simulated. Only scheduler runtime and test/experiment execution are actual local measurements. These files demonstrate the implemented simulator and its results, not a deployed AI service, real network timings or real-world security guarantees.

Project run dates are omitted from metadata and browser views. Source and evidence checksums have been refreshed after this presentation change. Screenshot `06-project-viewer.jpg` shows the local navigation page.
