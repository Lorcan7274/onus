# Fact graph (experiment)

A prototype of checking numbers as facts rather than as a bag of numbers, built on Beyond Meat's
Q2 2025 filings. It is not wired into `onus`; it imports `onus.numbers` and `onus.evidence` and runs on
its own.

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

Three sets of agent briefs written from the Q2 release, every number labelled by hand against the 10-Q
(`agent_briefs/setN/`, `labels_setN.py`). Sets 1 and 2 were used to develop the checker; set 3 was
written and labelled after the code was frozen and scored once.

Held-out set 3 (a credit recap and a bull/bear note from the original release, a deck from the corrected
one; 360 true numbers, 39 false):

| Checker | False caught (of 39) | True flagged (of 360) | True verified by key or formula |
|---|---|---|---|
| onus `main` | 12 | 59 | n/a |
| onus with the table-row fixes | 24 | 63 | n/a |
| graph, word overlap only | 25 | 103 | 46 |
| graph before structure parsing (`8d2d4bd`) | 26 | 76 | 78 |
| **graph with structure parsing and written arithmetic** | **29** | **61** | **95** |

What it still gets wrong: derived figures whose inputs sit in another sentence with no written formula
(ex-charges opex, free cash flow, shares of the decline), mix columns read against the wrong period, and
keys that land on the wrong fact ("$0.38/share" to share-based compensation, "$1.0M" to restricted cash).

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
