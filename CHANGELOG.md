# Changelog

## Unreleased

- A count in the 1950-2099 band is no longer forced to be a year: "2000 users"
  and "2048-bit keys" are counts, "in 2000" is still a year, and a number the
  text leaves open is checked as both (ONS001/ONS002).

- A range applies the symbol, scale or unit it states once to both of its
  ends: `$2-3M` is $2M and $3M, `18-24 months` two durations, `2-3%` two
  percentages. `$2-3M` used to read as two dollars, with the 3M dropped.

- A claim is checked at its own precision, not the looser of the two
  precisions: evidence reading "about 2 billion" no longer supports a claim of
  `$2.4B`, which the source never stated (ONS001).

## 0.1.0 - 2026-10-05

Initial alpha: deterministic number and date checks, model-judged claims with
verbatim quotes, document/transcript/directory evidence, ruff-style rule codes,
and a labelled eval. Default model: `anthropic:claude-sonnet-5-5`.
