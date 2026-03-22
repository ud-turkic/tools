#!/usr/bin/env python3
"""
Generate annotation strategy tables for BOL and ER from Turkic clustering results.
Creates tables showing which treebanks use which annotation strategies.
"""

import json
import sys
from pathlib import Path

def load_results(results_file):
    """Load the clustering results JSON file."""
    with open(results_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_top_strategies(combined_clusters, min_count=1):
    """
    Get the top annotation strategies from combined clusters.
    Returns list of (upos, deprel) tuples ordered by frequency.
    """
    strategies = []
    for cluster_str, count in combined_clusters.items():
        if count >= min_count:
            # Parse "(UPOS, deprel)" format
            cluster_clean = cluster_str.strip('()')
            if ', ' in cluster_clean:
                upos, deprel = cluster_clean.split(', ', 1)
                strategies.append((upos, deprel, count))
    
    # Sort by count (descending)
    strategies.sort(key=lambda x: x[2], reverse=True)
    return strategies

def has_strategy(strategies, target_upos, target_deprel):
    """Check if a specific UPOS-deprel strategy exists in the list."""
    for upos, deprel, count in strategies:
        if upos == target_upos and deprel == target_deprel:
            return True
    return False

def format_other_strategies(strategies, exclude_strategies):
    """Format the 'Other' column, excluding main strategies."""
    other = []
    for upos, deprel, count in strategies:
        strategy = f"{upos} - {deprel}"
        if strategy not in exclude_strategies:
            other.append(strategy)
    
    # Limit to top 10 to avoid overly long lists
    return other[:10]

def generate_table(results, lemma_type, target_strategies):
    """
    Generate a table for a specific lemma type (BOL or ER).
    
    Args:
        results: Complete clustering results
        lemma_type: "BOL" or "ER"
        target_strategies: List of (column_name, upos, deprel) tuples for main columns
    """
    if lemma_type not in results:
        print(f"No results found for {lemma_type}")
        return
    
    # Create header
    header = ["Treebank"]
    for col_name, _, _ in target_strategies:
        header.append(col_name)
    header.append("Other")
    
    # Create table rows
    rows = []
    
    # Process each language
    for language, lang_data in results[lemma_type]['languages'].items():
        for treebank_name, treebank_data in lang_data.get('treebanks', {}).items():
            if 'error' in treebank_data or treebank_data.get('total_matches', 0) == 0:
                continue
            
            # Get strategies for this treebank
            combined_clusters = treebank_data.get('combined_clusters', {})
            strategies = get_top_strategies(combined_clusters)
            
            # Build row
            row = [treebank_name.replace('UD_', '').replace('_', '-')]
            
            # Check each target strategy
            for col_name, target_upos, target_deprel in target_strategies:
                if has_strategy(strategies, target_upos, target_deprel):
                    row.append("✔")
                else:
                    row.append("✘")
            
            # Get other strategies
            exclude_list = [f"{upos} - {deprel}" for _, upos, deprel in target_strategies]
            other_strategies = format_other_strategies(strategies, exclude_list)
            
            if other_strategies:
                row.append("\n".join(other_strategies))
            else:
                row.append("✘")
            
            rows.append(row)
    
    # Sort rows by treebank name (first column)
    rows.sort(key=lambda x: x[0])
    
    return header, rows

def print_table(header, rows, title):
    """Print a formatted table."""
    print(f"\n{title}")
    print("=" * len(title))
    
    # Calculate column widths
    all_rows = [header] + rows
    col_widths = []
    for i in range(len(header)):
        max_width = max(len(str(row[i]).replace('\n', ' / ')) for row in all_rows)
        col_widths.append(min(max_width, 50))  # Cap at 50 chars
    
    # Print header
    header_line = " | ".join(h.ljust(col_widths[i]) for i, h in enumerate(header))
    print(header_line)
    print("-" * len(header_line))
    
    # Print rows
    for row in rows:
        # Handle multi-line cells
        formatted_row = []
        for i, cell in enumerate(row):
            cell_str = str(cell).replace('\n', ' / ')
            if len(cell_str) > col_widths[i]:
                cell_str = cell_str[:col_widths[i]-3] + "..."
            formatted_row.append(cell_str.ljust(col_widths[i]))
        
        print(" | ".join(formatted_row))

def generate_tsv_table(header, rows, filename):
    """Generate a TSV table for easier pasting into Google Docs."""
    with open(filename, 'w', encoding='utf-8') as f:
        # Write header
        f.write('\t'.join(header) + '\n')
        
        # Write rows
        for row in rows:
            # Convert multi-line cells to single line with semicolons
            tsv_row = []
            for cell in row:
                cell_str = str(cell)
                if '\n' in cell_str:
                    cell_str = cell_str.replace('\n', '; ')
                # Remove tabs from cell content to avoid breaking TSV format
                cell_str = cell_str.replace('\t', ' ')
                tsv_row.append(cell_str)
            f.write('\t'.join(tsv_row) + '\n')

def main():
    if len(sys.argv) < 2:
        print("Usage: python generate_annotation_tables.py <results.json> [output_prefix]")
        sys.exit(1)
    
    results_file = sys.argv[1]
    output_prefix = sys.argv[2] if len(sys.argv) > 2 else "annotation_strategies"
    
    if not Path(results_file).exists():
        print(f"Error: Results file not found: {results_file}")
        sys.exit(1)
    
    # Load results
    results = load_results(results_file)
    
    # Define target strategies for BOL
    bol_strategies = [
        ("AUX - cop", "AUX", "cop"),
        ("VERB - xcomp", "VERB", "xcomp")
    ]
    
    # Define target strategies for ER
    er_strategies = [
        ("AUX - cop", "AUX", "cop"),
        ("VERB - xcomp", "VERB", "xcomp")
    ]
    
    # Generate BOL table
    print("Generating BOL annotation strategies table...")
    bol_header, bol_rows = generate_table(results, "BOL", bol_strategies)
    print_table(bol_header, bol_rows, "Table 1. Attested strategies for annotation of BOL in existing Turkic treebanks")
    
    # Generate ER table
    print("\nGenerating ER annotation strategies table...")
    er_header, er_rows = generate_table(results, "ER", er_strategies)
    print_table(er_header, er_rows, "Table 2. Attested strategies for annotation of ER in existing Turkic treebanks")
    
    # Generate TSV files for easier pasting into Google Docs
    generate_tsv_table(bol_header, bol_rows, f"{output_prefix}_BOL.tsv")
    generate_tsv_table(er_header, er_rows, f"{output_prefix}_ER.tsv")
    
    print(f"\nTSV files generated:")
    print(f"  {output_prefix}_BOL.tsv")
    print(f"  {output_prefix}_ER.tsv")
    
    # Summary statistics
    print(f"\nSummary:")
    print(f"BOL treebanks analyzed: {len(bol_rows)}")
    print(f"ER treebanks analyzed: {len(er_rows)}")
    
    # Count strategies
    bol_aux_cop = sum(1 for row in bol_rows if row[1] == "✔")
    bol_verb_xcomp = sum(1 for row in bol_rows if row[2] == "✔")
    
    er_aux_cop = sum(1 for row in er_rows if row[1] == "✔")
    er_verb_case = sum(1 for row in er_rows if row[2] == "✔")
    
    print(f"\nBOL strategies:")
    print(f"  AUX-cop: {bol_aux_cop}/{len(bol_rows)} treebanks")
    print(f"  VERB-xcomp: {bol_verb_xcomp}/{len(bol_rows)} treebanks")
    
    print(f"\nER strategies:")
    print(f"  AUX-cop: {er_aux_cop}/{len(er_rows)} treebanks")
    print(f"  VERB-case: {er_verb_case}/{len(er_rows)} treebanks")

if __name__ == "__main__":
    main()
