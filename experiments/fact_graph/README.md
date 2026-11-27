# Fact graph (experiment)

A prototype layer that checks numbers as facts instead of looking for the same number anywhere in the
evidence. It runs on top of onus: it adds a flag only when it is certain a number is wrong, and clears an
onus flag when it verifies a number. Every other verdict is onus's. It isn't wired into `onus` yet; it
imports `onus.numbers` and `onus.evidence` and runs on its own.

## How it works

- **Facts.** `xbrl.py` reads a 10-Q's inline XBRL into facts: concept, period, segment, unit, sign and
  row label.
- **Keys.** `graph_check.py` gives each number in the document a metric, period and segment, taken from
  the words around it. Table cells take their metric from the row label and their period from the column
  header.
- **Verdicts.** A number is matched to a fact by key, or derived with one formula (share of revenue,
  change from an earlier period). It is wrong if its fact holds a different value, or if its sign or
  direction word disagrees. It is certain only when the claim's words pin one fact and nothing marks the
  number as adjusted, approximate or a change.
- **Embeddings (optional).** `emb_map.py` matches facts by meaning instead of words. It did worse, so
  it's off by default.

## Results

Agent briefs written from one quarterly release, every number labelled by hand against the 10-Q
(`agent_briefs/setN/`, `labels_setN.py`). Sets 1-4 were used during development; sets 5-7 were scored
once with frozen code.

| Set | onus: errors caught | onus: true flagged | + graph: errors caught | + graph: true flagged |
|---|---|---|---|---|
| 1 | 42 / 62 | 20 / 270 | 51 / 62 | 15 / 270 |
| 2 | 42 / 57 | 46 / 214 | 49 / 57 | 26 / 214 |
| 3 | 24 / 39 | 60 / 360 | 30 / 39 | 41 / 360 |
| 4 | 32 / 47 | 60 / 380 | 35 / 47 | 47 / 380 |
| 5 | 25 / 37 | 37 / 290 | 29 / 37 | 31 / 290 |
| 6 | 34 / 50 | 122 / 375 | 40 / 50 | 91 / 375 |
| 7 | 29 / 39 | 32 / 322 | 33 / 39 | 25 / 322 |

Most remaining false flags are onus's: figures derived from numbers in another sentence, which neither
layer can confirm yet.

## Limits

- Tuned to one filer: `SEGMENTS`, `ABBREV`, and the period end and comparison year.
- Needs inline XBRL, so it only works on SEC filings.

## Running

From this folder:

```bash
python3 graph_check.py data/q2_2025_press_release_original_narrative_only.md
```

```bash
python3 score_agents.py set3
```

Set `ONUS_BASELINE` to another onus checkout to score against it.
