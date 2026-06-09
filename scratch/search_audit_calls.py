import sys
import os
sys.path.append(os.getcwd())

# Search files for run_plan_audit, skipping standard heavy directories
skip_dirs = {".git", "node_modules", "venv", ".next", "__pycache__"}
for root, dirs, files in os.walk("."):
    dirs[:] = [d for d in dirs if d not in skip_dirs]
    for file in files:
        if file.endswith(".py"):
            path = os.path.join(root, file)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                    if "run_plan_audit" in content:
                        print(f"Found in {path}")
            except Exception as e:
                print("Error reading:", path, e)
