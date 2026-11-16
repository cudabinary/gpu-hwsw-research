# PAPER SCOUT and PAPER WRITER handoff

1. Check the index scope, hashes, and remote checkpoint in `RESEARCH_EVIDENCE_INDEX.json`.
2. Locate the shard by research name, role, or claim ID and identify the evidence ID. Use `UNKNOWN` where the experiment's source commit was never recorded.
3. Obtain an authorized B2 read key from the user or the secret store. B2 access is granted separately from GitHub access. Keep secrets out of chat, Git, command-line arguments, and logs.
4. Place `tools/restore_evidence.py`, `tools/independent_restore.py`, and `tools/restore_git_history.py` together. They use the Python standard library.
5. Restore the evidence IDs into a fresh directory and verify each full SHA-256. Review restored code before executing it.
6. Check the original environment, correctness contract, controls, repetitions, and measurement boundaries before citing a claim. Mark source inspection as pending when you lack remote read access.

Use a separate service key with read-only access restricted to the relevant bucket and prefix. Keep operational upload keys and the master key out of the service. Key expiration leaves stored objects and storage billing in place.
