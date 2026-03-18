from pathlib import Path
import argparse, os, re

def parse_args():
    parser = argparse.ArgumentParser(description='Run validation on CoNLL-U files.')
    parser.add_argument('-f', '--files', type=str, nargs='+', help='List of CoNLL-U files to validate.', required=True)
    return parser.parse_args()

def main():
    args = parse_args()
    script_dir = Path(__file__).parent
    conllu_files = [Path(file) for file in args.files]
    if not all(file.exists() for file in conllu_files):
        print('One or more files do not exist.')
        return
    language_pattern = re.compile(r'(\w+)_.+\.conllu')
    languages = set()
    for file in conllu_files:
        language = language_pattern.match(file.name).group(1)
        languages.add(language)
    if len(languages) > 1:
        print('Multiple languages detected in the directory.')
        return

    tools_dir = script_dir / 'tools'
    validation_script_path = tools_dir / 'validate.py'
    data_dir = tools_dir / 'data'
    if not tools_dir.exists() or not validation_script_path.exists() or not data_dir.exists():
        os.system(f'git clone https://github.com/UniversalDependencies/tools.git')
    else:
        os.system(f'cd {tools_dir} && git pull')
    os.chdir(script_dir)
    
    # Extract treebank title from the first file
    treebank_pattern = re.compile(r'(\w+_\w+)-')
    treebank_match = treebank_pattern.search(conllu_files[0].name)
    if treebank_match:
        treebank_title = treebank_match.group(1)
    else:
        treebank_title = language
    
    log_filename = f'{treebank_title}_validation.log'
    validation_command = f'python {validation_script_path} --lang {language} --max-err 0 {' '.join([str(file) for file in conllu_files])} &> {log_filename}'
    os.system(validation_command)

if __name__ == '__main__':
    main()