# Threat model and security scope

## Asset and policy

The asset is a task input marked sensitive. Policy: such an input may only be assigned to a node whose `trusted` attribute is true. The default configuration marks the two local nodes trusted and cloud untrusted.

## Assumptions

- Labels are correct and supplied by a trusted caller.
- Node trust configuration and program code are not modified by an adversary.
- A task executes on the destination selected by the simulation.
- Local trusted nodes are not compromised.

## In-scope failure

A scheduling decision accidentally places sensitive work on an untrusted node. Eligibility filtering prevents this, and the independent checker detects it if an invalid assignment is supplied. The simulator refuses to evaluate violating placements.

## Out of scope

Mislabelled data, malicious administrators, compromised nodes, network interception, malware, credential theft, malicious task content, data remaining in storage and tampered CSV logs. No actual task payload is transmitted or stored. The project does not claim compliance with a legal or industry standard.

## Controls and evidence

| Control | Implementation | Evidence |
|---|---|---|
| Classification | `Task.sensitive` | `tasks.csv` |
| Eligibility enforcement | `allowed_destinations` plus PSO masked decoding | Scheduler tests |
| Independent validation | `audit_policy`; rejection in `evaluate` | Deliberate violation test |
| Decision recording | Per-task CSV audit | `audit.csv` |

Audit logs record simulation decisions, not security events from a real deployment. They are ordinary editable files. A zero-violation result demonstrates policy compliance under the stated assumptions only.
