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

On three earnings briefs written by Haiku, Sonnet and Opus from the original (wrong) release, with
every number labelled by hand against the 10-Q (`agent_briefs/`, `agent_labels.py`):

| Checker | False caught (of 62) | True flagged (of 270) | True verified by key or formula |
|---|---|---|---|
| onus `main` | 27 | 44 | n/a |
| onus with the table-row fixes | 42 | 20 | n/a |
| graph, word overlap only | 45 | 54 | 22 |
| graph with tables and a claim's own arithmetic | **50** | 21 | **80** |
| graph with embeddings | 52 | 112 | 44 |

The last round of fixes was tuned on these same briefs, so the graph's row is optimistic. Labelled
claim sets: `cases.py` (67, tuned on), `cases2.py` (40, agent shorthand), `cases3.py` (40, held out
until the embedding test): 65/67, 39/40 and 33/40.

What it still gets wrong: adjusted figures computed from wrong inputs that happen to be right, shares
of a total whose inputs sit in another paragraph, a few bad keys ("share of revenue" to share-based
compensation), and non-GAAP figures the 10-Q does not hold.

## Running

From this folder:

```bash
python3 graph_check.py data/q2_2025_press_release_original_narrative_only.md
```

```bash
python3 score.py cases3
```

```bash
python3 score_agents.py
```

`score_agents.py` also scores another onus revision if `ONUS_BASELINE` points at its checkout, and the
embedding variant if `sentence-transformers` is installed.
