# UD Turkic Tools

Shared tooling for the [UD Turkic group](https://github.com/ud-turkic): cross-language clustering, annotation strategy tables, and treebank discovery.

## Scripts

### `turkic_clustering.py`

Cross-language lemma clustering across all Turkic UD treebanks. Maps overarching concepts (e.g., "BOL" for copula) to language-specific lemmas and generates UPOS × deprel distributions.

```bash
# List all Turkic languages and treebanks
python turkic_clustering.py --list-languages

# Process all Turkic languages with lemma mapping
python turkic_clustering.py --lemma-mapping complete_lemma_mapping.json --output results.json
```

### `generate_annotation_tables.py`

Generate annotation strategy comparison tables from clustering results (e.g., how different treebanks annotate copulas).

### `generate_filtered_report.py`

Generate filtered reports from clustering results.

### `get_ud_repos_with_gh.py`

Discover all UD repositories and generate language-to-treebank mappings using GitHub CLI.

```bash
python get_ud_repos_with_gh.py --output ud_repos.json
```

## Data

- `complete_lemma_mapping.json` — Lemma mappings across Turkic languages
- `ud_languages.json` — Language-to-treebank mapping
- `Lemma mapping - lemma_mapping.csv` — Tabular lemma mapping

## See also

- [ud-tools](https://gitlab.com/furkan4829/tools/ud-tools) — General UD tooling (`udvalidate`, `udsearch`, `udeval`)
- [ud-turkic/parallel](https://github.com/ud-turkic/parallel) — Parallel treebank tools
