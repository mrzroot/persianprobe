<!-- Paste into AGENTS.md, CLAUDE.md, .cursorrules or your agent's rules file. Requires `pipx install git+https://github.com/mrzroot/persianprobe` (or `uvx --from git+https://github.com/mrzroot/persianprobe persianprobe`). -->

## Persian (Farsi) text in code

Do not assume that `\d`, `\w`, `int()`, `parseInt()`, `len()`, `==`, `sort()` or `json.dumps()` handle Persian text the same way in every language: they do not. Before writing validation, search, sorting or parsing for Persian input, run:

```sh
persianprobe                      # the matrix for every runtime installed here
persianprobe --probes parse-int,digit-regex,sort-default
persianprobe xray "some pasted text" --fix   # look-alike / invisible characters in a string
```

- Normalize at the system boundary: Arabic ي ى ك to ی ک, Persian/Arabic digits to ASCII (or one chosen set), strip tatweel and bidi marks.
- Never compare, store or index un-normalized Persian text; never sort it with the default sort.
- `persianprobe` runs local interpreters only and sends nothing anywhere.
