#!/usr/bin/env python3
"""
Turkic Languages Clustering System for Universal Dependencies

This script performs clustering queries on all Turkic language treebanks in UD,
allowing for language-specific lemma mappings (e.g., "ol-" in Turkish, "бол-" in Kazakh).

Usage:
    python turkic_clustering.py --lemma-mapping lemma_mapping.json
    python turkic_clustering.py --lemma-mapping lemma_mapping.json --output results.json

The lemma mapping file should specify the lemma for each language, e.g.:
{
  "BOL": {
    "description": "Copula 'to be' equivalent across Turkic languages",
    "languages": {
      "Turkish": "ol-",
      "Ottoman_Turkish": "ol-",
      "Old_Turkish": "ėr-",
      "Azerbaijani": "ol-",
      "Uzbek": "bo'l-",
      "Uyghur": "بول-",
      "Kazakh": "бол-",
      "Kyrgyz": "бол-",
      "Tatar": "бул-",
      "Yakut": "буол-",
      "Turkish_English": "ol-",
      "Turkish_German": "ol-"
    }
  }
}
"""

import sys
import argparse
import json
from pathlib import Path
from collections import defaultdict, Counter
from conllu.conllu import Treebank

# Define all Turkic languages in UD based on the lang_spec_docs.html
TURKIC_LANGUAGES = {
    # Southwestern Turkic
    "Turkish": ["UD_Turkish-Atis", "UD_Turkish-BOUN", "UD_Turkish-FrameNet", 
                "UD_Turkish-GB", "UD_Turkish-IMST", "UD_Turkish-Kenet", 
                "UD_Turkish-PUD", "UD_Turkish-Penn", "UD_Turkish-Tourism", 
                "UD_Turkish-TueCL", "UD_Turkish-ULU"],
    "Ottoman_Turkish": ["UD_Ottoman_Turkish-BOUN", "UD_Ottoman_Turkish-DUDU"],
    "Azerbaijani": ["UD_Azerbaijani-TueCL"],
    
    # Southeastern Turkic
    "Uzbek": ["UD_Uzbek-TueCL", "UD_Uzbek-UT", "UD_Uzbek-UzUDT"],
    "Uyghur": ["UD_Uyghur-LDS", "UD_Uyghur-UDT"],
    
    # Northwestern Turkic
    "Kazakh": ["UD_Kazakh-KTB"],
    "Kyrgyz": ["UD_Kyrgyz-KTMU", "UD_Kyrgyz-TueCL"],
    "Tatar": ["UD_Tatar-NMCTT"],
    
    # Northeastern Turkic
    "Old_Turkish": ["UD_Old_Turkish-Clausal"],
    "Yakut": ["UD_Yakut-YKTDT"],
    
    # Code-switching treebanks
    "Turkish_English": ["UD_Turkish_English-BUTR"],
    "Turkish_German": ["UD_Turkish_German-SAGT"]
}

# Turkic language branches for classification
TURKIC_BRANCHES = {
    "Southwestern": ["Turkish", "Ottoman_Turkish", "Azerbaijani"],
    "Southeastern": ["Uzbek", "Uyghur"], 
    "Northwestern": ["Kazakh", "Kyrgyz", "Tatar"],
    "Northeastern": ["Old_Turkish", "Yakut"],
    "Code-switching": ["Turkish_English", "Turkish_German"]
}

def load_lemma_mapping(mapping_file):
    """
    Load the lemma mapping file that specifies which lemma to use for each language.
    
    Args:
        mapping_file: Path to JSON file with lemma mappings
        
    Returns:
        dict: Mapping structure with overarching lemma names and language-specific lemmas
    """
    with open(mapping_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def find_lemma_matches(treebank, lemmas):
    """
    Find all tokens with any of the specified lemmas that depend on other tokens.
    
    Args:
        treebank: Treebank object containing parsed sentences
        lemmas: List of lemmas to search for (or single lemma string)
        
    Returns:
        List of tuples (dependent_token, head_token) where dependent_token has one of the 
        specified lemmas and head_token is what it depends on
    """
    # Ensure lemmas is a list
    if isinstance(lemmas, str):
        lemmas = [lemmas]
    
    matches = []
    
    for sentence in treebank.sentences.values():
        for token in sentence.tokens.values():
            if token.lemma in lemmas and token.head:
                matches.append((token, token.head))
    
    return matches

def perform_clustering(matches):
    """
    Perform clustering analysis on the matches.
    
    Args:
        matches: List of (dependent_token, head_token) tuples
        
    Returns:
        Dictionary with clustering statistics
    """
    upos_clusters = Counter()
    deprel_clusters = Counter()
    combined_clusters = Counter()
    
    for dependent_token, head_token in matches:
        upos = dependent_token.upos or "None"
        deprel = dependent_token.deprel or "None"
        
        upos_clusters[upos] += 1
        deprel_clusters[deprel] += 1
        combined_clusters[(upos, deprel)] += 1
    
    return {
        'upos_clusters': upos_clusters,
        'deprel_clusters': deprel_clusters,
        'combined_clusters': combined_clusters,
        'total_matches': len(matches)
    }

def process_turkic_languages(lemma_mapping, output_file=None, version=None, verbose=False):
    """
    Process all Turkic languages with their respective lemmas.
    
    Args:
        lemma_mapping: Dictionary with lemma mappings
        output_file: Optional output file path
        version: Optional UD version to use
        verbose: Enable verbose output
        
    Returns:
        Dictionary with complete results
    """
    results = {}
    
    # Process each overarching lemma (e.g., "BOL")
    for overarching_lemma, lemma_info in lemma_mapping.items():
        print(f"\n{'='*60}")
        print(f"Processing overarching lemma: {overarching_lemma}")
        print(f"Description: {lemma_info.get('description', 'No description')}")
        print(f"{'='*60}")
        
        overarching_results = {
            'description': lemma_info.get('description', ''),
            'languages': {},
            'summary': {
                'total_treebanks_processed': 0,
                'total_treebanks_successful': 0,
                'total_matches_all_languages': 0,
                'languages_processed': 0,
                'languages_successful': 0
            },
            'branch_summary': {branch: {'languages': 0, 'treebanks': 0, 'matches': 0} 
                              for branch in TURKIC_BRANCHES.keys()}
        }
        
        # Process each language
        for language, language_lemmas in lemma_info['languages'].items():
            if language not in TURKIC_LANGUAGES:
                print(f"Warning: {language} not found in Turkic languages list, skipping...")
                continue
            
            # Skip if no lemmas defined for this language
            if not language_lemmas:
                print(f"\nSkipping {language} - no lemmas defined")
                continue
            
            # Ensure language_lemmas is a list
            if isinstance(language_lemmas, str):
                language_lemmas = [language_lemmas]
            
            lemmas_str = ", ".join(f"'{lemma}'" for lemma in language_lemmas)
            print(f"\nProcessing {language} with lemmas: {lemmas_str}")
            
            language_results = {
                'lemmas': language_lemmas,
                'treebanks': {},
                'total_matches': 0,
                'total_treebanks': len(TURKIC_LANGUAGES[language]),
                'successful_treebanks': 0,
                'branch': None
            }
            
            # Determine branch
            for branch, languages in TURKIC_BRANCHES.items():
                if language in languages:
                    language_results['branch'] = branch
                    break
            
            overarching_results['summary']['languages_processed'] += 1
            overarching_results['summary']['total_treebanks_processed'] += len(TURKIC_LANGUAGES[language])
            
            # Process each treebank for this language
            for treebank_name in TURKIC_LANGUAGES[language]:
                try:
                    if verbose:
                        print(f"  Loading {treebank_name}...")
                    
                    # Load treebank
                    treebank = Treebank(name=treebank_name, published=True, version=version)
                    matches = find_lemma_matches(treebank, language_lemmas)
                    clustering_results = perform_clustering(matches)
                    
                    # Store treebank results
                    language_results['treebanks'][treebank_name] = {
                        'sentences_loaded': len(treebank.sentences),
                        'total_matches': clustering_results['total_matches'],
                        'upos_clusters': dict(clustering_results['upos_clusters'].most_common()),
                        'deprel_clusters': dict(clustering_results['deprel_clusters'].most_common()),
                        'combined_clusters': {f"({k[0]}, {k[1]})": v 
                                            for k, v in clustering_results['combined_clusters'].most_common()}
                    }
                    
                    language_results['total_matches'] += clustering_results['total_matches']
                    language_results['successful_treebanks'] += 1
                    overarching_results['summary']['total_treebanks_successful'] += 1
                    
                    print(f"    {treebank_name}: {len(treebank.sentences)} sentences, {clustering_results['total_matches']} matches")
                    
                except Exception as e:
                    print(f"    {treebank_name}: ERROR - {e}")
                    language_results['treebanks'][treebank_name] = {
                        'error': str(e),
                        'total_matches': 0
                    }
            
            # Update summary statistics
            if language_results['successful_treebanks'] > 0:
                overarching_results['summary']['languages_successful'] += 1
            
            overarching_results['summary']['total_matches_all_languages'] += language_results['total_matches']
            
            # Update branch summary
            if language_results['branch']:
                branch = language_results['branch']
                overarching_results['branch_summary'][branch]['languages'] += 1
                overarching_results['branch_summary'][branch]['treebanks'] += language_results['successful_treebanks']
                overarching_results['branch_summary'][branch]['matches'] += language_results['total_matches']
            
            overarching_results['languages'][language] = language_results
            
            print(f"  Summary: {language_results['successful_treebanks']}/{language_results['total_treebanks']} treebanks successful, {language_results['total_matches']} total matches")
        
        results[overarching_lemma] = overarching_results
        
        # Print summary for this overarching lemma
        summary = overarching_results['summary']
        print(f"\n{overarching_lemma} SUMMARY:")
        print(f"  Languages: {summary['languages_successful']}/{summary['languages_processed']} successful")
        print(f"  Treebanks: {summary['total_treebanks_successful']}/{summary['total_treebanks_processed']} successful")
        print(f"  Total matches: {summary['total_matches_all_languages']}")
        
        print(f"\n  By branch:")
        for branch, branch_stats in overarching_results['branch_summary'].items():
            if branch_stats['languages'] > 0:
                print(f"    {branch}: {branch_stats['languages']} languages, {branch_stats['treebanks']} treebanks, {branch_stats['matches']} matches")
    
    # Save results if requested
    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"\nDetailed results saved to {output_file}")
    
    return results

def create_sample_lemma_mapping():
    """
    Create a sample lemma mapping file for the BOL copula across Turkic languages.
    
    Returns:
        dict: Sample lemma mapping structure
    """
    return {
        "BOL": {
            "description": "Copula 'to be' equivalent across Turkic languages",
            "languages": {
                "Turkish": ["ol"],
                "Ottoman_Turkish": ["ol"],
                "Old_Turkish": [],
                "Azerbaijani": ["ol"],
                "Uzbek": ["boʻl", "bo'l"],
                "Uyghur": ["بول"],
                "Kazakh": ["бол"],
                "Kyrgyz": ["бол"],
                "Tatar": ["бул"],
                "Yakut": ["буол"],
                "Turkish_English": ["ol"],
                "Turkish_German": ["ol"]
            }
        },
        "ER": {
            "description": "Auxiliary 'i/er' copula across Turkic languages",
            "languages": {
                "Turkish": ["i", "y"],
                "Ottoman_Turkish": ["i", "y"],
                "Old_Turkish": ["i", "y"],
                "Azerbaijani": ["i"],
                "Uzbek": ["i"],
                "Uyghur": ["ئى"],
                "Kazakh": ["е"],
                "Kyrgyz": ["э"],
                "Tatar": ["и"],
                "Yakut": ["э"],
                "Turkish_English": ["i"],
                "Turkish_German": ["i"]
            }
        }
    }

def main():
    parser = argparse.ArgumentParser(
        description="Turkic Languages Clustering System for Universal Dependencies",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process all Turkic languages with provided lemma mapping
  python turkic_clustering.py --lemma-mapping lemma_mapping.json
  
  # Save results to JSON file
  python turkic_clustering.py --lemma-mapping lemma_mapping.json --output turkic_results.json
  
  # Create sample lemma mapping file
  python turkic_clustering.py --create-sample-mapping
  
  # Use specific UD version
  python turkic_clustering.py --lemma-mapping lemma_mapping.json --version 2.14
        """
    )
    
    parser.add_argument('--lemma-mapping',
                       help='JSON file with language-specific lemma mappings')
    parser.add_argument('--output', '-o',
                       help='Output file for results (JSON format)')
    parser.add_argument('--version',
                       help='Specific version of UD treebanks to use (e.g., 2.14)')
    parser.add_argument('--verbose', '-v',
                       action='store_true',
                       help='Enable verbose output')
    parser.add_argument('--create-sample-mapping',
                       action='store_true',
                       help='Create a sample lemma mapping file (sample_lemma_mapping.json)')
    parser.add_argument('--list-languages',
                       action='store_true',
                       help='List all Turkic languages and their treebanks')
    
    args = parser.parse_args()
    
    # Create sample mapping file
    if args.create_sample_mapping:
        sample_mapping = create_sample_lemma_mapping()
        with open('sample_lemma_mapping.json', 'w', encoding='utf-8') as f:
            json.dump(sample_mapping, f, indent=2, ensure_ascii=False)
        print("Sample lemma mapping created in 'sample_lemma_mapping.json'")
        return
    
    # List languages
    if args.list_languages:
        print("Turkic Languages in Universal Dependencies:")
        print("=" * 50)
        for branch, languages in TURKIC_BRANCHES.items():
            print(f"\n{branch} Turkic:")
            for language in languages:
                if language in TURKIC_LANGUAGES:
                    print(f"  {language}:")
                    for treebank in TURKIC_LANGUAGES[language]:
                        print(f"    - {treebank}")
        return
    
    # Validate arguments
    if not args.lemma_mapping:
        parser.error("Must specify --lemma-mapping file (use --create-sample-mapping to create a sample)")
    
    if not Path(args.lemma_mapping).exists():
        print(f"Error: Lemma mapping file '{args.lemma_mapping}' not found.")
        print("Use --create-sample-mapping to create a sample file.")
        sys.exit(1)
    
    # Load lemma mapping
    try:
        lemma_mapping = load_lemma_mapping(args.lemma_mapping)
    except Exception as e:
        print(f"Error loading lemma mapping: {e}")
        sys.exit(1)
    
    print("Turkic Languages Clustering System")
    print("=" * 40)
    print(f"Lemma mapping: {args.lemma_mapping}")
    if args.version:
        print(f"UD version: {args.version}")
    print(f"Output file: {args.output or 'console only'}")
    
    # Process all Turkic languages
    try:
        results = process_turkic_languages(
            lemma_mapping, 
            output_file=args.output,
            version=args.version,
            verbose=args.verbose
        )
        
        print(f"\nProcessing complete!")
        if not args.output:
            print("Use --output to save detailed results to a file.")
            
    except Exception as e:
        print(f"Error during processing: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
