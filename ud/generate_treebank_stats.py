#!/usr/bin/env python3
"""
Generate statistics tables for UD Turkic treebanks.

Computes per-treebank stats (sentences, tokens, MWTs, word types, lemma types,
POS tags, deprels, features) and outputs LaTeX and/or Markdown tables matching
the format used in the UD Turkic survey paper appendix.

Usage:
    python ud/generate_treebank_stats.py --local-dir /tmp/ud-impact
    python ud/generate_treebank_stats.py --format latex --output stats.tex
    python ud/generate_treebank_stats.py --format both --local-dir /tmp/ud-impact
    python ud/generate_treebank_stats.py --format json --output stats.json
"""

import sys
import argparse
import json
from pathlib import Path
from collections import Counter

# Allow importing from repo root (for clustering.turkic_clustering)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from clustering.turkic_clustering import TURKIC_LANGUAGES, TURKIC_BRANCHES
from udsearch.conllu import parse_conllu


def load_treebank_local(treebank_dir: Path) -> list:
    """Load all CoNLL-U files from a local treebank directory."""
    sentences = []
    for f in sorted(treebank_dir.glob("*.conllu")):
        text = f.read_text(encoding="utf-8")
        sentences.extend(parse_conllu(text))
    return sentences


def load_treebank_auto(treebank_name: str, local_dir: Path | None = None) -> list:
    """Load a treebank from local dir or via udsearch download."""
    ud_name = f"UD_{treebank_name}" if not treebank_name.startswith("UD_") else treebank_name
    bare_name = treebank_name.removeprefix("UD_")

    if local_dir:
        tb_path = local_dir / ud_name
        if tb_path.is_dir():
            return load_treebank_local(tb_path)
        # Try without UD_ prefix
        tb_path = local_dir / bare_name
        if tb_path.is_dir():
            return load_treebank_local(tb_path)

    # Fall back to udsearch download
    from udsearch import load_treebank
    return load_treebank(bare_name, quiet=True)


def count_mwts(sentences: list) -> int:
    """Count multi-word tokens by inspecting raw lines for range IDs (e.g. 1-2)."""
    count = 0
    for sent in sentences:
        for line in sent._all_lines:
            if line.startswith("#"):
                continue
            fields = line.split("\t")
            if len(fields) >= 1 and "-" in fields[0]:
                count += 1
    return count


def compute_stats(sentences: list) -> dict:
    """Compute treebank statistics from a list of Sentence objects."""
    n_sentences = len(sentences)
    n_tokens = 0
    word_types = set()
    lemma_types = set()
    pos_tags = set()
    deprels = set()
    features = set()

    for sent in sentences:
        n_tokens += len(sent.tokens)
        for token in sent.tokens:
            if token.form and token.form != "_":
                word_types.add(token.form)
            if token.lemma and token.lemma != "_":
                lemma_types.add(token.lemma)
            if token.upos and token.upos != "_":
                pos_tags.add(token.upos)
            if token.deprel and token.deprel != "_":
                deprels.add(token.deprel)
            if token.feats:
                for feat_name in token.feats:
                    features.add(feat_name)

    n_mwts = count_mwts(sentences)

    return {
        "sentences": n_sentences,
        "tokens": n_tokens,
        "mwts": n_mwts,
        "word_types": len(word_types),
        "lemma_types": len(lemma_types),
        "pos_tags": len(pos_tags),
        "deprels": len(deprels),
        "features": len(features),
    }


def collect_all_stats(local_dir: Path | None = None) -> list[dict]:
    """Collect stats for all Turkic treebanks, ordered by branch and language."""
    results = []

    for branch, languages in TURKIC_BRANCHES.items():
        for language in languages:
            if language not in TURKIC_LANGUAGES:
                continue
            for treebank in TURKIC_LANGUAGES[language]:
                ud_name = treebank  # e.g. "UD_Turkish-BOUN"
                bare_name = treebank.removeprefix("UD_")
                # Display name: "Language/Treebank" e.g. "Turkish/BOUN"
                parts = bare_name.split("-", 1)
                display_name = f"{parts[0]}/{parts[1]}" if len(parts) == 2 else bare_name

                print(f"  Processing {treebank}...", file=sys.stderr)
                try:
                    sentences = load_treebank_auto(treebank, local_dir)
                    if not sentences:
                        print(f"    WARNING: no data for {treebank}", file=sys.stderr)
                        continue
                    stats = compute_stats(sentences)
                    stats["treebank"] = treebank
                    stats["display_name"] = display_name
                    stats["language"] = language
                    stats["branch"] = branch
                    results.append(stats)
                    print(
                        f"    {stats['sentences']} sent, {stats['tokens']} tok",
                        file=sys.stderr,
                    )
                except Exception as e:
                    print(f"    ERROR: {treebank}: {e}", file=sys.stderr)

    return results


def format_latex(results: list[dict], ud_version: str | None = None) -> str:
    """Format results as a LaTeX table matching the appendix format."""
    version_note = f" (as of UD version {ud_version})" if ud_version else ""

    lines = []
    lines.append(r"\begin{table*}[h]")
    lines.append(r"\centering")
    lines.append(r"\resizebox{\linewidth}{!}{%")
    lines.append(
        r"    \begin{tabular}{>{\raggedright\arraybackslash}p{8cm}*{8}{r}}"
    )
    lines.append(r"\toprule")
    lines.append(
        r"                    &   sent &  tok & multi & types & ltypes & pos & rel & feat \\"
    )
    lines.append(r"\midrule")

    for r in results:
        name = r["display_name"].replace("_", r"\_")
        lines.append(
            f"{name:<20s}"
            f"& {r['sentences']:>6d} "
            f"& {r['tokens']:>6d}"
            f"& {r['mwts']:>6d} "
            f"& {r['word_types']:>6d} "
            f"& {r['lemma_types']:>6d} "
            f"& {r['pos_tags']:>4d} "
            f"& {r['deprels']:>4d} "
            f"& {r['features']:>5d} \\\\"
        )

    lines.append(r"\bottomrule")
    lines.append(r"\end{tabular}}")
    lines.append(
        r"  \caption{Basic statistics on current UD Turkic treebanks"
        + version_note
        + "."
    )
    lines.append(r"  \emph{sent}: number of sentences,")
    lines.append(r"  \emph{tok}: number of tokens,")
    lines.append(r"  \emph{multi}: number of multi-word tokens,")
    lines.append(r"  \emph{types}: number of word types,")
    lines.append(r"  \emph{ltypes}: number of lemma types,")
    lines.append(r"  \emph{pos}: number of POS tags used,")
    lines.append(
        r"  \emph{rel}: number of dependency relations used (including language/treebank specific relations),"
    )
    lines.append(r"  \emph{feat}: number of morphological features used.")
    lines.append(r"  }\label{tbl:current-treebanks}")
    lines.append(r"\end{table*}")

    return "\n".join(lines)


def format_markdown(results: list[dict], ud_version: str | None = None) -> str:
    """Format results as a Markdown table."""
    version_note = f" (UD {ud_version})" if ud_version else ""

    lines = []
    lines.append(f"## UD Turkic Treebank Statistics{version_note}")
    lines.append("")
    lines.append(
        "| Treebank | Sent | Tok | MWT | Types | LTypes | POS | Rel | Feat |"
    )
    lines.append(
        "|:---------|-----:|----:|----:|------:|-------:|----:|----:|-----:|"
    )

    for r in results:
        lines.append(
            f"| {r['display_name']} "
            f"| {r['sentences']} "
            f"| {r['tokens']} "
            f"| {r['mwts']} "
            f"| {r['word_types']} "
            f"| {r['lemma_types']} "
            f"| {r['pos_tags']} "
            f"| {r['deprels']} "
            f"| {r['features']} |"
        )

    lines.append("")
    lines.append(
        "*sent*: sentences, *tok*: tokens, *MWT*: multi-word tokens, "
        "*types*: word types, *ltypes*: lemma types, *pos*: POS tags, "
        "*rel*: dependency relations, *feat*: morphological features."
    )

    return "\n".join(lines)


def format_json(results: list[dict]) -> str:
    """Format results as JSON."""
    return json.dumps(results, indent=2, ensure_ascii=False)


def main():
    parser = argparse.ArgumentParser(
        description="Generate UD Turkic treebank statistics table",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python ud/generate_treebank_stats.py --local-dir /tmp/ud-impact
  python ud/generate_treebank_stats.py --format latex --output stats.tex
  python ud/generate_treebank_stats.py --format both --local-dir /tmp/ud-impact
  python ud/generate_treebank_stats.py --format json --output stats.json
        """,
    )
    parser.add_argument(
        "--format",
        choices=["latex", "markdown", "both", "json"],
        default="both",
        help="Output format (default: both)",
    )
    parser.add_argument(
        "--output",
        "-o",
        help="Output file path (default: stdout)",
    )
    parser.add_argument(
        "--local-dir",
        type=Path,
        help="Local directory containing UD treebank repos (e.g., /tmp/ud-impact)",
    )
    parser.add_argument(
        "--ud-version",
        help="UD version string for the caption (e.g., 2.15)",
    )
    args = parser.parse_args()

    if args.local_dir and not args.local_dir.is_dir():
        print(f"Error: {args.local_dir} is not a directory", file=sys.stderr)
        sys.exit(1)

    print("Collecting treebank statistics...", file=sys.stderr)
    results = collect_all_stats(local_dir=args.local_dir)

    if not results:
        print("Error: no treebank data found", file=sys.stderr)
        sys.exit(1)

    print(f"Processed {len(results)} treebanks.", file=sys.stderr)

    # Build output
    parts = []
    if args.format in ("latex", "both"):
        parts.append(format_latex(results, args.ud_version))
    if args.format in ("markdown", "both"):
        parts.append(format_markdown(results, args.ud_version))
    if args.format == "json":
        parts.append(format_json(results))

    output = "\n\n".join(parts)

    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
        print(f"Written to {args.output}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
