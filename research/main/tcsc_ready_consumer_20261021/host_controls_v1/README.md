# Host controls v1: implementation and targeted CPU/static result

The two proposed controls are implemented in a separate version. The generated
owner differs from its frozen parent by 47 added/deleted diff lines, plus the
shared host helper and targeted tests. No kernel, CUDA ABI, builder, original
source/result or RCC interface was changed. This is baseline completion, not
a new algorithm or a claim of preparation benefit.

| Mode | Traversal | Stop conditions after initialization | Degree statistics |
|---|---|---|---|
| 0 | Push | EARLY_N | No |
| 6 | Push | EARLY_N | Yes |
| 7, new | Push | EARLY_N, static B(source) | No |
| 8, new | Push | EARLY_N, frontier-zero, static B(source) | Yes |
| 4 | Direction | EARLY_N, frontier-zero | Yes |
| 5 | Direction | EARLY_N, frontier-zero, RIE | Yes |

Modes6/8 do not build bitmaps or execute shadow Direction transitions. They are
not full policy-cost-matched controls. Mode8 matches mode5's logical stopping
boundary and statistics, while mode7 supplies the leaner static certificate.
Switching/bitmap overhead remains part of Direction's measured consumer cost.

The source, reverse, distance initialization, device allocation, query event
handling, per-level synchronization/safety checks, full D2H, owned immutable
result and q-prefix timing boundaries retain the frozen owner's structure.
All modes compute the same static metadata once in owner setup, outside the
ready query batch. `static_bound_setup_ms` is a subset of setup time, not an
extra term to add twice. This CPU scan is not a GPU conversion measurement.
The metadata occupies 48 host bytes plus an eight-byte setup-time field on this
build; it adds no device allocation. No per-vertex bound table is introduced.

`remaining_in_known` is false for modes0/7: their placeholder remaining value
must not be read as a measured zero. `visit_bound` records the query's bound;
reason5 identifies a static-bound stop, distinct from RIE reason2. EARLY_N is
checked first, then frontier-zero, then the applicable certificate. Init-only
cancellation still returns before any certificate/output publication.

## Exact scope of the static identity

For a single in-range source on an immutable finite directed CSR, with unit-hop
BFS and a distinct reached count including the source, let K count all graph
vertices of positive indegree. With exact complete reverse/COUNT degrees for
the same graph identity/version, `remaining_in==0` iff
`seen==B(source)=K+[indegree(source)==0]` at completed BFS frontier boundaries.
All reached non-source vertices have positive indegree. No assumption of full
reachability or strong connectivity is needed. Duplicates and self-loops are
allowed. This bound can remain loose on unreachable positive-indegree components.

The helper binds graph/reverse identity, n, m and version. Missing/stale bound
metadata falls back to EARLY_N for the certificate. A mismatched actual reverse
is still rejected by the existing owner; this is not permission to consume it.
Structural row checks do not prove that degrees correspond to CSR edges. The
unchanged builder's completed reverse is a prerequisite. Mutation without a
version change, forged/partial degrees, nonunique seen counts, an omitted source
exception, and applying the single-source formula to multiple seeds are outside
the guarantee. Targeted counterexamples demonstrate the unsafe variations.

## Completed validation

* Existing-tool MinGW C++17 static host compile/link: PASS, one attempt.
* Targeted actual replay/shared-helper comparison: 32 complete CPU arrays over
  eight small cases, PASS; eight equal-stop checks and16 identity boundaries.
* Fourteen negative/boundary checks, including deliberately wrong variants:
  PASS. Deliberate wrong outputs are counterexample witnesses, not accepted results.
* One fresh-permit rejection before driver initialization: PASS; three CPU
  reference/replay arrays precede that rejection. Driver loaded=false, launches=0.
* Earlier 402-array suite, sanitizers, GPU queries/execution: not run.

The host runtime code is compiled, not an empty-main stub. An additional
version-specific gate before `native::init` is unset; existing native approval,
PID handshake and safety guards remain required. There is no new dispatcher,
baseline capture or automatic resumption. GPU correctness/performance remain
UNMEASURED. Binary and all unchanged kernel/ABI hashes are in config/PINS.json.

The sole remaining GPU question is whether ready Direction beats both mode7
and mode8 at the same full-distance owned-return boundary. config/COMPARISON.json
is a frozen draft, dispatch_ready=false. No preparation/HW claim follows from
a consumer win alone.
