# UD Query Script

A Python script that performs clustering queries on Universal Dependencies treebanks, similar to the functionality provided by Grew-match.

## Features

The script implements the following Grew-match pattern:

```grew
pattern { X [lemma="<lemma>"]; e: Y -> X }
clustering 1: X.upos ; clustering 2: e.label
```

This finds all tokens with a specified lemma that depend on other tokens, clustering by:

1. **X.upos**: The UPOS (Part-of-Speech) tag of the target token
2. **e.label**: The dependency relation label from the target token to its head

## Turkic Languages Clustering System

This repository includes a specialized system for clustering queries across all Turkic languages in Universal Dependencies. The `turkic_clustering.py` script allows you to:

- Process all Turkic language treebanks with language-specific lemma mappings
- Map overarching concepts (like "BOL" for copula) to language-specific lemmas
- Generate comprehensive results across Turkic language branches
- Use GitHub CLI for efficient treebank access without local cloning

### Turkic Languages Support

The system supports all Turkic languages available in UD:

**Southwestern Turkic**: Turkish (11 treebanks), Ottoman Turkish (2 treebanks), Azerbaijani (1 treebank)  
**Southeastern Turkic**: Uzbek (3 treebanks), Uyghur (2 treebanks)  
**Northwestern Turkic**: Kazakh (1 treebank), Kyrgyz (2 treebanks), Tatar (1 treebank)  
**Northeastern Turkic**: Old Turkish (1 treebank), Yakut (1 treebank)  
**Code-switching**: Turkish-English (1 treebank), Turkish-German (1 treebank)

### Turkic Usage

```bash
# List all Turkic languages and treebanks
python turkic_clustering.py --list-languages

# Create sample lemma mapping
python turkic_clustering.py --create-sample-mapping

# Process all Turkic languages with lemma mapping
python turkic_clustering.py --lemma-mapping lemma_mapping.json --output results.json

# Process with specific UD version
python turkic_clustering.py --lemma-mapping lemma_mapping.json --version 2.14 --output results.json
```

### Lemma Mapping Format

Create a JSON file specifying lemmas for each language:

```json
{
  "BOL": {
    "description": "Copula 'to be' equivalent across Turkic languages",
    "languages": {
      "Turkish": "ol",
      "Ottoman_Turkish": "ol", 
      "Uzbek": "bo'l",
      "Kazakh": "бол",
      "Kyrgyz": "бол",
      "Tatar": "бул",
      "Yakut": "буол",
      "Turkish_English": "ol",
      "Turkish_German": "ol"
    }
  },
  "I": {
    "description": "Auxiliary 'i-' copula across Turkic languages",
    "languages": {
      "Turkish": "i",
      "Ottoman_Turkish": "i",
      "Uzbek": "i",
      "Kazakh": "е",
      "Kyrgyz": "е", 
      "Tatar": "и",
      "Yakut": "и"
    }
  }
}
```

### GitHub CLI Integration

The system can use GitHub CLI (`gh`) for efficient treebank access:

1. Install GitHub CLI: <https://cli.github.com/>
2. Authenticate: `gh auth login`
3. The system will automatically use GitHub CLI if available

This avoids the need to clone repositories locally and provides faster access to treebank data.

## Usage

```bash
# Single treebank
python query.py <treebank_file_or_name> <lemma> [--verbose] [--version]

# Multiple treebanks
python query.py --treebank-list <file> <lemma> --output <output.json> [--version] [--verbose]
```

### Arguments

- `treebank` (optional): Either:
  - Path to a CoNLL-U format treebank file (e.g., `data/sample.conllu`)
  - Name of a published UD treebank (e.g., `UD_Turkish-BOUN`, `UD_English-EWT`)
- `lemma`: The lemma to search for in the treebank
- `--treebank-list` (optional): Path to a file containing list of treebank names (one per line)
- `--output` (optional): Output file path for JSON results (required when using --treebank-list)
- `--verbose` (optional): Enable verbose output with examples
- `--version` (optional): Specify version for published treebanks (e.g., `2.8`)

### Examples

```bash
# Load from local file
python query.py data/en_ewt-ud-train.conllu be

# Load published treebank by name
python query.py UD_Turkish-BOUN ol
python query.py UD_English-EWT be --verbose

# Use specific version of published treebank
python query.py UD_Turkish-BOUN ol --version 2.8 --verbose

# Process multiple treebanks and save results to JSON
echo -e "UD_Turkish-BOUN\nUD_Turkish-Atis" > treebanks.txt
python query.py --treebank-list treebanks.txt ol --output results.json
```

## Output

The script provides:

1. **Total matches**: Number of tokens with the specified lemma that have incoming dependencies
2. **UPOS clustering**: Distribution of Part-of-Speech tags for matching tokens
3. **Dependency relation clustering**: Distribution of dependency relation labels for incoming edges
4. **Combined clustering**: Joint distribution of (UPOS, dependency relation) pairs
5. **Examples** (with `--verbose`): First few concrete examples

### Sample Output

With the Turkish treebank `UD_Turkish-BOUN` and lemma "ol":

```text
Clustering Query Results for lemma 'ol'
==================================================
Total matches found: 3710

Clustering 1: X.upos (UPOS of target token)
----------------------------------------
VERB             3672 ( 99.0%)
NOUN               18 (  0.5%)
AUX                17 (  0.5%)
ADV                 3 (  0.1%)

Clustering 2: e.label (Dependency relation of incoming edge)
------------------------------------------------------------
punct                  687 ( 18.5%)
nsubj                  593 ( 16.0%)
obj                    513 ( 13.8%)
obl                    510 ( 13.7%)
amod                   231 (  6.2%)
advmod                 169 (  4.6%)
conj                   160 (  4.3%)
cop                    129 (  3.5%)
...

Combined Clustering: (UPOS, Dependency Relation)
--------------------------------------------------
(VERB, punct)                       678 ( 18.3%)
(VERB, nsubj)                       591 ( 15.9%)
(VERB, obj)                       511 ( 13.8%)
(VERB, obl)                       505 ( 13.6%)
...
```

## Requirements

- Python 3.6+
- The `conllu` module (included in this repository)
- Git (for downloading published treebanks)
- Internet connection (for first-time download of published treebanks)

## Published Treebanks

The script can automatically download and use any published Universal Dependencies treebank. When you specify a treebank name starting with `UD_`, the script will:

1. Clone the treebank repository from GitHub
2. Use the latest released version (or a specific version if `--version` is specified)
3. Load all `.conllu` files from the treebank

Downloaded treebanks are cached in `conllu/repos/` and don't need to be re-downloaded.

## Multi-Treebank Analysis

The script supports processing multiple treebanks at once and generating a comprehensive JSON report with separate clustering results for each treebank.

### Creating a Treebank List

Create a text file with one treebank name per line:

```text
UD_Turkish-BOUN
UD_Turkish-Atis
UD_English-EWT
UD_German-GSD
```

### Output Format

The multi-treebank mode outputs a JSON file with the following structure:

```json
{
  "lemma": "ol",
  "version": null,
  "total_treebanks": 2,
  "successful_treebanks": 2,
  "failed_treebanks": 0,
  "total_matches_all_treebanks": 2852,
  "treebank_results": {
    "UD_Turkish-BOUN": {
      "sentences_loaded": 9761,
      "total_matches": 1913,
      "upos_clusters": { "VERB": 1422, "AUX": 447, ... },
      "deprel_clusters": { "aux": 320, "compound:lvc": 292, ... },
      "combined_clusters": { "(VERB, aux)": 320, ... }
    },
    "UD_Turkish-Atis": {
      "sentences_loaded": 5432,
      "total_matches": 939,
      ...
    }
  }
}
```

## Data Format

The script accepts CoNLL-U format files as specified by the Universal Dependencies project. Each sentence should be separated by a blank line, and tokens should follow the 10-column CoNLL-U format.

## Understanding the Results

- **Clustering 1 (X.upos)**: Shows what part-of-speech categories the tokens with your queried lemma belong to
- **Clustering 2 (e.label)**: Shows what types of syntactic relationships other tokens have with your queried lemma
- **Combined Clustering**: Shows the joint distribution, helping you understand patterns like "NOUN tokens with lemma X are typically subjects (nsubj)"

This information is useful for linguistic analysis, understanding the syntactic behavior of specific words, and identifying patterns in dependency structures.
