#!/usr/bin/env python3
"""
A script to count tokens in CoNLL-U files.
"""

import argparse
from pathlib import Path
from collections import Counter, defaultdict
from udsearch import load_local_file

def count_tokens(conllu_file):
    """Count tokens in a CoNLL-U file with various statistics."""
    sentences = load_local_file(conllu_file)

    # Initialize counters
    stats = {
        'total_sentences': len(sentences),
        'total_tokens': 0,
        'pos_counts': Counter(),
        'feature_counts': defaultdict(Counter),
        'deprel_counts': Counter(),
        'tokens_per_sentence': []
    }

    # Collect statistics (udsearch already skips MWT range tokens)
    for sentence in sentences:
        token_count = len(sentence.tokens)
        stats['total_tokens'] += token_count
        stats['tokens_per_sentence'].append(token_count)

        for token in sentence.tokens:
                
            # Count POS tags
            if token.upos and token.upos != '_':
                stats['pos_counts'][token.upos] += 1

            # Count features
            if token.feats:
                for feat_name, feat_value in token.feats.items():
                    stats['feature_counts'][feat_name][feat_value] += 1

            # Count dependency relations
            if token.deprel and token.deprel != '_':
                stats['deprel_counts'][token.deprel] += 1
    
    return stats

def print_stats(stats, file_name):
    """Print statistics in a readable format."""
    print(f"\n=== Statistics for {file_name} ===")
    print(f"Total sentences: {stats['total_sentences']}")
    print(f"Total tokens: {stats['total_tokens']}")
    
    if stats['tokens_per_sentence']:
        avg_tokens = sum(stats['tokens_per_sentence']) / len(stats['tokens_per_sentence'])
        print(f"Average tokens per sentence: {avg_tokens:.2f}")
    
    print("\nPOS tag distribution:")
    for pos, count in stats['pos_counts'].most_common():
        percentage = (count / stats['total_tokens']) * 100
        print(f"  {pos}: {count} ({percentage:.2f}%)")
    
    print("\nTop 10 dependency relations:")
    for deprel, count in stats['deprel_counts'].most_common(10):
        percentage = (count / stats['total_tokens']) * 100
        print(f"  {deprel}: {count} ({percentage:.2f}%)")
    
    print("\nTop 5 features:")
    for i, (feat_name, values) in enumerate(sorted(
            stats['feature_counts'].items(),
            key=lambda x: sum(x[1].values()),
            reverse=True)[:5]):
        total = sum(values.values())
        percentage = (total / stats['total_tokens']) * 100
        print(f"  {feat_name}: {total} ({percentage:.2f}%)")
        for val, count in values.most_common(3):
            val_percentage = (count / total) * 100
            print(f"    {val}: {count} ({val_percentage:.2f}%)")

def main():
    parser = argparse.ArgumentParser(description="Count tokens in CoNLL-U files")
    parser.add_argument("files", nargs="+", help="CoNLL-U files to analyze")
    args = parser.parse_args()
    
    for file_path in args.files:
        path = Path(file_path)
        if not path.exists():
            print(f"Error: File {file_path} does not exist")
            continue
            
        try:
            stats = count_tokens(path)
            print_stats(stats, path.name)
        except Exception as e:
            print(f"Error processing {file_path}: {e}")

if __name__ == "__main__":
    main()