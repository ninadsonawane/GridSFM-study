# Official MATPOWER source snapshot (retrieved on demand)

Release: **8.1**. Annotated tag object: `3f8ecfdbc79b07697d6b45f8d868ac1c2d27f788`.
Actual source commit: **`1a828c7af590714499284e36ee9c81273388c594`**.

- [Immutable official case300.m](https://github.com/MATPOWER/matpower/blob/1a828c7af590714499284e36ee9c81273388c594/data/case300.m)
- SHA-256 of raw Git blob bytes: `69a90280e999ef533d94656e0fbc08311f1347c962dd2753ff2005ff5e3f9ac5`
- The source file was acquired and inspected locally. `case300.m` is intentionally not committed. It is small but its redistribution license is not established here. The [MATPOWER license](https://github.com/MATPOWER/matpower/blob/1a828c7af590714499284e36ee9c81273388c594/LICENSE) explicitly excludes case files from its BSD grant. The originating [UW archive policy](https://labs.ece.uw.edu/pstca/pg_tcaintro.htm) describes research/education use. Do not label this dataset BSD merely because MATPOWER software is BSD.
- `LICENSE` preserves the exact upstream notice, including its data exception. It does not grant extra rights to case data.

Retrieve the original from the pinned repository, without newline normalization:

```sh
git clone --branch 8.1 --depth 1 https://github.com/MATPOWER/matpower.git work/matpower-8.1
git -C work/matpower-8.1 rev-parse HEAD
# Must print 1a828c7af590714499284e36ee9c81273388c594
python scripts/python/matpower_case.py --git-dir work/matpower-8.1
python scripts/python/matpower_test.py
```

The acquisition script uses `git show <commit>:data/case300.m` as bytes. On Windows, checking the SHA of a CRLF-normalized working checkout can differ despite the same Git object. The acquisition refuses to overwrite a different snapshot. The case is an acquisition artifact; the committed audit and immutable retrieval information make it recoverable.
