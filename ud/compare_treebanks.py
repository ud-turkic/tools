#!/usr/bin/env python3
"""
Treebank Comparison Tool

This script compares two CoNLL-U format treebanks with the same sentence IDs,
analyzing differences in annotations.

Usage:
    python treebank_compare.py treebank1.conllu treebank2.conllu
"""

import sys
import re
import collections
import argparse
from typing import Dict, List, Set, Tuple, Any


class ConlluFormatError(Exception):
    """Exception raised for errors in the CoNLL-U format"""
    pass


class Sentence:
    """Represents a sentence in CoNLL-U format"""

    def __init__(self, sent_id, text, lines):
        self.sent_id = sent_id
        self.text = text
        self.tokens = []

        for line in lines:
            if not line.strip() or line.startswith('#'):
                continue

            fields = line.strip().split('\t')
            if len(fields) != 10:
                raise ConlluFormatError(f"Expected 10 fields in CoNLL-U format, got {len(fields)} in sentence {sent_id}")

            # Token ID can be a number or a range (e.g., "1-2" for multiword tokens)
            token_id = fields[0]
            form = fields[1]
            lemma = fields[2]
            upos = fields[3]
            xpos = fields[4]
            feats = fields[5]
            head = fields[6]
            deprel = fields[7]
            deps = fields[8]
            misc = fields[9]

            # Store the token
            self.tokens.append({
                'id': token_id,
                'form': form,
                'lemma': lemma,
                'upos': upos,
                'xpos': xpos,
                'feats': feats,
                'head': head,
                'deprel': deprel,
                'deps': deps,
                'misc': misc
            })


def parse_conllu(filename: str) -> Dict[str, Sentence]:
    """
    Parse a CoNLL-U file and return a dictionary of sentences indexed by sent_id.

    Args:
        filename: Path to the CoNLL-U file

    Returns:
        Dictionary of Sentence objects indexed by sentence ID

    Raises:
        ConlluFormatError: If the file is not in valid CoNLL-U format
    """
    sentences = {}
    current_lines = []
    current_sent_id = None
    current_text = None

    sent_id_pattern = re.compile(r'# sent_id\s*=\s*(.+)')
    text_pattern = re.compile(r'# text\s*=\s*(.+)')

    try:
        with open(filename, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.rstrip('\n')

                # Empty line marks the end of a sentence
                if not line.strip():
                    if current_sent_id and current_lines:
                        sentences[current_sent_id] = Sentence(current_sent_id, current_text, current_lines)
                        current_lines = []
                        current_sent_id = None
                        current_text = None
                    continue

                # Comment lines starting with '#'
                if line.startswith('#'):
                    # Extract sent_id
                    sent_id_match = sent_id_pattern.match(line)
                    if sent_id_match:
                        current_sent_id = sent_id_match.group(1)

                    # Extract text
                    text_match = text_pattern.match(line)
                    if text_match:
                        current_text = text_match.group(1)
                else:
                    # It's a token line
                    if not current_sent_id:
                        raise ConlluFormatError(f"Line {line_num}: Token line appears before 'sent_id' is defined")
                    current_lines.append(line)

            # Don't forget the last sentence if the file doesn't end with an empty line
            if current_sent_id and current_lines:
                sentences[current_sent_id] = Sentence(current_sent_id, current_text, current_lines)

    except FileNotFoundError:
        print(f"Error: File '{filename}' not found")
        sys.exit(1)

    return sentences


def compare_treebanks(treebank1: Dict[str, Sentence], treebank2: Dict[str, Sentence]) -> Dict[str, Any]:
    """
    Compare two treebanks and return detailed analysis of differences.

    Args:
        treebank1: First treebank (dictionary of sentences)
        treebank2: Second treebank (dictionary of sentences)

    Returns:
        Dictionary with comparison results
    """
    results = {
        'sentences_only_in_tb1': [],
        'sentences_only_in_tb2': [],
        'common_sentences': [],
        'diff_counts': {
            'id': 0,
            'form': 0,
            'lemma': 0,
            'upos': 0,
            'xpos': 0,
            'feats': 0,
            'head': 0,
            'deprel': 0,
            'deps': 0,
            'misc': 0,
            'combination': collections.defaultdict(int)
        },
        'sentence_diffs': {}
    }

    # Find sentences only in treebank1
    results['sentences_only_in_tb1'] = [sent_id for sent_id in treebank1 if sent_id not in treebank2]

    # Find sentences only in treebank2
    results['sentences_only_in_tb2'] = [sent_id for sent_id in treebank2 if sent_id not in treebank1]

    # Find common sentences
    common_sent_ids = set(treebank1.keys()) & set(treebank2.keys())
    results['common_sentences'] = list(common_sent_ids)

    # Compare annotations for common sentences
    for sent_id in common_sent_ids:
        sent1 = treebank1[sent_id]
        sent2 = treebank2[sent_id]

        # Skip if different number of tokens
        if len(sent1.tokens) != len(sent2.tokens):
            results['sentence_diffs'][sent_id] = {
                'error': f"Different number of tokens: {len(sent1.tokens)} vs {len(sent2.tokens)}"
            }
            continue

        # Compare each token's annotations
        sent_diffs = {
            'id': [],
            'form': [],
            'lemma': [],
            'upos': [],
            'xpos': [],
            'feats': [],
            'head': [],
            'deprel': [],
            'deps': [],
            'misc': [],
            'diff_combinations': collections.defaultdict(list)
        }

        has_diff = False

        for i, (token1, token2) in enumerate(zip(sent1.tokens, sent2.tokens)):
            token_id = token1['id']
            diff_fields = set()

            # Check all 10 CoNLL-U fields
            if token1['id'] != token2['id']:
                sent_diffs['id'].append((token_id, token1['id'], token2['id']))
                diff_fields.add('id')
                results['diff_counts']['id'] += 1
                has_diff = True

            if token1['form'] != token2['form']:
                print(token1['form'], token2['form'], sent_id)
                sent_diffs['form'].append((token_id, token1['form'], token2['form']))
                diff_fields.add('form')
                results['diff_counts']['form'] += 1
                has_diff = True

            if token1['lemma'] != token2['lemma']:
                sent_diffs['lemma'].append((token_id, token1['lemma'], token2['lemma']))
                diff_fields.add('lemma')
                results['diff_counts']['lemma'] += 1
                has_diff = True

            if token1['upos'] != token2['upos']:
                sent_diffs['upos'].append((token_id, token1['upos'], token2['upos']))
                diff_fields.add('upos')
                results['diff_counts']['upos'] += 1
                has_diff = True

            if token1['xpos'] != token2['xpos']:
                sent_diffs['xpos'].append((token_id, token1['xpos'], token2['xpos']))
                diff_fields.add('xpos')
                results['diff_counts']['xpos'] += 1
                has_diff = True

            if token1['feats'] != token2['feats']:
                sent_diffs['feats'].append((token_id, token1['feats'], token2['feats']))
                diff_fields.add('feats')
                results['diff_counts']['feats'] += 1
                has_diff = True

            if token1['head'] != token2['head']:
                sent_diffs['head'].append((token_id, token1['head'], token2['head']))
                diff_fields.add('head')
                results['diff_counts']['head'] += 1
                has_diff = True

            if token1['deprel'] != token2['deprel']:
                sent_diffs['deprel'].append((token_id, token1['deprel'], token2['deprel']))
                diff_fields.add('deprel')
                results['diff_counts']['deprel'] += 1
                has_diff = True

            if token1['deps'] != token2['deps']:
                sent_diffs['deps'].append((token_id, token1['deps'], token2['deps']))
                diff_fields.add('deps')
                results['diff_counts']['deps'] += 1
                has_diff = True

            if token1['misc'] != token2['misc']:
                sent_diffs['misc'].append((token_id, token1['misc'], token2['misc']))
                diff_fields.add('misc')
                results['diff_counts']['misc'] += 1
                has_diff = True

            # Record combination of differences
            if diff_fields:
                diff_key = '+'.join(sorted(diff_fields))
                sent_diffs['diff_combinations'][diff_key].append(token_id)
                results['diff_counts']['combination'][diff_key] += 1

        if has_diff:
            results['sentence_diffs'][sent_id] = sent_diffs

    return results


def generate_report(results: Dict[str, Any]) -> str:
    """Generate a concise report showing which fields changed across all sentences"""
    report = []

    report.append("# Treebank Comparison Report")
    report.append("")

    # Summary
    report.append("## Summary")
    report.append(f"- Sentences only in first treebank: {len(results['sentences_only_in_tb1'])}")
    report.append(f"- Sentences only in second treebank: {len(results['sentences_only_in_tb2'])}")
    report.append(f"- Common sentences: {len(results['common_sentences'])}")
    report.append(f"- Sentences with differences: {len(results['sentence_diffs'])}")
    report.append("")

    # List sentences only in first treebank
    if results['sentences_only_in_tb1']:
        report.append("## Sentences only in first treebank")
        for sent_id in sorted(results['sentences_only_in_tb1']):
            report.append(f"- {sent_id}")
        report.append("")

    # List sentences only in second treebank
    if results['sentences_only_in_tb2']:
        report.append("## Sentences only in second treebank")
        for sent_id in sorted(results['sentences_only_in_tb2']):
            report.append(f"- {sent_id}")
        report.append("")

    # List all changed sentences
    changed_sents = list(results['sentence_diffs'].keys())
    if changed_sents:
        report.append("## Changed Sentences")
        for sent_id in sorted(changed_sents):
            if 'error' in results['sentence_diffs'][sent_id]:
                report.append(f"- {sent_id}: ERROR - {results['sentence_diffs'][sent_id]['error']}")
            else:
                report.append(f"- {sent_id}")
        report.append("")

    # List all unchanged sentences
    unchanged_sents = set(results['common_sentences']) - set(results['sentence_diffs'].keys())
    if unchanged_sents:
        report.append("## Unchanged Sentences")
        for sent_id in sorted(unchanged_sents):
            report.append(f"- {sent_id}")
        report.append("")

    # Overall field change summary
    report.append("## Field Change Summary")

    # Count how many sentences had each field changed
    field_changes = {
        'id': 0,
        'form': 0,
        'lemma': 0,
        'upos': 0,
        'xpos': 0,
        'feats': 0,
        'head': 0,
        'deprel': 0,
        'deps': 0,
        'misc': 0
    }

    for sent_id, diffs in results['sentence_diffs'].items():
        if 'error' in diffs:
            continue

        for field in field_changes.keys():
            if diffs[field]:
                field_changes[field] += 1

    # Report on each field
    for field, count in field_changes.items():
        field_upper = field.upper()
        total_changed_sents = len([s for s in results['sentence_diffs'].keys() if 'error' not in results['sentence_diffs'][s]])
        if total_changed_sents > 0:
            percentage = (count / total_changed_sents) * 100
            report.append(f"- {field_upper}: Changed in {count} sentences ({percentage:.1f}% of changed sentences)")
        else:
            report.append(f"- {field_upper}: No changes")

    report.append("")

    # Field change combinations summary
    combinations = results['diff_counts']['combination']
    if combinations:
        report.append("## Field Change Patterns")

        # Sort by frequency
        for combo, count in sorted(combinations.items(), key=lambda x: x[1], reverse=True):
            report.append(f"- {combo}: {count} instances")

        report.append("")

    # Special patterns - list sentences where specific patterns occur
    report.append("## Special Patterns")

    # Define patterns to check
    patterns = [
        ('FEATS changed but DEPREL unchanged', lambda diffs: diffs['feats'] and not diffs['deprel']),
        ('HEAD changed but DEPREL unchanged', lambda diffs: diffs['head'] and not diffs['deprel']),
        ('UPOS changed but FEATS unchanged', lambda diffs: diffs['upos'] and not diffs['feats']),
        ('LEMMA changed but UPOS unchanged', lambda diffs: diffs['lemma'] and not diffs['upos']),
        ('XPOS changed but UPOS unchanged', lambda diffs: diffs['xpos'] and not diffs['upos']),
        ('HEAD changed but DEPS unchanged', lambda diffs: diffs['head'] and not diffs['deps']),
        ('MISC changed only', lambda diffs: diffs['misc'] and
                                          not any(diffs[f] for f in ['id', 'form', 'lemma', 'upos', 'xpos', 'feats', 'head', 'deprel', 'deps']))
    ]

    for pattern_name, pattern_func in patterns:
        matching_sents = []

        for sent_id, diffs in results['sentence_diffs'].items():
            if 'error' in diffs:
                continue

            if pattern_func(diffs):
                matching_sents.append(sent_id)

        if matching_sents:
            report.append(f"### {pattern_name}")
            for sent_id in sorted(matching_sents):
                report.append(f"- {sent_id}")
            report.append("")

    return '\n'.join(report)


def main():
    parser = argparse.ArgumentParser(description='Compare two CoNLL-U format treebanks')
    parser.add_argument('file1', help='First treebank file')
    parser.add_argument('file2', help='Second treebank file')
    parser.add_argument('--output', '-o', help='Output file (default: stdout)')
    parser.add_argument('--concise', '-c', action='store_true',
                       help='Generate concise output (only changed sent_ids and fields)')
    args = parser.parse_args()

    try:
        print(f"Parsing first treebank: {args.file1}")
        treebank1 = parse_conllu(args.file1)
        print(f"Found {len(treebank1)} sentences in first treebank")

        print(f"Parsing second treebank: {args.file2}")
        treebank2 = parse_conllu(args.file2)
        print(f"Found {len(treebank2)} sentences in second treebank")

        print("Comparing treebanks...")
        results = compare_treebanks(treebank1, treebank2)

        print("Generating report...")
        report = generate_report(results)

        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(report)
            print(f"Report written to {args.output}")
        else:
            print("\n" + report)

    except ConlluFormatError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()