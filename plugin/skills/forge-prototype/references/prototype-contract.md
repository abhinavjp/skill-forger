# Prototype behaviour contract

Load when building or changing a prototype.

1. Prototype only the journeys needed to answer the documented questions, with
   realistic synthetic data. Never copy production secrets, credentials,
   personal information, logs, or customer data.
2. Make relevant controls truly interactive, including error, cancel, recover,
   empty, and disabled states when material. A dead control is disabled with an
   explanation or listed as unimplemented.
3. Label simulated behaviour as distinct from real APIs, permissions,
   persistence, security, and performance. Never claim a property was validated
   because the UI simulates it.
4. Prefer a local static artifact (HTML, CSS, JavaScript) unless a framework is
   justified. No unnecessary dependencies, network calls, external scripts or
   CDNs, and no autonomous installs. Tell the user that linters or CI may scan
   runnable JavaScript under `.forge/`. A `README.md` in the folder may state
   how to launch it and what is simulated.
5. Keep it disposable and isolated. Never edit production source to make the
   prototype work.
6. If browser automation is available and authorised, click through the target
   journeys and capture evidence. If not, run what is available and record
   interaction and visual checks as `UNMEASURED` with reasons, and say what was
   not verified. No fabricated passes or screenshots.

These checks are ledger Observations. Forge defines no required check for a
prototype; the human decides.
