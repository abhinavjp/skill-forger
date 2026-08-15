# Final Skill Engineering & Review Specification

**Purpose:** Source of truth for implementing one agent-agnostic Skill that can later:

1. help create/draft a new Agent Skill; and
2. deeply review an existing Agent Skill.

This specification defines the engineering rules, review model, eval model, architecture and implementation contract. It does **not** implement the Skill.

---

# 1. Evidence classes

Every rule used by the future Skill must carry one of these classifications.

## Universal

Portable requirement or engineering principle that should apply across compatible Agent Skill hosts.

## Strong heuristic

Supported by official guidance, multiple implementations or evidence, but legitimate exceptions exist.

## Platform-specific

Depends on Claude Code, Codex, Cursor, Antigravity or another host implementation.

## Situational

Only applicable when the Skill has the relevant characteristic, such as mutation, external calls or large-input processing.

## Needs validation

Plausible technique without enough evidence to recommend automatically. Require eval evidence before treating it as beneficial.

The Skill must never silently promote a heuristic or platform feature to Universal.

---

# 2. Governing principles

## 2.1 Optimize measured utility, not checklist compliance

**Universal**

A Skill is useful only if it improves the target agent's ability to complete intended tasks at acceptable cost and risk.

The future reviewer must therefore consider:

* functional correctness;
* trigger precision and recall;
* harmful activation;
* safety;
* context/token cost;
* latency;
* tool/command cost;
* maintainability;
* portability where claimed.

A longer or more structured Skill is not inherently better.

Recent empirical work found that Skills can cause negative transfer, including functional and efficiency regressions when procedures and verification become excessive.
Evidence: [From Raw Experience to Skill Consumption](https://arxiv.org/abs/2608.11888)

---

## 2.2 Use the smallest mechanism that reliably solves the problem

**Strong heuristic**

Do not default every reusable instruction to a Skill.

Choose among:

* Skill;
* persistent Rule / `AGENTS.md` / `CLAUDE.md`;
* script/code;
* hook/CI/validator;
* MCP/tool/API;
* subagent;
* workflow/command;
* one-off prompt.

---

## 2.3 Separate routing from execution

**Universal**

A Skill has two independent failure surfaces:

1. **Should the Skill activate?**
2. **Does the Skill work after activation?**

They require separate review and evals.

Official Agent Skills guidance treats name/description as discovery metadata and supports dedicated trigger evaluation.
Evidence: [Agent Skills specification](https://agentskills.io/specification), [Optimizing descriptions](https://agentskills.io/skill-creation/optimizing-descriptions)

---

## 2.4 Progressive disclosure is architectural

**Universal for Agent Skills-compatible hosts**

Use:

```text
name + description
        ↓
SKILL.md
        ↓
conditional references/resources/scripts
```

Do not load all supporting knowledge into the initial context.

Evidence: [Agent Skills specification](https://agentskills.io/specification)

---

## 2.5 Determinism should replace model reasoning only where it earns its cost

**Strong heuristic**

Prefer deterministic execution for:

* parsing;
* filtering;
* sorting;
* schema validation;
* exact transformations;
* filesystem inventory;
* static checks;
* repeatable command sequences.

Do not create scripts merely because scripts are possible.

Compare complexity, maintenance and runtime benefit.

---

## 2.6 Verification must be proportional

**Strong heuristic**

Use the cheapest validation that materially reduces relevant failure risk.

Do not reward:

```text
more tests
more validators
more agents
more tool calls
more procedural gates
```

unless they improve expected outcome.

Excessive mandatory verification can itself create negative transfer and efficiency regressions.
Evidence: [From Raw Experience to Skill Consumption](https://arxiv.org/abs/2608.11888)

---

# 3. Architecture and mechanism selection

This is the first gate in both Create and Review modes.

## 3.1 Mechanism selection table

| Need                                                        | Default mechanism                          | Applicability                 |
| ----------------------------------------------------------- | ------------------------------------------ | ----------------------------- |
| Reusable specialised workflow used only for relevant tasks  | Skill                                      | Universal concept             |
| Persistent repository/project guidance                      | Rule / `AGENTS.md` / `CLAUDE.md`           | Strong heuristic              |
| Exact repeatable operation                                  | Script/code                                | Strong heuristic              |
| Requirement must be enforced regardless of model compliance | Hook / validator / CI / permission control | Strong heuristic              |
| External data/action capability                             | MCP/tool/API/connector                     | Universal concept             |
| Independent context-heavy bounded task                      | Subagent                                   | Situational                   |
| Explicit fixed user-invoked sequence                        | Workflow/command/manual Skill              | Situational/platform-specific |
| One-off instruction                                         | Prompt                                     | Strong heuristic              |

Platform documentation exposes these as distinct customization layers.
Evidence: [Codex customization](https://developers.openai.com/codex/customization/overview), [Cursor customization](https://cursor.com/docs/customize-cursor), [Antigravity Skills](https://antigravity.google/docs/skills)

---

## R1. Correct mechanism

**Check →** Is each responsibility implemented through the appropriate mechanism?

**Detection →**

* identify requirements applying to every task;
* identify exact/repeatable logic;
* identify external capabilities;
* identify mandatory security/compliance controls;
* identify independent parallel/context-heavy work.

**Severity →**

* Critical if wrong mechanism creates a safety/security failure;
* High if it materially harms correctness;
* Medium otherwise.

**Recommended action →** Move only the misplaced responsibility to the more appropriate mechanism.

**Validation/eval →** Compare behaviour before/after mechanism change where consequential.

**Applicability →** Universal review dimension; specific mechanisms may be platform-specific.

---

# 4. Skill design and structure

## 4.1 Scope must be cohesive, not arbitrarily narrow

**Strong heuristic**

A Skill should contain capabilities that share enough of:

* trigger semantics;
* workflow;
* domain knowledge;
* tools;
* lifecycle;
* references.

Splitting has a cost:

* more discovery entries;
* overlapping descriptions;
* duplicated guidance;
* catalog pressure.

Codex explicitly notes catalog/context limits and may truncate descriptions or omit Skills when the available Skill list grows.
Evidence: [Codex Skills](https://developers.openai.com/codex/build-skills)

---

## R2. Scope and decomposition

**Check →** Does the Skill contain unrelated capabilities, or has one coherent capability been over-fragmented?

**Detection →** Compare branches across:

* trigger surface;
* workflow;
* dependencies;
* references;
* expected outputs.

**Severity →** High if routing ambiguity or irrelevant context causes failures; otherwise Medium.

**Recommended action →**

* split materially independent capabilities;
* keep related branches together with conditional disclosure.

**Validation/eval →** Trigger tests with neighbouring Skills and execution tests across branches.

**Applicability →** Strong heuristic.

---

## 4.2 Standard structure

The portable core should use the open Agent Skills format.

Minimum:

```text
skill-name/
└── SKILL.md
```

Optional:

```text
references/
scripts/
assets/
evals/
fixtures/
adapters/
```

Only `SKILL.md` is structurally required by the open format.
Evidence: [Agent Skills specification](https://agentskills.io/specification)

Do not create empty directories for architectural symmetry.

---

## 4.3 `SKILL.md` content

Prefer to keep only material needed on most activations:

* purpose;
* core workflow;
* essential constraints;
* branch selection;
* conditional reference pointers;
* script/tool invocation contracts;
* completion conditions where needed.

The open specification recommends keeping `SKILL.md` below approximately 500 lines / 5,000 tokens and moving detail into supporting resources.

Treat this as a **budget heuristic, not a correctness threshold**.
Evidence: [Agent Skills specification](https://agentskills.io/specification)

---

# 5. Trigger and discovery engineering

## 5.1 Portable routing metadata

**Universal**

For implicit discovery, treat:

```text
name + description
```

as the portable routing interface.

Do not assume description alone determines activation.

Explicit invocation is a separate mode and must be evaluated separately.

---

## R3. Trigger metadata quality

**Check →** Do name and description communicate what the Skill does and when it is relevant?

**Detection →**

* inspect semantic specificity;
* test representative user wording;
* test adjacent tasks;
* test important synonyms/paraphrases.

**Severity →** Critical for implicitly activated Skills when routing materially fails.

**Recommended action →**

* state capability;
* include important trigger concepts;
* communicate meaningful boundaries;
* remove generic language.

**Validation/eval →** Positive/negative/boundary trigger suite.

**Applicability →** Universal.

---

## R4. Trigger precision and recall

**Check →** Does the Skill activate when intended and remain inactive when irrelevant?

**Detection →**

* positive;
* negative;
* paraphrase;
* boundary;
* near-neighbour;
* adversarial;
* competing-Skill queries.

**Severity →** High/Critical.

**Recommended action →** Modify routing metadata or Skill boundaries.

**Validation/eval →** Re-run trigger suite across multiple trials where model variance matters.

**Applicability →** Universal.

---

## R5. Catalog competition

**Check →** Does routing still work when realistic neighbouring Skills are installed?

**Detection →** Test in:

* isolation;
* realistic Skill catalog;
* high-overlap catalog where relevant.

**Severity →** High if real deployment includes substantial catalog competition.

**Recommended action →**

* differentiate descriptions;
* consolidate redundant Skills;
* alter invocation strategy if supported.

**Validation/eval →** Catalog-aware trigger eval.

**Applicability →** Strong heuristic; exact catalog behaviour is platform-specific.

---

## 5.2 Front-loading semantics

**Strong heuristic**

Put trigger-critical meaning early in name/description.

This is particularly valuable where hosts truncate catalog metadata. Codex documents description truncation/catalog limits.
Evidence: [Codex Skills](https://developers.openai.com/codex/build-skills)

Do not mechanically optimize for “magic” leading words.

---

## 5.3 Matt Pocock's “leading words”

**Needs validation**

Use distinctive domain vocabulary when natural and representative of actual user requests.

Do not recommend vocabulary changes solely because they appear earlier.

Require trigger A/B evidence when claiming improvement.

Evidence: [writing-for-agents](https://github.com/mattpocock/skills/blob/main/skills/productivity/writing-for-agents/SKILL.md)

---

# 6. Progressive disclosure and context/token efficiency

## R6. Progressive disclosure

**Check →** Is information loaded at the lowest level needed to perform the current branch?

**Detection →**

* inspect always-loaded instructions;
* map branch-specific content;
* inspect references loaded during eval traces.

**Severity →** High when excess context materially harms performance; otherwise Medium.

**Recommended action →**

* retain core instructions in `SKILL.md`;
* defer conditional detail;
* remove unnecessary always-loaded content.

**Validation/eval →**

* compare token/context usage;
* verify task correctness does not regress.

**Applicability →** Universal principle for standard-compatible hosts.

---

## R7. Reference reachability

**Check →** Can the agent reliably know when a deferred reference is needed?

**Detection →**

* broken paths;
* vague pointers;
* deep reference chains;
* failure to load required resource in evals.

**Severity →** High when omitted reference affects correctness.

**Recommended action →** Use an explicit condition such as:

```text
If authentication code changed, read references/auth.md.
```

instead of:

```text
See references for more information.
```

**Validation/eval →** Cases exercising that reference branch.

**Applicability →** Strong heuristic grounded in progressive disclosure.

---

## R8. Branch isolation

**Check →** Are materially different branches loading only their relevant knowledge?

**Detection →**

* build branch-to-reference map;
* inspect unnecessary resource loads;
* compare branch traces.

**Severity →** Medium/High.

**Recommended action →** Route first, then load branch-specific resources.

**Validation/eval →** Context/token and execution comparison.

**Applicability →** Strong heuristic.

---

## R9. Context filtering

**Check →** Could raw task inputs be reduced before reasoning without losing necessary evidence?

Examples:

* changed files rather than entire repository;
* relevant log clusters rather than full logs;
* schema subset rather than entire API catalog;
* search hits plus context rather than complete documents.

**Detection →** Compare consumed evidence against raw input size.

**Severity →** High for large-input Skills.

**Recommended action →** Add retrieval/filter/extraction with provenance.

**Validation/eval →**

* correctness before/after;
* token/context reduction;
* missed-evidence tests.

**Applicability →** Strong heuristic.

---

## R10. Instruction necessity

**Check →** Does each substantial instruction address an observed/credible failure mode?

**Detection →**

* flag generic instructions;
* flag duplicated constraints;
* identify expensive procedural rules;
* use ablation when impact is uncertain.

**Severity →** Medium, High where unnecessary procedure creates measurable regression.

**Recommended action →** Remove, weaken or make conditional.

**Validation/eval →** With-instruction vs without-instruction comparison.

**Applicability →** Strong heuristic.

---

## 6.1 No-op instructions

Examples:

```text
Think carefully.
Be accurate.
Use good practices.
Read the request.
```

These are removal candidates, not automatic defects.

Model behaviour can change; use ablation for important cases.

---

## 6.2 Co-location and information hierarchy

Treat both as **diagnostic heuristics**, not directly measurable quality scores.

Raise a finding only when poor organization creates a concrete symptom:

* requirement missed;
* contradiction;
* unnecessary reference chasing;
* repeated loading;
* workflow buried behind irrelevant material.

Evidence and terminology influenced by Matt Pocock's `writing-for-agents`, but the exact conceptual model is not part of the open specification.
Evidence: [writing-for-agents](https://github.com/mattpocock/skills/blob/main/skills/productivity/writing-for-agents/SKILL.md)

---

# 7. Deterministic versus agentic execution

## 7.1 Decision rule

Use deterministic execution when all or most of these are true:

* operation is precisely specifiable;
* same input should yield same result;
* failure is mechanically detectable;
* model reasoning adds little value;
* operation repeats frequently;
* implementation is simpler than repeated reasoning.

Use agent reasoning when:

* ambiguity must be resolved;
* competing objectives require judgement;
* semantic interpretation matters;
* inputs vary substantially;
* no stable deterministic specification exists.

---

## R11. Deterministic extraction opportunity

**Check →** Is the model repeatedly doing mechanically reproducible work?

**Detection →**

* repeated parsing;
* repeated filtering;
* exact sorting;
* static inventory;
* repeated deterministic shell/tool loops.

**Severity →** Medium/High.

**Recommended action →** Extract only the stable deterministic portion.

**Validation/eval →** Compare correctness, context, latency and maintenance complexity.

**Applicability →** Strong heuristic.

---

## R12. Excessive deterministic pipeline

**Check →** Has the Skill converted flexible reasoning into an unnecessarily rigid pipeline?

**Detection →**

* excessive mandatory scripts;
* mandatory full validation for low-risk tasks;
* complex pipeline on trivial requests.

**Severity →** Medium/High when it causes negative transfer.

**Recommended action →** Return non-critical decisions to agent reasoning or make gates conditional.

**Validation/eval →** Differential eval against simpler version.

**Applicability →** Strong heuristic.

---

# 8. Scripts, tools, hooks, MCP and subagents

## 8.1 Scripts

### Normal execution

**Strong heuristic**

Prefer stable interfaces:

```text
script --help
script input
structured output
meaningful exit codes
```

Avoid loading implementation source merely to execute the tool.

Antigravity explicitly recommends treating scripts as executable resources rather than unnecessary context.
Evidence: [Antigravity Skills](https://antigravity.google/docs/skills)

### Review/security mode

Inspect source where required to establish:

* trust;
* side effects;
* correctness;
* portability;
* security.

---

## R13. Script quality

**Check →** Does the script have a stable, inspectable execution contract appropriate to its role?

**Detection →**

* entry point;
* inputs;
* outputs;
* exit/error behaviour;
* privileges;
* network/filesystem operations.

**Severity →**

* Critical for unsafe privileged behaviour;
* High for correctness-critical instability;
* Medium otherwise.

**Recommended action →** Stabilize interface or remove unnecessary script.

**Validation/eval →** Unit/integration test plus dependent Skill eval.

**Applicability →** Situational.

---

## 8.2 Tools and MCP

Use an MCP/tool when external capability or live data is required.

Do not load or expose every tool “just in case.”

---

## R14. Tool efficiency

**Check →** Are tool calls broader, more repetitive or more numerous than necessary?

**Detection →**

* duplicate searches;
* repeated metadata discovery;
* full enumeration then immediate filtering;
* repeated fetch of same artifact.

**Severity →** Medium; High if cost/latency becomes material.

**Recommended action →**

* narrow queries;
* reuse results;
* batch where supported;
* prefilter.

**Validation/eval →** Tool-call count + correctness comparison.

**Applicability →** Strong heuristic.

---

## 8.3 Hooks

Hooks are appropriate when behaviour must be enforced independent of model judgement.

Examples:

* block forbidden operation;
* run validator before mutation;
* enforce policy;
* gate dangerous commands.

Exact hook systems differ by platform.

Evidence: [Codex Hooks](https://developers.openai.com/codex/hooks), [Antigravity hooks](https://antigravity.google/docs/skills)

---

## R15. Deterministic enforcement

**Check →** Is the Skill asking the model to obey an invariant that must never be bypassed?

**Detection →** Terms such as:

* must always;
* must never;
* security requirement;
* destructive action restriction.

**Severity →** Critical where bypass causes security/data risk.

**Recommended action →** Move enforcement into hook/permission/CI/validator where host permits; keep explanatory guidance in Skill.

**Validation/eval →** Attempt violating action in controlled test.

**Applicability →** Strong heuristic; enforcement implementation is platform-specific.

---

## 8.4 Subagents

Use only where delegation brings material benefit:

* context isolation;
* parallel independent work;
* specialist reasoning;
* protection of main thread from noisy intermediate data.

Codex, Cursor and Antigravity expose subagent/context-isolation mechanisms, but implementation differs.
Evidence: [Codex subagents](https://developers.openai.com/codex/subagents), [Antigravity subagents](https://antigravity.google/docs/subagents)

---

## R16. Subagent justification

**Check →** Does delegation provide enough benefit to justify additional execution?

**Detection →**

* task independence;
* context volume;
* possibility of parallelism;
* duplicate work;
* merge/reconciliation cost.

**Severity →** Medium.

**Recommended action →**

* use single agent for small/serial tasks;
* delegate bounded independent work when worthwhile.

**Validation/eval →** Compare delegated vs single-agent success, cost and latency.

**Applicability →** Situational.

---

# 9. Reliability, safety, completion and failure handling

## R17. Proportional validation

**Check →** Is probabilistic work validated where failure matters, without unnecessary procedure?

**Detection →**

* identify outputs with deterministic validators;
* assess failure impact;
* inspect validation cost.

**Severity →**

* Critical/High when incorrect output has serious consequence;
* Medium otherwise.

**Recommended action →** Add the cheapest adequate validator.

Examples:

```text
generated JSON → schema parser
code edit → targeted tests
config edit → config parser
migration → migration checker
```

**Validation/eval →** Measure error reduction and added cost.

**Applicability →** Strong heuristic.

---

## R18. Completion semantics

**Check →** Could the agent plausibly stop at an intermediate state?

**Detection →**

* multi-stage workflow;
* intermediate artifact resembling final output;
* missing verification;
* unclear definition of done.

**Severity →** High for multi-step workflows; Low/Not applicable for simple reference Skills.

**Recommended action →** Add minimal observable completion conditions.

**Validation/eval →** Interrupted/incomplete execution cases.

**Applicability →** Situational.

---

## R19. Premature-completion risk

Treat this as part of **Completion semantics**, not a separate duplicated rule.

Review for:

* unvisited required branches;
* missing validation stage;
* partial file review presented as complete;
* tool output presented as final solution.

---

## R20. Failure recovery

**Check →** Can expected failure lead to unsafe continuation or unnecessary loss of work?

**Applies when →**

* external tools;
* stateful operation;
* network calls;
* long-running workflows.

**Detection →**

* inject missing dependency;
* timeout;
* malformed input;
* partial completion.

**Severity →** High/Critical according to impact.

**Recommended action →**

* stop on unsafe failure;
* preserve useful intermediate state;
* clearly surface failure;
* retry only when plausible.

**Validation/eval →** Failure-injection cases.

**Applicability →** Situational.

---

## R21. Retry behaviour

Part of **Failure recovery**, not an independent mandatory requirement.

Use retries only when failure is plausibly transient.

Require:

* bounded attempts;
* no infinite retry;
* no retry on deterministic validation failure unless state changes;
* optional backoff where external service semantics warrant it.

---

## R22. Idempotency

**Check →** Can rerunning a mutating Skill duplicate or corrupt state?

**Detection →** Execute the operation twice against controlled state.

**Severity →** Critical/High for dangerous mutations.

**Recommended action →**

* precondition/state check;
* stable identifier;
* update rather than duplicate;
* explicit user confirmation where non-idempotence is unavoidable.

**Validation/eval →** Re-run test.

**Applicability →** Situational, mutating Skills only.

---

## R23. Safety and least privilege

**Check →** Does the workflow request more authority than necessary?

**Detection →**

* filesystem scope;
* network access;
* secrets;
* shell;
* external mutation;
* destructive commands.

**Severity →** Critical.

**Recommended action →** Restrict capability using host permissions/tool boundaries, not prose alone.

**Validation/eval →** Controlled permission-denied and adversarial cases.

**Applicability →** Universal security objective; implementation platform-specific.

---

## R24. Untrusted Skill/resource security

**Check →** Can a Skill, reference, script or retrieved artifact redirect privileged behaviour or exfiltrate data?

**Detection →**

* provenance inspection;
* suspicious shell/network operations;
* credential access;
* embedded prompt injection;
* obfuscation;
* unexpected downloads.

**Severity →** Critical.

**Recommended action →**

* review source;
* sandbox;
* reduce permissions;
* remove unsafe dependency;
* require trust provenance.

**Validation/eval →** Adversarial fixture where appropriate.

**Applicability →** Universal.

Research increasingly identifies public Skill ecosystems as a supply-chain/security surface.
Evidence: [Agent Skills security study](https://arxiv.org/html/2604.03070v2)

---

# 10. Portability and platform-specific extensions

## 10.1 Portable core

**Universal portability requirement**

If a Skill claims to be agent-agnostic, the core must not require:

* Claude-only frontmatter;
* Codex-only agents;
* Cursor-only hooks;
* Antigravity-only permissions;
* host-specific filesystem paths;
* proprietary invocation syntax.

Use standard `SKILL.md` plus relative resources.

---

## R25. Portability boundary

**Check →** Does claimed portable behaviour depend on host-specific features?

**Detection →**

* frontmatter inspection;
* hardcoded paths;
* invocation syntax;
* hook names;
* named subagents;
* platform tool assumptions.

**Severity →** High when portability is claimed.

**Recommended action →**

* move feature into adapter;
* add capability detection;
* gracefully degrade;
* narrow compatibility claim.

**Validation/eval →** Standards validation + host-specific tests.

**Applicability →** Universal for portable Skills.

---

## 10.2 Format portability vs behavioural portability

Do not equate:

```text
Skill parses on multiple hosts
```

with:

```text
Skill behaves equivalently on multiple hosts
```

A portable Skill should record:

* standard compatibility;
* hosts tested;
* models tested where relevant;
* known deviations;
* untested environments.

Research indicates Skill utility can vary by target model/agent.
Evidence: [Microsoft Research: model-generated Agent Skills](https://www.microsoft.com/en-us/research/publication/from-raw-experience-to-skill-consumption-a-systematic-study-of-model-generated-agent-skills/)

---

# 11. Platform-specific guidance

These are adapters, not portable requirements.

## Claude Code

Potential features:

* Claude-specific invocation controls;
* hooks;
* subagents;
* `skill-creator`.

Claude-specific metadata such as `disable-model-invocation` must remain platform-specific.

Evidence: [Claude Code Skills](https://docs.anthropic.com/en/docs/claude-code/skills)

---

## OpenAI Codex

Potential features:

* `AGENTS.md`;
* Skills;
* hooks;
* subagents;
* sandbox/permissions;
* platform eval tooling.

Evidence: [Codex customization](https://developers.openai.com/codex/customization/overview)

---

## Cursor

Potential features:

* Rules;
* Skills;
* Hooks;
* subagents;
* MCP/tools;
* explicit Skill invocation.

Evidence: [Cursor customization](https://cursor.com/docs/customize-cursor)

---

## Google Antigravity

Potential features:

* Skills;
* Rules;
* workflows;
* hooks;
* subagents;
* permission controls.

Evidence: [Antigravity Skills](https://antigravity.google/docs/skills)

---

## Claude Code `skill-creator`

Treat as **optional supplemental tooling**, not a dependency.

Useful ideas include:

* generating test prompts;
* with/without comparisons;
* expectation grading;
* execution metrics;
* iterative Skill comparison.

Evidence: [Anthropic skill-creator](https://github.com/anthropics/skills/blob/main/skills/skill-creator/SKILL.md)

The future Skill must keep its canonical eval model runner-independent because platform tooling can itself fail or produce false negatives. Current issue reports document trigger-eval problems under some installations.
Evidence: [Anthropic Skills issue #1383](https://github.com/anthropics/skills/issues/1383)

---

# 12. Maintainability and evolution

## R26. Duplication and drift

**Check →** Is knowledge copied from another source that is expected to evolve independently?

**Detection →**

* exact duplication;
* repeated configuration values;
* version numbers;
* contradictions against known canonical sources.

**Severity →** High if stale data can cause incorrect operation; otherwise Medium.

**Recommended action →**

* point to canonical source;
* dynamically inspect it;
* mechanically generate derived content.

**Validation/eval →** Change source and verify Skill still behaves correctly where feasible.

**Applicability →** Strong heuristic.

Do not claim semantic staleness can be detected without a comparison source.

---

## R27. Source-of-truth choice

**Check →** Is the Skill using the appropriate authority for a fact?

**Detection →** Classify fact as:

* runtime state;
* repository configuration;
* external contract;
* policy;
* legislation;
* design intent.

**Severity →** High where wrong authority causes incorrect behaviour.

**Recommended action →** Use the authoritative source for that fact.

**Validation/eval →** Fixture with contradictory environment vs policy where relevant.

**Applicability →** Strong heuristic.

The environment is **not automatically** the source of truth.

---

## R28. Maintainability

**Check →** Can one concern be changed without requiring broad edits or duplicated updates?

**Detection →**

* repeated rule across files;
* cross-file coupling;
* duplicated adapter logic;
* unstable script interfaces.

**Severity →** Medium.

**Recommended action →** Consolidate actual source of truth and stabilize boundaries.

**Validation/eval →** Static inspection plus regression suite.

**Applicability →** Strong heuristic.

---

## R29. Regression preservation

**Check →** Are previously discovered failures retained as regression cases?

**Detection →** Compare change history/issues/eval corpus where available.

**Severity →** High for mature Skills.

**Recommended action →** Add historical failure as minimal reproducible eval case.

**Validation/eval →** Candidate must continue passing it.

**Applicability →** Strong heuristic.

---

# 13. Shared rule model for creation and review

Creation and review must use the same engineering rules R1–R29.

Do not maintain separate duplicated rule sets.

Create mode asks:

> How should the Skill be designed to satisfy each applicable rule?

Review mode asks:

> Does the existing Skill satisfy each applicable rule, and what evidence supports the finding?

---

# 14. Creation checklist

Use this order.

* [ ] Collect representative intended requests.
* [ ] Collect explicit non-goals and adjacent tasks.
* [ ] Select Skill vs Rule/script/hook/tool/subagent/prompt.
* [ ] Establish portability target and claimed hosts.
* [ ] Define observable success.
* [ ] Identify side effects and safety risks.
* [ ] Define implicit trigger boundary.
* [ ] Draft name and description.
* [ ] Build positive, negative and boundary trigger cases.
* [ ] Define minimal execution workflow.
* [ ] Identify necessary decision branches.
* [ ] Identify deterministic operations worth extracting.
* [ ] Identify large inputs worth filtering before context.
* [ ] Determine required tools/MCP.
* [ ] Determine whether subagents add measurable value.
* [ ] Define proportional validation.
* [ ] Define completion behaviour where multi-step ambiguity exists.
* [ ] Define failure/retry/idempotency only where applicable.
* [ ] Design progressive disclosure.
* [ ] Draft minimal `SKILL.md`.
* [ ] Add references only for genuinely conditional knowledge.
* [ ] Add scripts only when justified.
* [ ] Add platform adapters only when required.
* [ ] Create trigger evals.
* [ ] Create execution evals.
* [ ] Establish baseline/no-Skill or previous-version comparison.
* [ ] Run relevant multiple trials.
* [ ] Inspect efficiency metrics.
* [ ] Fix observed failures rather than adding speculative instructions.
* [ ] Preserve new failures as regressions.
* [ ] Document tested/untested platform claims.

---

# 15. Review checklist

Use this order.

* [ ] Inventory Skill package, related rules, scripts, resources and adapters.
* [ ] Validate standard structure/frontmatter.
* [ ] Reconstruct actual capability and side effects.
* [ ] Re-evaluate whether Skill is the correct abstraction.
* [ ] Review scope/decomposition.
* [ ] Inspect name/description.
* [ ] Map competing trigger surfaces.
* [ ] Inspect progressive disclosure.
* [ ] Validate reference reachability.
* [ ] Map branch-specific context.
* [ ] Detect excessive always-loaded content.
* [ ] Find deterministic extraction opportunities.
* [ ] Find pre-context filtering opportunities.
* [ ] Inspect scripts and executable resources.
* [ ] Inspect tools/MCP efficiency.
* [ ] Inspect hooks/deterministic enforcement.
* [ ] Inspect subagent use.
* [ ] Inspect proportional validation.
* [ ] Inspect completion/failure behaviour where applicable.
* [ ] Inspect retries/idempotency where applicable.
* [ ] Inspect permissions/security.
* [ ] Inspect platform coupling.
* [ ] Inspect duplication/drift/source-of-truth issues.
* [ ] Run deterministic static checks.
* [ ] Run trigger evals.
* [ ] Run execution evals.
* [ ] Compare against baseline/previous version.
* [ ] Measure resource cost after correctness.
* [ ] Run relevant adversarial/boundary tests.
* [ ] Rank findings by severity and confidence.
* [ ] Recommend the smallest evidence-supported changes.

---

# 16. Eval specification

Evals are a first-class part of Skill engineering but are not part of the open Skill format itself.

The canonical eval corpus must be platform-neutral.

---

## 16.1 Eval layers

### Layer A: Static validation

No model required.

Examples:

* frontmatter;
* file paths;
* broken references;
* missing fixtures;
* known platform metadata;
* portable eval-schema validation.

---

### Layer B: Trigger evals

Measure implicit routing independently from execution.

Required case types where relevant:

* positive;
* negative;
* paraphrase;
* boundary;
* near-neighbour;
* competing-Skill;
* adversarial;
* historical regression.

Do not mix explicit invocation into implicit-trigger precision/recall.

---

### Layer C: Execution-quality evals

Measure whether the Skill successfully performs its intended work.

Cases should include as appropriate:

* happy path;
* edge case;
* incomplete input;
* large input;
* failure injection;
* adversarial input;
* historical regression.

---

### Layer D: Differential evals

Compare:

```text
candidate Skill
vs
previous accepted Skill
vs
without Skill where informative
```

A Skill must not be assumed to improve the base model.

Official Agent Skills evaluation guidance recommends with/without or previous-version comparison.
Evidence: [Evaluating Skills](https://agentskills.io/skill-creation/evaluating-skills)

---

# 17. Eval fixtures

Maintain both:

## Known-good fixtures

Inputs where expected correct behaviour is clearly defined.

Examples:

* valid Skill;
* correct reference structure;
* safely mutating workflow;
* correctly scoped description.

## Intentionally defective fixtures

Purpose-built examples containing one or more known defects.

Examples:

* broken reference;
* overbroad description;
* false trigger neighbour;
* irrelevant massive reference;
* unsafe script;
* duplicated stale instruction;
* platform-specific field in allegedly portable Skill;
* workflow with premature completion;
* mutating operation that duplicates on retry.

Each defective fixture should identify the intended defect so deterministic and AI-review behaviour can be regression-tested.

---

# 18. Portable eval schema

Recommended project convention:

```yaml
version: 1

id: EX-001
kind: trigger | execution
category: positive | negative | boundary | adversarial | regression

prompt: |
  ...

fixtures: []

setup: []

trials: 1

expected:
  trigger: true

  outcome:
    assertions: []

  state:
    assertions: []

  process:
    required: []
    forbidden: []

graders:
  - type: deterministic
    check: ...

budgets:
  tokens: null
  duration_ms: null
  tool_calls: null
  commands: null

platforms:
  required: []
  optional: []

tags: []
```

This is **not** part of the Agent Skills standard.

Keep it extensible.

---

# 19. Grading strategy

Use this order.

## 19.1 Deterministic outcome/state grading

Preferred when possible.

Examples:

* expected file exists;
* parser succeeds;
* tests pass;
* state mutation correct;
* duplicate mutation absent.

---

## 19.2 Deterministic process grading

Use only when the process itself is required for correctness or safety.

Examples:

* security validator must run before deployment;
* forbidden destructive command must not execute.

Avoid requiring one exact trajectory when multiple valid approaches exist.

---

## 19.3 LLM judge

Use where semantic judgement is unavoidable.

Require:

* narrow criterion;
* explicit rubric;
* evidence-backed verdict;
* structured output;
* judge/model identifier if available.

---

## 19.4 Human review

Use for:

* judge calibration;
* high-value subjective criteria;
* disputed cases.

Anthropic also recommends deterministic/code-based grading wherever criteria can be encoded mechanically.
Evidence: [Anthropic eval guidance](https://docs.anthropic.com/en/docs/build-with-claude/develop-tests)

---

# 20. Multiple trials

Use multiple trials when:

* trigger behaviour varies;
* reasoning is stochastic;
* candidate versions are close;
* LLM judges are used;
* a failure appears intermittent.

Record at minimum:

```text
trial count
pass count
pass rate
```

Where useful:

```text
median tokens
median duration
variance
p95 latency
```

Do not claim statistical significance without sufficient data.

---

# 21. Efficiency metrics

Correctness takes priority.

After correctness, record where the host exposes them:

* input/context tokens;
* output tokens;
* duration;
* tool calls;
* commands;
* retries;
* errors;
* references loaded;
* subagents spawned;
* side-effect operations.

Do not optimize one metric in isolation.

---

# 22. Regression behaviour

Changes must trigger relevant regression suites.

## Name/description changed

Run:

* full trigger suite;
* competing-Skill cases;
* trigger regressions.

## Core workflow changed

Run:

* execution smoke;
* affected cases;
* historical regressions.

## Reference changed

Run cases that require that reference.

## Script changed

Run:

* script tests;
* dependent Skill evals.

## Adapter changed

Run that platform's validation and runtime suite.

## Safety/permission logic changed

Run:

* adversarial;
* failure;
* side-effect;
* permission cases.

Always run a minimal smoke suite.

---

# 23. Eval failure classification

A failed trial must be classified when possible as:

```text
Skill failure
routing failure
model variance
tool failure
fixture failure
harness failure
environment failure
grader failure
```

Do not punish the Skill for broken eval infrastructure.

This is especially important because current platform Skill-eval tooling has reported false-negative trigger failures.
Evidence: [Anthropic Skills issue #1383](https://github.com/anthropics/skills/issues/1383)

---

# 24. High-leverage techniques

Ranked by expected general value.

## 1. Differential evaluation

Compare Skill vs baseline/previous version.

Largest protection against negative transfer.

**Evidence class:** Universal for mature engineering.

---

## 2. Correct mechanism selection

Avoid forcing model reasoning where deterministic/persistent mechanisms are better.

**Evidence class:** Strong heuristic.

---

## 3. Progressive disclosure

Keep conditional knowledge out of always-loaded context.

**Evidence class:** Universal.

---

## 4. Pre-context filtering

Reduce raw task data before model reasoning while preserving evidence.

**Evidence class:** Strong heuristic.

---

## 5. Deterministic extraction

Turn stable exact repeated work into scripts/tools.

**Evidence class:** Strong heuristic.

---

## 6. Proportional deterministic validation

Validate model output where failures matter.

**Evidence class:** Strong heuristic.

---

## 7. Independent trigger engineering

Treat routing quality as its own measurable system.

**Evidence class:** Universal.

---

## 8. Completion semantics

Add observable done conditions for multi-stage workflows.

**Evidence class:** Situational / Strong heuristic.

---

## 9. Instruction ablation

Remove accumulated instructions that do not improve behaviour.

**Evidence class:** Strong heuristic.

---

## 10. Context-isolated subagents

Useful for large independent work, not default orchestration.

**Evidence class:** Situational.

---

# 25. Anti-patterns

The reviewer should recognize these as **investigation signals**, not automatic defects unless specified.

## Universal/strong anti-patterns

### Skill used as mandatory enforcement

Model instructed to enforce security/policy that should be deterministic.

### Broad vague discovery metadata

```text
Helps with engineering.
```

### Unconditional context dump

All domain references loaded for every request.

### Broken/weak context pointers

Critical reference exists but activation condition is unclear.

### Repeated deterministic reasoning loop

Agent repeatedly reconstructs exact information code could cheaply provide.

### Raw-data dumping

Massive logs/repos/docs placed directly into context despite cheap filtering.

### Verification theatre

Many checks measure procedure but not task success.

### Eval theatre

Tests confirm that instructions were followed but do not verify actual outcome/state.

### Instruction accumulation

Every observed failure causes another paragraph rather than fixing root cause.

### Exact-trace overfitting

Eval requires arbitrary tool ordering even though alternative trajectories are correct.

### Platform leakage

Portable Skill silently relies on proprietary host behaviour.

### Unbounded retries

Transient failures cause infinite/unsafe retry loops.

### Non-idempotent mutation without protection

Repeated run duplicates destructive or persistent actions.

### Excessive subagents

Delegation creates more coordination cost than useful isolation/parallelism.

### Copied canonical knowledge

Version/configuration duplicated in prose and becomes stale.

---

# 26. Severity model

## Critical

Likely to cause:

* security compromise;
* secret exposure;
* destructive action;
* materially unsafe external mutation;
* consistent wrong activation into dangerous capability;
* fundamental correctness failure in high-risk workflow.

Expected action: block release/acceptance until resolved or explicitly accepted.

---

## High

Materially affects:

* functional correctness;
* trigger precision/recall;
* critical reference loading;
* portability claim;
* completion reliability;
* repeated state corruption;
* significant negative transfer.

Expected action: fix before normal production use unless explicit trade-off accepted.

---

## Medium

Meaningful but bounded effect on:

* context efficiency;
* latency;
* maintainability;
* occasional correctness;
* tool cost;
* unnecessary procedure.

Expected action: prioritize according to measured impact.

---

## Low

Minor:

* clarity;
* organization;
* small redundancy;
* low-impact inefficiency.

Expected action: fix opportunistically.

Severity and **confidence must be separate**.

---

# 27. Automation responsibility matrix

## Deterministic

Suitable for:

* parsing frontmatter;
* validating required metadata;
* checking paths;
* broken references;
* file inventory;
* file size/token estimates;
* exact duplicate blocks;
* platform-extension lookup;
* eval-schema validation;
* missing fixtures;
* script existence/permissions;
* hardcoded path detection;
* deterministic outcome/state grading.

Do not use deterministic labels for semantic conclusions.

---

## AI judgement

Suitable for:

* correct mechanism;
* scope/cohesion;
* trigger semantics;
* pointer quality;
* branch decomposition;
* likely no-op instruction;
* procedural over-specification;
* deterministic-extraction opportunity;
* context-filtering opportunity;
* completion risk;
* subagent suitability;
* source-of-truth choice;
* maintainability;
* security intent analysis;
* platform-coupling interpretation.

Every AI finding must cite concrete Skill evidence.

---

## Runtime/eval

Required for:

* trigger precision/recall;
* Skill vs baseline utility;
* previous-version comparison;
* process predictability;
* reference retrieval reliability;
* completion behaviour;
* failure/retry behaviour;
* idempotency;
* tool efficiency;
* subagent effectiveness;
* token/time efficiency;
* negative-transfer detection.

---

## Hybrid

Use where static or AI analysis proposes a finding that runtime evidence can confirm.

---

# 28. Review finding format

Every important finding must use:

```text
Check
Finding
Evidence
Detection method
Severity
Confidence
Recommended action
Validation/eval
Automation type
Evidence class
Applicability
```

Where useful also provide:

```text
Good pattern
Failure pattern
```

Do not issue vague recommendations such as:

```text
Improve the structure.
Use better context.
Make the Skill clearer.
```

Every recommendation must identify a concrete change.

---

# 29. Review output priorities

Order findings by:

1. Safety/security
2. Functional correctness
3. Trigger/discovery
4. Negative transfer / procedural burden
5. Completion/failure handling
6. Portability
7. Context/tool efficiency
8. Maintainability
9. Minor authoring issues

Do not bury serious defects beneath style comments.

---

# 30. Claims still needing validation

The future Skill must not automatically recommend these without evidence.

## Leading-word vocabulary optimization

Plausible but exact wording advantage requires trigger tests.

## Router Skills

May reduce human discoverability burden but also add routing/context complexity.

Evaluate against:

* better automatic discovery;
* explicit invocation;
* consolidation.

## Precise ideal `SKILL.md` size

500 lines / ~5,000 tokens is recommended guidance, not demonstrated universal optimum.

## Exact optimal number of references

No universal target.

## Exact optimal amount of validation

Must be workload/risk dependent.

## Exact ideal subagent threshold

Must depend on task complexity and host overhead.

## Human cognitive-load scoring

Useful design concept but not directly measurable from Skill files.

---

# 31. Matt Pocock `writing-for-agents`: accepted usage

Use the following ideas as **Strong heuristics**:

* context pointers;
* progressive conditional disclosure;
* process predictability;
* awareness of context load;
* aggressive instruction pruning;
* information hierarchy as diagnostic;
* co-location as diagnostic;
* explicit completion criteria for multi-step workflows.

Use with qualification:

* leading words → Needs validation;
* router Skills → Situational;
* manual/model invocation mechanics → Platform-specific where relevant.

Do not import Claude-specific mechanics into the portable core.

Evidence:
[writing-for-agents](https://github.com/mattpocock/skills/blob/main/skills/productivity/writing-for-agents/SKILL.md)
[SKILL-MECHANICS.md](https://github.com/mattpocock/skills/blob/main/skills/productivity/writing-for-agents/SKILL-MECHANICS.md)

---

# 32. Recommended architecture for the future Skill Engineer/Reviewer

Start with:

```text
skill-engineer/
├── SKILL.md
│
├── references/
│   ├── review-rubric.md
│   ├── eval-spec.md
│   └── platform-extensions.md
│
├── scripts/
│   ├── inspect-skill
│   └── validate-evals
│
└── evals/
    ├── trigger.yaml
    ├── execution.yaml
    └── regressions.yaml
```

Add only when required:

```text
fixtures/
run-evals
adapters/
additional domain references
```

The future Skill must obey its own architecture rules:

* small operational core;
* conditional references;
* deterministic filesystem/static inspection;
* AI semantic judgement only where required;
* runtime evidence for behavioural claims.

---

# 33. Deterministic inspector contract

`inspect-skill` should produce structured facts only.

Example logical output:

```json
{
  "metadata": {},
  "files": [],
  "references": [],
  "scripts": [],
  "assets": [],
  "broken_references": [],
  "platform_extensions": [],
  "hardcoded_paths": [],
  "exact_duplicates": [],
  "metrics": {
    "skill_lines": 0,
    "skill_bytes": 0,
    "skill_token_estimate": 0
  },
  "evals": {}
}
```

It must not make semantic judgements such as:

```text
bad scope
poor context design
weak completion criteria
```

Those belong to AI/runtime review.

---

# 34. Portable eval runner architecture

If implemented, separate:

```text
portable eval case
        ↓
host adapter
        ↓
agent execution
        ↓
normalized trace/result
        ↓
graders
        ↓
comparison/report
```

Keep:

* case definitions;
* grading criteria;
* regression corpus;

independent of Claude/Codex/Cursor/Antigravity trace formats.

---

# 35. Production-quality acceptance criteria

A Skill may be considered production-quality only when all **applicable** requirements hold:

* [ ] Standard structure validates.
* [ ] Mechanism selection is appropriate.
* [ ] Scope is coherent.
* [ ] Trigger boundary is defined.
* [ ] Representative positive trigger tests pass.
* [ ] Representative negative/boundary trigger tests pass.
* [ ] Representative execution evals pass.
* [ ] Candidate is not materially worse than baseline unless the trade-off is explicit and accepted.
* [ ] Critical side effects are validated.
* [ ] Safety and permissions are understood.
* [ ] Required resources are reachable.
* [ ] Platform-specific dependencies are declared.
* [ ] Claimed portability is tested or clearly marked untested.
* [ ] Known historical failures are regression cases.
* [ ] No unresolved Critical findings remain.

Do not require optional mechanisms purely for completeness.

---

# IMPLEMENTATION CONTRACT

## Mandatory portable behaviour

Build one Skill with two modes:

```text
CREATE
REVIEW
```

Both modes must use one shared engineering rule set rather than duplicated creation/review rules.

The Skill must default to the open Agent Skills model and remain agent-agnostic unless a platform adapter is explicitly selected.

### Core workflow

The Skill must perform this sequence:

```text
understand requested mode and target
→ inspect target/context
→ select correct mechanism(s)
→ perform deterministic static analysis
→ perform semantic AI analysis
→ determine applicable review rules
→ design or inspect trigger behaviour
→ design or inspect execution behaviour
→ design or inspect eval coverage
→ compare against baseline/version where runtime is available
→ produce evidence-backed recommendations
```

### Required engineering dimensions

Implement rules covering:

1. mechanism selection;
2. scope/decomposition;
3. trigger metadata;
4. trigger precision/recall;
5. catalog competition where relevant;
6. progressive disclosure;
7. reference reachability;
8. branch isolation;
9. context filtering;
10. instruction necessity/procedural burden;
11. deterministic extraction opportunities;
12. proportional validation;
13. scripts;
14. tools/MCP;
15. deterministic enforcement/hooks;
16. subagents;
17. completion semantics;
18. failure/retry behaviour where applicable;
19. idempotency for mutating workflows;
20. safety/permissions;
21. untrusted resource security;
22. portability boundaries;
23. duplication/drift/source-of-truth;
24. maintainability;
25. regression preservation;
26. measured Skill utility.

Do not create separate duplicate rules for premature completion, retries or related sub-concepts where they belong under the parent dimension.

### Evidence classification

Every rule/finding must be tagged as one of:

```text
Universal
Strong heuristic
Platform-specific
Situational
Needs validation
```

Every finding must also have independent:

```text
Severity
Confidence
```

### Severity values

```text
Critical
High
Medium
Low
```

### Required finding schema

For each material review finding emit:

```text
Check
Finding
Evidence
Detection method
Severity
Confidence
Recommended action
Validation/eval
Automation type
Evidence class
Applicability
```

Use Good pattern / Failure pattern only when they improve clarity.

### Deterministic inspector

Implement a deterministic inspector that can, at minimum:

* parse `SKILL.md`;
* validate portable frontmatter/metadata;
* inventory Skill files;
* validate local references;
* calculate line/byte/token estimates;
* detect exact duplicated blocks;
* identify configured platform extensions;
* detect obvious hardcoded paths;
* inventory scripts/assets;
* locate configured evals;
* validate portable eval structure;
* detect missing referenced fixtures/resources.

It must output structured facts and must **not** make semantic quality judgements.

### AI-review responsibilities

Use model judgement for:

* mechanism choice;
* scope;
* semantic trigger boundary;
* pointer quality;
* branch decomposition;
* unnecessary/procedural instructions;
* deterministic extraction opportunity;
* context filtering opportunity;
* completion risk;
* subagent suitability;
* source-of-truth choice;
* maintainability;
* security intent;
* portability interpretation.

Every AI finding must cite concrete evidence from the inspected Skill.

### Eval model

Implement or define a platform-neutral eval format supporting:

```text
trigger evals
execution evals
regression evals
```

Required case categories:

```text
positive
negative
boundary
adversarial
regression
```

Support additionally where useful:

```text
paraphrase
near-neighbour
competing-skill
large-input
failure-injection
```

### Fixtures

Support:

```text
known-good fixtures
intentionally defective fixtures
```

Defective fixtures must identify the expected defect so the reviewer itself can be regression-tested.

### Grading

Support:

1. deterministic outcome/state graders;
2. deterministic process graders;
3. LLM judges;
4. human/manual grading metadata.

Prefer outcome/state grading over final-text grading whenever possible.

Do not enforce exact traces unless sequence is required for safety or correctness.

### Differential evaluation

Support comparison between:

```text
candidate vs previous accepted Skill
candidate vs no-Skill baseline
```

where execution infrastructure permits it.

Correctness must be evaluated before efficiency.

### Multiple trials

Allow configurable repeated trials.

Use multiple trials when routing or execution is probabilistic or comparison is close.

Record at minimum:

```text
trial count
pass count
pass rate
```

### Efficiency metrics

Capture when exposed by the host:

```text
input/context tokens
output tokens
duration
tool calls
commands
errors
retries
references loaded
subagents spawned
side-effect operations
```

Do not optimize efficiency at the expense of correctness without explicit trade-off.

### Regression behaviour

Automatically map changes to relevant eval suites:

```text
name/description change
→ trigger suites

workflow change
→ affected execution + regression suites

reference change
→ dependent cases

script change
→ script tests + dependent execution cases

platform adapter change
→ target-host tests

safety/permission change
→ adversarial/failure/side-effect cases
```

Always retain known failures as regression cases when reproducible.

### Eval failure classification

Distinguish:

```text
Skill failure
routing failure
model variance
tool failure
fixture failure
harness failure
environment failure
grader failure
```

Do not count infrastructure failures as Skill regressions without evidence.

### Context architecture

Keep `SKILL.md` operational and minimal.

Use references for conditional detail.

Every critical deferred reference must have a meaningful retrieval condition.

Do not load by default:

* full eval corpus;
* fixture contents;
* historical benchmark results;
* script implementations;
* unrelated platform adapters;
* irrelevant branch references;
* raw data that can be safely prefiltered.

### Scripts

Add scripts only when deterministic execution materially improves reliability, capability, context or cost.

Scripts used during normal execution should expose stable inputs/outputs and useful failure behaviour.

Review mode must be able to inspect script source when trust/security/correctness requires it.

### Subagents

Do not require subagents.

Recommend/use them only for bounded work where context isolation, specialization or parallelism justifies their overhead.

### Hooks and deterministic enforcement

Do not rely on model instructions for mandatory safety/security invariants when deterministic enforcement is available.

Portable core should describe the requirement; platform adapters may implement host-specific hooks/permissions.

### Portability

Portable core must not require proprietary host behaviour.

Platform-specific features must be isolated in optional adapters.

Track separately:

```text
standards-compatible
tested platforms
untested platforms
known behavioural deviations
```

### Platform adapters

Support optional guidance/adapters for:

```text
Claude Code
OpenAI Codex
Cursor
Google Antigravity
```

Adapters may contain host-specific:

* invocation controls;
* rules files;
* hooks;
* subagents;
* permission configuration;
* eval runners.

They must never become dependencies of the portable core.

### Claude Code `skill-creator`

Integrate only as optional supplemental tooling when available.

Do not make it:

* mandatory;
* canonical eval storage;
* the portable eval schema;
* the sole trigger evaluator.

### Create mode output

Produce:

```text
architecture/mechanism decision
trigger boundary
proposed minimal Skill structure
applicable engineering requirements
eval plan/cases
platform-specific adaptations if required
assumptions and unresolved validation needs
```

Do not create unnecessary files/mechanisms.

### Review mode output

Produce:

```text
executive verdict
Critical/High findings
Medium/Low findings
trigger assessment
execution assessment
context/procedure assessment
safety assessment
portability assessment
eval coverage/gaps
smallest recommended changes
regression cases to add
```

Do not generate a single arbitrary numeric quality score by default.

### Required behaviour principles

The implementation must actively avoid:

```text
instruction accumulation
checklist accumulation
unnecessary validation
unnecessary Skill splitting
platform leakage
eval theatre
verification theatre
exact-trace overfitting
```

When evidence is uncertain, classify the claim as **Needs validation** and propose the smallest eval capable of resolving it.

The governing optimization criterion is:

```text
maximize reliable task success
subject to acceptable safety, context, latency, tool cost and maintainability
```

—not maximizing the amount of guidance inside the Skill.
