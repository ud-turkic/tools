#!/usr/bin/env python3
"""
Generate a filtered markdown report from Turkic clustering results.
Shows only combined clusters with frequency >= 10% threshold.
"""

import json
import sys
from pathlib import Path

def generate_filtered_report(results_file, output_file, threshold=0.10):
    """
    Generate markdown report with filtered combined clusters.
    
    Args:
        results_file: Path to the JSON results file
        output_file: Path to output markdown file
        threshold: Minimum percentage threshold (default 0.10 = 10%)
    """
    
    # Load results
    with open(results_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Generate markdown content
    lines = []
    lines.append("# Turkic Languages Clustering Results - Filtered Report")
    lines.append("")
    lines.append(f"*Combined clusters with frequency ≥ {threshold*100:.0f}% only*")
    lines.append("")
    
    # Process each overarching lemma (BOL, ER)
    for lemma_key, lemma_data in data.items():
        lines.append(f"## {lemma_key}")
        lines.append("")
        lines.append(f"*{lemma_data.get('description', '')}*")
        lines.append("")
        
        # Process each language
        for lang_name, lang_data in lemma_data.get('languages', {}).items():
            lang_has_results = False
            lang_lines = []
            
            # Process each treebank
            for tb_name, tb_data in lang_data.get('treebanks', {}).items():
                total_matches = tb_data.get('total_matches', 0)
                if total_matches == 0:
                    continue
                
                combined_clusters = tb_data.get('combined_clusters', {})
                if not combined_clusters:
                    continue
                
                # Filter clusters by threshold
                filtered_clusters = []
                for cluster, count in combined_clusters.items():
                    percentage = count / total_matches
                    if percentage >= threshold:
                        # Parse cluster format "(UPOS, deprel)" 
                        cluster_clean = cluster.strip('()')
                        upos, deprel = cluster_clean.split(', ')
                        filtered_clusters.append((upos, deprel, count, percentage))
                
                if filtered_clusters:
                    if not lang_has_results:
                        lang_lines.append(f"### {lang_name.replace('_', ' ')}")
                        lang_lines.append("")
                        lang_has_results = True
                    
                    lang_lines.append(f"#### {tb_name}")
                    lang_lines.append("")
                    
                    # Sort by count (descending)
                    filtered_clusters.sort(key=lambda x: x[2], reverse=True)
                    
                    for upos, deprel, count, percentage in filtered_clusters:
                        lang_lines.append(f"{upos} - {deprel}\t{count} ({percentage*100:.1f}%)")
                    
                    lang_lines.append("")
            
            # Add language section if it has results
            if lang_has_results:
                lines.extend(lang_lines)
        
        lines.append("")
    
    # Write output
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    
    print(f"Filtered report generated: {output_file}")
    print(f"Threshold: {threshold*100:.0f}%")

def main():
    if len(sys.argv) < 2:
        print("Usage: python generate_filtered_report.py <results.json> [output.md] [threshold]")
        print("  results.json: Input JSON results file")
        print("  output.md: Output markdown file (default: filtered_report.md)")
        print("  threshold: Minimum percentage (default: 0.10 = 10%)")
        sys.exit(1)
    
    results_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else 'filtered_report.md'
    threshold = float(sys.argv[3]) if len(sys.argv) > 3 else 0.10
    
    if not Path(results_file).exists():
        print(f"Error: Results file not found: {results_file}")
        sys.exit(1)
    
    generate_filtered_report(results_file, output_file, threshold)

if __name__ == "__main__":
    main()
