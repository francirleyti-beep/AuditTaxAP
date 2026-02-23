import os

path = "audit_data"
try:
    if not os.path.exists(path):
        os.makedirs(path)
        print(f"Created {path}")
    else:
        print(f"{path} already exists")
except Exception as e:
    print(f"Error: {e}")
