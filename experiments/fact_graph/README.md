# Fact graph (experiment)

A prototype second verification layer for onus: it checks numbers as facts rather than as a bag of
numbers, built on Beyond Meat's Q2 2025 filings. It does not replace onus's checks. Layered on top, it
flags a number whose fact contradicts it and clears an onus flag on a number it verifies by key or
formula; every other verdict is onus's own. It is not wired into `onus` yet; it imports `onus.numbers`
and `onus.evidence` and runs on its own.

## How it works

- **Evidence facts.** `xbrl.py` reads the 10-Q's inline XBRL (`data/q2_2025_10q.htm`): 1,046 facts,
  each with its concept, period, segment members, unit, sign and the table row label beside it.
- **Claim keys.** `graph_check.py` gives each number in a document a key from code: its period (from
  the document, "compared to", "first half", carried through a paragraph), its metric (the words
  around it matched against fact labels, finance abbreviations written out) and its segment.
- **Verdicts.** A number is *matched* by key, else *derived* along one formula (share of revenue,
  percentage change, difference), else checked against the claim's own other numbers (sums,
  differences, ratios), else held to presence in the filing's text as *weak*. A number its key
  contradicts is *wrong*; one with no key and no presence is *unsupported*.
- **Tables.** Each cell is read by its row label (metric) and column header (period); a "Change"
  column is recomputed from the facts, a "($M)" header scales bare cells.
- **Embeddings (optional).** `emb_map.py` ranks facts by meaning with a sentence-transformers model
  (`MODE=embed`); it did worse than word overlap on agent output and is off by default.

## Results

Agent briefs written from the Q2 release, every number labelled by hand against the 10-Q
(`agent_briefs/setN/`, `labels_setN.py`). Sets 1 and 2 were used to develop the checker; set 3 was
written and labelled after the code was frozen and scored once. The measure is onus with the layer
against onus alone.

| Set | Checker | False caught | True flagged |
|---|---|---|---|
| 1 | onus | 42 / 62 | 20 / 270 |
| 1 | onus + graph layer | 52 / 62 | 18 / 270 |
| 2 | onus | 42 / 57 | 45 / 214 |
| 2 | onus + graph layer | 49 / 57 | 27 / 214 |
| 3 (held out) | onus | 24 / 39 | 63 / 360 |
| 3 (held out) | onus + graph layer | 30 / 39 | 58 / 360 |
| 4 (held out, rule frozen first) | onus | 32 / 47 | 63 / 380 |
| 4 (held out, rule frozen first) | onus + graph layer | 36 / 47 | 63 / 380 |
| 5 (held out, certainty rule frozen first) | onus | 25 / 37 | 36 / 290 |
| 5 (held out, certainty rule frozen first) | onus + graph layer | 27 / 37 | 31 / 290 |
| 6 (held out, same frozen code) | onus | 33 / 50 | 130 / 375 |
| 6 (held out, same frozen code) | onus + graph layer | 38 / 50 | 99 / 375 |
| 7 (held out, after the margin fixes) | onus | 29 / 39 | 32 / 322 |
| 7 (held out, after the margin fixes) | onus + graph layer | 32 / 39 | 29 / 322 |

The layering rule was written after set 3 was scored, so set 3 is not a clean test of it; set 4 is. On
set 4 the layer (then adding every "wrong") caught 4 more errors but added 12 false flags of its own, all
from keys that landed on the wrong fact or period, cancelling the 12 it cleared. So the layer now adds a
flag only when its key is certain: the fact explains every word of the claim's metric, nothing marks the
number as adjusted or as a change, and no other period, segment or date of the same concept holds the
claimed value. Rows 1-4 above use the earlier rule; on set 5, scored once after that change, the layer
catches 2 more errors, loses none, clears 6 false flags and adds 1; on set 6 it catches 5 more, loses
none, clears 32 and adds 1. An audit then found a true margin (-46.5%, the 10-Q's own figure) flagged
with certainty through the lease discount rate, so a margin's subject must now be money and a fitting
filing table cell that states the claimed value blocks certainty; on set 7, scored once after that, the
layer catches 3 more errors, loses none, clears 6 false flags and adds 3. Most remaining false flags are onus's own: derived figures whose inputs sit in another
sentence with no written formula, which neither layer can confirm yet.

## Running

From this folder:

```bash
python3 graph_check.py data/q2_2025_press_release_original_narrative_only.md
```

```bash
python3 score.py cases3
```

```bash
python3 score_agents.py set3
```

`score_agents.py` also scores another onus revision if `ONUS_BASELINE` points at its checkout, and the
embedding variant if `sentence-transformers` is installed.
