import os
import sys

def generate_tree(start_path, ignore_dirs):
    for root, dirs, files in os.walk(start_path, topdown=True):
        dirs[:] = [d for d in dirs if d not in ignore_dirs]
        level = root.replace(start_path, '').count(os.sep)
        indent = '    ' * level
        dir_name = os.path.basename(root)
        if level == 0:
            print(f'{dir_name}')
        else:
            print(f'{indent}+---{dir_name}')
        
        sub_indent = '    ' * (level + 1)
        for f in files:
            print(f'{sub_indent}|   {f}')

if __name__ == "__main__":
    path_to_tree = sys.argv[1]
    ignore_list = ['__pycache__', '.git']
    generate_tree(path_to_tree, ignore_list)