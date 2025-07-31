#!/usr/bin/env python3
"""
Create a local searchable index of the codebase
"""
import os
import json
from pathlib import Path
from datetime import datetime

def should_ignore_file(file_path, ignore_patterns):
    """Check if file should be ignored based on patterns"""
    file_str = str(file_path)
    for pattern in ignore_patterns:
        if pattern in file_str or file_str.endswith(pattern):
            return True
    return False

def create_codebase_index():
    """Create a local index of the codebase"""
    
    # Define file extensions to index
    code_extensions = {'.py', '.js', '.ts', '.tsx', '.jsx', '.html', '.css', '.json', '.md', '.txt', '.yml', '.yaml'}
    
    # Define ignore patterns
    ignore_patterns = [
        '__pycache__',
        'node_modules',
        '.git',
        'myenv',
        'venv',
        '.vscode',
        '.idea',
        'output',
        'logs',
        '.egg-info',
        'dist',
        'build'
    ]
    
    index = {
        'created_at': datetime.now().isoformat(),
        'total_files': 0,
        'files': [],
        'directories': [],
        'file_types': {},
        'summary': {}
    }
    
    project_root = Path('.')
    
    print("🔍 Creating local codebase index...")
    
    for root, dirs, files in os.walk(project_root):
        root_path = Path(root)
        
        # Skip ignored directories
        if should_ignore_file(root_path, ignore_patterns):
            continue
            
        # Add directory to index
        if root_path != project_root:
            index['directories'].append(str(root_path))
        
        for file in files:
            file_path = root_path / file
            
            # Skip ignored files
            if should_ignore_file(file_path, ignore_patterns):
                continue
                
            # Check if it's a code file
            if file_path.suffix.lower() in code_extensions:
                try:
                    # Get file stats
                    stat = file_path.stat()
                    
                    # Read file content (first 1000 chars for preview)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content_preview = f.read(1000)
                    except:
                        content_preview = "[Binary or unreadable file]"
                    
                    file_info = {
                        'path': str(file_path),
                        'name': file_path.name,
                        'extension': file_path.suffix,
                        'size_bytes': stat.st_size,
                        'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        'content_preview': content_preview
                    }
                    
                    index['files'].append(file_info)
                    index['total_files'] += 1
                    
                    # Count file types
                    ext = file_path.suffix.lower()
                    index['file_types'][ext] = index['file_types'].get(ext, 0) + 1
                    
                except Exception as e:
                    print(f"⚠️ Error processing {file_path}: {e}")
    
    # Create summary
    index['summary'] = {
        'total_files': index['total_files'],
        'total_directories': len(index['directories']),
        'file_types_count': len(index['file_types']),
        'most_common_types': sorted(index['file_types'].items(), key=lambda x: x[1], reverse=True)[:5]
    }
    
    # Save index to file
    index_file = 'local_codebase_index.json'
    with open(index_file, 'w', encoding='utf-8') as f:
        json.dump(index, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Index created: {index_file}")
    print(f"📊 Indexed {index['total_files']} files in {len(index['directories'])} directories")
    print(f"📁 File types: {dict(index['file_types'])}")
    
    return index_file

def search_index(query, index_file='local_codebase_index.json'):
    """Search the local index"""
    try:
        with open(index_file, 'r', encoding='utf-8') as f:
            index = json.load(f)
        
        results = []
        query_lower = query.lower()
        
        for file_info in index['files']:
            # Search in file path, name, and content preview
            if (query_lower in file_info['path'].lower() or 
                query_lower in file_info['name'].lower() or 
                query_lower in file_info['content_preview'].lower()):
                results.append(file_info)
        
        return results
    except Exception as e:
        print(f"Error searching index: {e}")
        return []

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "search" and len(sys.argv) > 2:
            # Search mode
            query = " ".join(sys.argv[2:])
            print(f"🔍 Searching for: {query}")
            results = search_index(query)
            
            if results:
                print(f"📋 Found {len(results)} results:")
                for result in results[:10]:  # Show first 10 results
                    print(f"  📄 {result['path']} ({result['size_bytes']} bytes)")
            else:
                print("❌ No results found")
        else:
            print("Usage: python create_local_index.py search <query>")
    else:
        # Create index mode
        create_codebase_index()
