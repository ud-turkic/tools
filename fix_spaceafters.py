#!/usr/bin/env python3
"""
Script to automatically fill in missing SpaceAfter=No annotations in CoNLL-U treebank files
based on validation error logs.

Usage:
    python fix_space_after.py error_log.txt treebank.conllu

This script processes error logs from the UD validator that report missing SpaceAfter=No
annotations and updates the treebank file to add these annotations where necessary.
"""

import re
import sys
import os


def parse_error_log(error_log_path):
    """
    Parse the error log file to identify tokens that need SpaceAfter=No
    
    Returns a dictionary mapping sentence IDs to lists of node numbers that need the annotation
    """
    missing_space_after = {}
    
    # Regular expression to extract information from error logs
    pattern = r"\[Line (\d+) Sent ([^\]]+)\]: \[L2 Metadata missing-spaceafter\] 'SpaceAfter=No' is missing in the MISC field of node #%(\d+)"
    
    with open(error_log_path, 'r', encoding='utf-8') as f:
        for line in f:
            match = re.search(pattern, line)
            if match:
                line_num, sent_id, node_num = match.groups()
                if sent_id not in missing_space_after:
                    missing_space_after[sent_id] = []
                missing_space_after[sent_id].append(node_num)
    
    return missing_space_after


def update_treebank(treebank_path, missing_space_after, output_path=None):
    """
    Update the treebank file to add SpaceAfter=No annotations
    """
    if output_path is None:
        base, ext = os.path.splitext(treebank_path)
        output_path = f"{base}_fixed{ext}"
    
    current_sent_id = None
    updated_lines = []
    
    with open(treebank_path, 'r', encoding='utf-8') as f:
        for line in f:
            # Check for sentence ID
            sent_id_match = re.search(r"^# sent_id = (.+)$", line)
            if sent_id_match:
                current_sent_id = sent_id_match.group(1)
            
            # Check if this is a token line (not a comment)
            if line.strip() and not line.startswith('#'):
                fields = line.strip().split('\t')
                if len(fields) == 10:  # Ensure this is a valid CoNLL-U token line
                    token_id, form, lemma, upos, xpos, feats, head, deprel, deps, misc = fields
                    
                    # Check if this token needs SpaceAfter=No
                    if current_sent_id in missing_space_after and token_id in missing_space_after[current_sent_id]:
                        if misc == '_':
                            misc = 'SpaceAfter=No'
                        else:
                            # Only add SpaceAfter=No if it's not already there
                            if 'SpaceAfter=No' not in misc:
                                misc = f"{misc}|SpaceAfter=No"
                        
                        # Reconstruct the line with the updated MISC field
                        fields[9] = misc
                        line = '\t'.join(fields) + '\n'
            
            updated_lines.append(line)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.writelines(updated_lines)
    
    return output_path


def main():
    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} error_log.txt treebank.conllu [output.conllu]")
        sys.exit(1)
    
    error_log_path = sys.argv[1]
    treebank_path = sys.argv[2]
    output_path = sys.argv[3] if len(sys.argv) > 3 else None
    
    # Parse error log to identify tokens that need SpaceAfter=No
    missing_space_after = parse_error_log(error_log_path)
    
    # Update the treebank file
    fixed_path = update_treebank(treebank_path, missing_space_after, output_path)
    
    print(f"Fixed treebank written to {fixed_path}")


if __name__ == "__main__":
    main()