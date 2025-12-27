#!/usr/bin/env python3
"""
Direct entry point for SpritePacker CLI.
Allows running 'python spritepacker.py [args]' without module installation.
"""

if __name__ == '__main__':
    import sys
    from pathlib import Path
    
    # Add parent directory to path so the package can be imported
    script_dir = Path(__file__).parent
    parent_dir = script_dir.parent
    if str(parent_dir) not in sys.path:
        sys.path.insert(0, str(parent_dir))
    
    # Import and run the main function from the package's __main__ module
    # This is done in __main__ block to avoid import side effects
    from SpritePacker.__main__ import main
    sys.exit(main())
