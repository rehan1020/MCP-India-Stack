import re

files_to_update = [
    'pyproject.toml',
    'src/mcp_india_stack/__init__.py',
    'docs/resources.md',
    'SETUP.md',
    'smithery.yaml',
    'README.md'
]

for file in files_to_update:
    try:
        with open(file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Replace 0.6.4 with 0.6.5
        content = re.sub(r'0\.6\.4', '0.6.5', content)
        
        with open(file, 'w', encoding='utf-8') as f:
            f.write(content)
    except FileNotFoundError:
        pass
