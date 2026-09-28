# Contributing

Thanks for helping improve this framework. This is a documentation project —
there is no compiled code, no test suite to run, and no package to publish.

## Scope of contributions

**In scope:**

- Corrections to methodology, terminology, or classification rules
- Clarifications that reduce ambiguity or unsafe interpretation
- New domain guides and report templates
- Additional objective/method diversification where the gap is real
- Examples, checklists, and evidence schemas
- Typographic, structural, and navigation improvements

**Out of scope:**

- Real vulnerability reports against third-party targets
- Live credentials, tokens, API keys, or captured target data
- Exploit payloads intended for use against live systems
- Unattributed or scraped third-party content
- Marketing language, unsupported capability claims, or fabricated metrics
- Bulk restructuring that churns history without improving the reader

## Hard rules for any contribution

1. **Never fabricate.** No invented results, statistics, case studies,
   capabilities, or tool usage. If a technique was not performed, do not write
   as though it was.
2. **Preserve original content.** Fix errors; do not silently delete material
   you disagree with. If something should be removed, explain why in the pull
   request.
3. **Classify precisely.** Every technique and conclusion uses the taxonomy in
   [`docs/guides/DECISION-MATRIX.md`](docs/guides/DECISION-MATRIX.md).
4. **No secrets.** Never commit credentials, tokens, private keys, session
   data, or real target captures.
5. **Keep attribution.** Do not strip third-party credit or license notices.

## Making a change

1. **Branch** from `main`.

   ```bash
   git checkout -b your-branch-name
   ```

2. **Edit** the file in its new location under `docs/`, `examples/`, or
   `templates/`.

3. **Update cross-references** if you moved or renamed a file. Every relative
   link in the repository must still resolve.

4. **Update [`FILE-INDEX.txt`](FILE-INDEX.txt)** when you add, rename, or move a
   document. It is the authoritative index and must stay complete.

5. **Verify your links** before opening the PR:

   ```bash
   # find relative markdown links
   grep -rnoE '\]\(([^)#][^)]*)\)' --include='*.md' . | grep -v '^\./\.git'
   ```

6. **Open a pull request** describing:
   - what changed and why
   - whether any original content was removed, and the justification
   - which `FILE-INDEX.txt` entries you updated

## Style

- Sentence case for headings
- One concept per section; prefer short sections over long ones
- Use tables for classification matrices and decision rules
- Keep the ASCII box-drawing diagrams in the operational modes — they are
  deliberate and load-bearing
- Match the surrounding document's formatting rather than introducing a new
  style mid-repository

## Reporting a defect

Methodology errors can be reported as issues. Security-sensitive defects
should follow the reporting path in [`SECURITY.md`](SECURITY.md).

## License for contributions

Contributions are accepted under the [MIT License](LICENSE) that covers this
repository. By opening a pull request you confirm that you have the right to
license the contribution and that it contains no third-party material you are
not permitted to relicense.
