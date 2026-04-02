import os
import glob

replacements = {
    'label_0': 'label_0',
    'label_1': 'label_1',
    'naming_prefix_0': 'naming_prefix_0',
    'naming_prefix_1': 'naming_prefix_1',
    'NAMING_PREFIX_0': 'NAMING_PREFIX_0',
    'NAMING_PREFIX_1': 'NAMING_PREFIX_1',
    '标签0': '标签0',
    '标签1': '标签1',
    'Label0': 'Label0',
    'Label1': 'Label1'
}

for root, _, files in os.walk('.'):
    if '.venv' in root or '.git' in root or '.vscode' in root:
        continue
    for file in files:
        if file.endswith('.py'):
            path = os.path.join(root, file)
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()

            new_content = content
            for k, v in replacements.items():
                new_content = new_content.replace(k, v)
                
            if new_content != content:
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                print(f'Updated {path}')
