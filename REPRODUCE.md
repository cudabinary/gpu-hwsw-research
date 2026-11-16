# Reproduction and recovery

1. Open this worktree in WSL.
2. Run `python3 tools/verify.py`. It uses g++ to build and test the CPU API, three shared modules, and MAIN client. Each run writes raw logs to a new `results/run_*` directory. The initial compile error involving the `n` field is retained in the historical results and precedes the successful run.
3. Run `python3 tools/static_cuda.py` for a static build of the preserved CUDA kernels and native owner with nvcc 13.3 and MinGW. This step does not launch GPU work. Each run writes a separate `static_cuda_*` log directory. The initial host compiler error from a missing CUDA include path precedes the corrected build.
4. Use `git worktree list`, `git status`, and `git log -1` to inspect the branch and checkpoint. Compare remote SHAs with `git ls-remote origin refs/heads/main refs/heads/research/rcc`.

The local recovery archive was stored at `../checkpoint/PRE_SPLIT_RESEARCH.zip` in the original layout. It contains 10,270 files and is 1,350,781,528 bytes. The ZIP passed its CRC check and has SHA-256 `e043c998b3cf106c4edec2430617509ded8e7d785d71dbfe11debc6837d708bd`. The accompanying `MANIFEST.json` lists paths, sizes, and hashes. GitHub carries a smaller subset because the archive includes large historical traces. The archive contains research source, raw data, and logs and excludes the Library transfer helper.

The earlier results ZIP was stored at `../../deliverables/TCSC_RCC_RIE_CONSUMER_CPU_GPU_PILOT_20261021.zip` in the original layout, with SHA-256 `08a280c02d0cad82189e8ef1c925040df69ad4aabb2a33dd178c95efaee2631a` and Library ID `libfile_5c29472f6c10819182f6d87d202621ae`. The original ZIP was preserved.

If a Git bundle is available, run `git clone research.bundle restored` to restore versioned code and evidence. From the restored repository, run `git worktree add ../rcc research/rcc` to create the RCC worktree. The bundle omits the large local checkpoint. GitHub carries source, pinned inputs, selected raw CPU and GPU logs, and regression results. Large traces, executables, tokens, and private keys are excluded.
