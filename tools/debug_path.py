import sys
import os

print("Initial sys.path:", sys.path)
print("CWD:", os.getcwd())

try:
    import src
    print("Successfully imported src")
    from src.infrastructure.xml_reader import XMLReader
    print("Successfully imported XMLReader")
except ImportError as e:
    print("ImportError:", e)
except Exception as e:
    print("Exception:", e)
