# Changelog

## Unreleased

- A claim is checked at its own precision, not the looser of the two
  precisions: evidence reading "about 2 billion" no longer supports a claim of
  `$2.4B`, which the source never stated (ONS001).

## 0.1.0 - 2026-10-05

Initial alpha: deterministic number and date checks, model-judged claims with
verbatim quotes, document/transcript/directory evidence, ruff-style rule codes,
and a labelled eval. Default model: `anthropic:claude-sonnet-5-5`.
