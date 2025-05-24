import os

# Root directory of the project
root_dir = "."

# Output file to save all code
output_file = "full_codebase_dump.txt"

def is_code_file(filename):
    return filename.endswith(('.py', '.sh', '.js', '.ts', '.json', '.yml', '.yaml', '.Dockerfile', 'Dockerfile'))

# Crawl and extract code
code_dump = []
for dirpath, dirnames, filenames in os.walk(root_dir):
    for filename in filenames:
        if is_code_file(filename):
            filepath = os.path.join(dirpath, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as file:
                    content = file.read()
                    code_dump.append(f"\n\n# {'='*20} {filepath} {'='*20}\n\n{content}")
            except Exception as e:
                code_dump.append(f"\n\n# {'='*20} {filepath} (Failed to read: {e}) {'='*20}\n\n")

# Write to a single file
with open(output_file, 'w', encoding='utf-8') as out:
    out.write("\n".join(code_dump))

output_file
