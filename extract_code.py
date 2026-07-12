import os
import sys
from pathlib import Path

# Directories and files to ignore
IGNORE_DIRS = {
    'venv',
    '.venv',
    'env',
    '.git',
    '.github',
    '__pycache__',
    '.idea',
    '.vscode',
    'node_modules',
    'build',
    'dist'
}

IGNORE_FILES = {
    'extract_code.py',
    'project_source.md',
    '.gitignore',
    'package-lock.json',
    'poetry.lock',
    'yarn.lock'
}

# Source file extensions to extract
SUPPORTED_EXTENSIONS = {
    '.py', '.md', '.txt', '.json', '.yaml', '.yml', '.toml', '.ini', '.cfg', '.sh', '.bat', '.ps1'
}

def build_tree(dir_path, prefix="", ignore_dirs=None, ignore_files=None):
    if ignore_dirs is None:
        ignore_dirs = IGNORE_DIRS
    if ignore_files is None:
        ignore_files = IGNORE_FILES
        
    tree_lines = []
    
    try:
        entries = sorted(list(Path(dir_path).iterdir()), key=lambda x: (not x.is_dir(), x.name.lower()))
    except PermissionError:
        return [prefix + "└── [Permission Denied]"]
        
    filtered_entries = []
    for entry in entries:
        if entry.is_dir():
            if entry.name in ignore_dirs:
                continue
        else:
            if entry.name in ignore_files:
                continue
            if entry.suffix not in SUPPORTED_EXTENSIONS:
                continue
        filtered_entries.append(entry)
        
    count = len(filtered_entries)
    for i, entry in enumerate(filtered_entries):
        is_last = (i == count - 1)
        connector = "└── " if is_last else "├── "
        
        if entry.is_dir():
            tree_lines.append(f"{prefix}{connector}{entry.name}/")
            new_prefix = prefix + ("    " if is_last else "│   ")
            tree_lines.extend(build_tree(entry, new_prefix, ignore_dirs, ignore_files))
        else:
            tree_lines.append(f"{prefix}{connector}{entry.name}")
            
    return tree_lines

def extract_source(root_path, output_file_path):
    root = Path(root_path)
    
    # Generate tree
    tree_header = [f"Project Directory Tree: {root.name}"]
    tree_header.append("=" * len(tree_header[0]))
    tree_header.append(".")
    tree_header.extend(build_tree(root))
    tree_str = "\n".join(tree_header)
    
    output_content = []
    output_content.append("# Project Source Code Export\n")
    output_content.append("## Directory Tree\n")
    output_content.append("```text")
    output_content.append(tree_str)
    output_content.append("```\n")
    output_content.append("---")
    
    # Extract file contents
    def walk_and_extract(dir_path):
        try:
            entries = sorted(list(Path(dir_path).iterdir()), key=lambda x: (not x.is_dir(), x.name.lower()))
        except PermissionError:
            return
            
        for entry in entries:
            if entry.is_dir():
                if entry.name in IGNORE_DIRS:
                    continue
                walk_and_extract(entry)
            else:
                if entry.name in IGNORE_FILES:
                    continue
                if entry.suffix not in SUPPORTED_EXTENSIONS:
                    continue
                    
                # Read content
                rel_path = entry.relative_to(root)
                output_content.append(f"## File: `{rel_path.as_posix()}`")
                
                # Determine language for markdown block
                lang = entry.suffix.lstrip('.')
                if lang == 'py':
                    lang = 'python'
                elif lang == 'md':
                    lang = 'markdown'
                elif lang == 'sh' or lang == 'bash':
                    lang = 'bash'
                elif lang == 'bat' or lang == 'ps1':
                    lang = 'powershell'
                elif lang not in ['json', 'yaml', 'yml', 'toml', 'ini', 'cfg', 'txt']:
                    lang = 'text'
                    
                output_content.append(f"```{lang}")
                try:
                    with open(entry, 'r', encoding='utf-8', errors='replace') as f:
                        content = f.read()
                    # Make sure triple backticks in markdown are not breaking the markdown blocks
                    if lang == 'markdown':
                        content = content.replace("```", "``\\`" if sys.version_info >= (3, 0) else "``\\`")
                    output_content.append(content)
                except Exception as e:
                    output_content.append(f"Error reading file: {str(e)}")
                output_content.append("```\n")
                output_content.append("---")
                
    walk_and_extract(root)
    
    # Save to output file
    try:
        with open(output_file_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(output_content))
        print(f"Source codes successfully extracted to: {output_file_path}")
    except Exception as e:
        print(f"Error writing output file: {str(e)}")

if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else os.getcwd()
    output_file = os.path.join(current_dir, "project_source.md")
    extract_source(current_dir, output_file)
