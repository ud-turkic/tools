#!/usr/bin/env python3
"""
GitHub CLI Repository Discovery for Universal Dependencies

This script uses the GitHub CLI (`gh`) to discover all UD repositories
and extract language-to-treebank mappings without cloning repositories.

Usage:
    python get_ud_repos_with_gh.py
    python get_ud_repos_with_gh.py --output ud_repos_gh.json

Requirements:
    - GitHub CLI (`gh`) must be installed and authenticated
    - Run: gh auth login
"""

import subprocess
import json
import sys
import argparse
import re
from pathlib import Path
from collections import defaultdict

def check_gh_cli():
    """
    Check if GitHub CLI is installed and authenticated.
    
    Returns:
        bool: True if gh CLI is available and authenticated
    """
    try:
        # Check if gh is installed
        result = subprocess.run(['gh', '--version'], 
                              capture_output=True, text=True, check=True)
        print(f"GitHub CLI found: {result.stdout.strip().split()[2]}")
        
        # Check if authenticated
        result = subprocess.run(['gh', 'auth', 'status'], 
                              capture_output=True, text=True, check=True)
        print("GitHub CLI authentication: OK")
        return True
        
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"GitHub CLI check failed: {e}")
        print("\nTo fix this:")
        print("1. Install GitHub CLI: https://cli.github.com/")
        print("2. Authenticate: gh auth login")
        return False

def get_ud_repositories():
    """
    Get all Universal Dependencies repositories using GitHub CLI.
    
    Returns:
        list: List of repository information dictionaries
    """
    print("Fetching UD repositories with GitHub CLI...")
    
    try:
        # Get all repos in the UniversalDependencies organization
        cmd = [
            'gh', 'repo', 'list', 'UniversalDependencies',
            '--limit', '1000',  # Should be enough for all UD repos
            '--json', 'name,description,defaultBranch,updatedAt,pushedAt'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        repos = json.loads(result.stdout)
        
        print(f"Found {len(repos)} repositories in UniversalDependencies organization")
        return repos
        
    except subprocess.CalledProcessError as e:
        print(f"Error fetching repositories: {e}")
        print(f"Command output: {e.stderr}")
        sys.exit(1)

def extract_language_from_repo_name(repo_name):
    """
    Extract language name from UD repository name.
    
    Args:
        repo_name: Repository name (e.g., "UD_Turkish-BOUN")
        
    Returns:
        tuple: (language, treebank_code) or (None, None) if not a treebank repo
    """
    # Standard UD treebank pattern: UD_Language-Treebank or UD_Language_OtherLanguage-Treebank
    if not repo_name.startswith('UD_'):
        return None, None
    
    # Remove UD_ prefix
    name_part = repo_name[3:]
    
    # Handle code-switching treebanks (e.g., UD_Turkish_German-SAGT)
    if '_' in name_part and '-' in name_part:
        # This could be code-switching like Turkish_German or something else
        parts = name_part.split('-')
        if len(parts) >= 2:
            language_part = parts[0]
            treebank_code = '-'.join(parts[1:])
            return language_part, treebank_code
    
    # Standard treebanks (e.g., UD_Turkish-BOUN)
    elif '-' in name_part:
        parts = name_part.split('-', 1)
        language = parts[0]
        treebank_code = parts[1]
        return language, treebank_code
    
    return None, None

def get_repo_metadata(repo_name):
    """
    Get additional metadata for a repository using GitHub CLI.
    
    Args:
        repo_name: Repository name
        
    Returns:
        dict: Repository metadata
    """
    try:
        cmd = [
            'gh', 'api', f'repos/UniversalDependencies/{repo_name}',
            '--jq', '.size,.stargazers_count,.language'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        lines = result.stdout.strip().split('\n')
        
        return {
            'size_kb': int(lines[0]) if lines[0] != 'null' else 0,
            'stars': int(lines[1]) if lines[1] != 'null' else 0,
            'primary_language': lines[2] if lines[2] != 'null' else None
        }
        
    except (subprocess.CalledProcessError, IndexError, ValueError):
        return {
            'size_kb': 0,
            'stars': 0,
            'primary_language': None
        }

def fetch_lang_spec_docs():
    """
    Fetch the language specification docs to get authoritative language list.
    
    Returns:
        dict: Mapping of language codes to language names
    """
    try:
        # Use gh to fetch the file content
        cmd = [
            'gh', 'api',
            'repos/UniversalDependencies/docs/contents/_includes/lang_spec_docs.html',
            '--jq', '.content'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        import base64
        content = base64.b64decode(result.stdout.strip()).decode('utf-8')
        
        # Extract language links
        language_pattern = r'<a\s+href="/([^/]+)/index\.html">([^<]+)</a>'
        languages = {}
        
        for match in re.finditer(language_pattern, content):
            lang_code = match.group(1)
            lang_name = match.group(2)
            languages[lang_code] = lang_name
        
        print(f"Found {len(languages)} languages in lang_spec_docs.html")
        return languages
        
    except Exception as e:
        print(f"Warning: Could not fetch lang_spec_docs.html: {e}")
        return {}

def create_language_mapping(repos, lang_spec_mapping=None):
    """
    Create language to treebank mapping from repository list.
    
    Args:
        repos: List of repository information
        lang_spec_mapping: Optional mapping from lang_spec_docs.html
        
    Returns:
        dict: Language to treebank list mapping
    """
    language_mapping = defaultdict(list)
    repo_details = {}
    
    print("Processing repository names...")
    
    for repo in repos:
        repo_name = repo['name']
        language, treebank_code = extract_language_from_repo_name(repo_name)
        
        if language and treebank_code:
            # Get additional metadata
            metadata = get_repo_metadata(repo_name)
            
            repo_details[repo_name] = {
                'language': language,
                'treebank_code': treebank_code,
                'description': repo.get('description', ''),
                'updated_at': repo.get('updatedAt', ''),
                'pushed_at': repo.get('pushedAt', ''),
                'default_branch': repo.get('defaultBranch', 'master'),
                **metadata
            }
            
            language_mapping[language].append(repo_name)
        else:
            # Non-treebank repository (docs, tools, etc.)
            repo_details[repo_name] = {
                'type': 'non-treebank',
                'description': repo.get('description', ''),
                'updated_at': repo.get('updatedAt', ''),
                'default_branch': repo.get('defaultBranch', 'master')
            }
    
    # Sort treebanks for each language
    for language in language_mapping:
        language_mapping[language].sort()
    
    return dict(language_mapping), repo_details

def main():
    parser = argparse.ArgumentParser(
        description="GitHub CLI Repository Discovery for Universal Dependencies",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Discover all UD repositories
  python get_ud_repos_with_gh.py
  
  # Save results to specific file
  python get_ud_repos_with_gh.py --output ud_repos_gh.json
  
  # Include detailed metadata
  python get_ud_repos_with_gh.py --detailed --output detailed_repos.json
        """
    )
    
    parser.add_argument('--output', '-o',
                       default='ud_repos_gh.json',
                       help='Output file for repository mapping (default: ud_repos_gh.json)')
    parser.add_argument('--detailed',
                       action='store_true',
                       help='Include detailed repository metadata')
    parser.add_argument('--languages-only',
                       action='store_true',
                       help='Only output language-to-treebank mapping')
    
    args = parser.parse_args()
    
    # Check GitHub CLI
    if not check_gh_cli():
        sys.exit(1)
    
    print("\nDiscovering Universal Dependencies repositories...")
    
    # Get all repositories
    repos = get_ud_repositories()
    
    # Fetch language specification if needed
    lang_spec_mapping = None
    if args.detailed:
        print("\nFetching language specification documentation...")
        lang_spec_mapping = fetch_lang_spec_docs()
    
    # Create mappings
    language_mapping, repo_details = create_language_mapping(repos, lang_spec_mapping)
    
    # Prepare output
    if args.languages_only:
        output_data = language_mapping
    else:
        output_data = {
            'language_mapping': language_mapping,
            'repository_details': repo_details if args.detailed else {},
            'summary': {
                'total_repositories': len(repos),
                'treebank_repositories': sum(len(tbs) for tbs in language_mapping.values()),
                'languages_with_treebanks': len(language_mapping),
                'generated_with_gh_cli': True
            }
        }
    
    # Save results
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    # Print summary
    print(f"\nSUMMARY:")
    print(f"Total repositories: {len(repos)}")
    print(f"Languages with treebanks: {len(language_mapping)}")
    print(f"Total treebank repositories: {sum(len(tbs) for tbs in language_mapping.values())}")
    
    print(f"\nTop languages by number of treebanks:")
    sorted_languages = sorted(language_mapping.items(), key=lambda x: len(x[1]), reverse=True)
    for language, treebanks in sorted_languages[:10]:
        print(f"  {language}: {len(treebanks)} treebanks")
    
    # Highlight Turkic languages
    print(f"\nTurkic languages found:")
    turkic_keywords = ['Turkish', 'Uzbek', 'Kazakh', 'Kyrgyz', 'Tatar', 'Yakut', 'Uyghur', 'Azerbaijani', 'Ottoman']
    for language, treebanks in language_mapping.items():
        if any(keyword in language for keyword in turkic_keywords):
            print(f"  {language}: {len(treebanks)} treebanks")
    
    print(f"\nResults saved to {args.output}")

if __name__ == "__main__":
    main()
