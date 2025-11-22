#!/usr/bin/env python3
"""
Quick script to check PandasAI version in your app.
Run with: poetry run python check_pandasai_version.py
"""

import sys

def get_pandasai_version():
    """Get PandasAI version using multiple methods."""
    methods = []
    
    # Method 1: importlib.metadata (Python 3.8+)
    try:
        import importlib.metadata
        version = importlib.metadata.version('pandasai')
        methods.append(("importlib.metadata", version))
    except Exception as e:
        methods.append(("importlib.metadata", f"Error: {e}"))
    
    # Method 2: pkg_resources (older Python)
    try:
        import pkg_resources
        version = pkg_resources.get_distribution('pandasai').version
        methods.append(("pkg_resources", version))
    except Exception:
        pass
    
    # Method 3: __version__ module
    try:
        from pandasai import __version__
        if isinstance(__version__, str):
            methods.append(("__version__ module", __version__))
        elif hasattr(__version__, '__version__'):
            methods.append(("__version__ module", __version__.__version__))
    except Exception as e:
        methods.append(("__version__ module", f"Error: {e}"))
    
    return methods


if __name__ == "__main__":
    print("🔍 Checking PandasAI Version...")
    print("=" * 50)
    
    methods = get_pandasai_version()
    
    for method_name, result in methods:
        print(f"{method_name:25} : {result}")
    
    # Get the first successful result
    successful = [m for m in methods if not str(m[1]).startswith("Error")]
    if successful:
        print("\n✅ PandasAI Version:", successful[0][1])
    else:
        print("\n❌ Could not determine version")
        sys.exit(1)

