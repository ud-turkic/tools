# UD Turkic Tools

Shared tooling for the [UD Turkic group](https://github.com/ud-turkic): cross-language clustering, annotation strategy tables, treebank discovery, and general UD utilities.

## clustering/

Cross-language lemma clustering across all Turkic UD treebanks. Maps overarching concepts (e.g., "BOL" for copula) to language-specific lemmas and generates UPOS × deprel distributions. See [docs/ud-query.md](docs/ud-query.md) for the query approach.

```bash
# List all Turkic languages and treebanks
python clustering/turkic_clustering.py --list-languages

# Process all Turkic languages with lemma mapping
python clustering/turkic_clustering.py --lemma-mapping clustering/data/complete_lemma_mapping.json --output results.json

# Generate annotation strategy tables from results
python clustering/generate_annotation_tables.py results.json

# Discover all UD Turkic repos via GitHub CLI
python clustering/get_ud_repos_with_gh.py --output ud_repos.json
```

**Data:**

- `clustering/data/complete_lemma_mapping.json` — lemma mappings across Turkic languages
- `clustering/data/ud_languages.json` — language-to-treebank mapping
- `clustering/data/lemma_mapping.csv` — tabular lemma mapping

## ud/

General UD utilities (not Turkic-specific), moved from [ud-turkic/parallel](https://github.com/ud-turkic/parallel).

- `compare_treebanks.py` — compare annotations between two CoNLL-U files with the same sentence IDs
- `count_tokens.py` — token/POS/feature statistics for CoNLL-U files
- `fix_spaceafters.py` — fill in missing `SpaceAfter=No` from UD validator error logs
- `generate_treebank_stats.py` — generate statistics tables (LaTeX/Markdown/JSON) for all UD Turkic treebanks

```bash
python ud/compare_treebanks.py treebank1.conllu treebank2.conllu
python ud/count_tokens.py corpus.conllu
python ud/fix_spaceafters.py error_log.txt treebank.conllu

# Generate treebank stats table from pre-cloned repos
python ud/generate_treebank_stats.py --local-dir /tmp/ud-impact --format both

# LaTeX only, with UD version in caption
python ud/generate_treebank_stats.py --local-dir /tmp/ud-impact --format latex --ud-version 2.15 --output stats.tex

# JSON output for downstream processing
python ud/generate_treebank_stats.py --format json --output stats.json
```

## See also

- [ud-tools](https://gitlab.com/furkan4829/tools/ud-tools) — general UD tooling (`udvalidate`, `udsearch`, `udeval`)
- [ud-turkic/parallel](https://github.com/ud-turkic/parallel) — parallel treebank tools
