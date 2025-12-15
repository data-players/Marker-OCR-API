#!/usr/bin/env python3
"""
Test script to check Marker ConfigParser processors with different configurations.
This helps verify if table processors can be disabled.
"""

import sys
import os

# Add marker to path if needed
try:
    from marker.config.parser import ConfigParser
    from marker.models import create_model_dict
    
    print("=" * 80)
    print("Testing Marker ConfigParser processors")
    print("=" * 80)
    
    # Test 1: With pagination enabled
    print("\n1. Testing with paginate_output=True:")
    config1 = {
        "output_format": "markdown",
        "paginate_output": True
    }
    cp1 = ConfigParser(config1)
    processors1 = cp1.get_processors()
    print(f"   Processors ({len(processors1)}):")
    for p in processors1:
        print(f"     - {type(p).__name__}")
    
    # Test 2: Without pagination
    print("\n2. Testing with paginate_output=False:")
    config2 = {
        "output_format": "markdown",
        "paginate_output": False
    }
    cp2 = ConfigParser(config2)
    processors2 = cp2.get_processors()
    print(f"   Processors ({len(processors2)}):")
    for p in processors2:
        print(f"     - {type(p).__name__}")
    
    # Compare processors
    print("\n3. Comparison:")
    processor_names1 = [type(p).__name__ for p in processors1]
    processor_names2 = [type(p).__name__ for p in processors2]
    
    table_processors1 = [name for name in processor_names1 if 'table' in name.lower() or 'Table' in name]
    table_processors2 = [name for name in processor_names2 if 'table' in name.lower() or 'Table' in name]
    
    print(f"   Table processors with paginate_output=True: {table_processors1}")
    print(f"   Table processors with paginate_output=False: {table_processors2}")
    
    if len(table_processors1) == len(table_processors2):
        print("\n   ⚠️  Same number of table processors - Marker may still run table recognition")
    else:
        print(f"\n   ✅ Different number of table processors: {len(table_processors1)} vs {len(table_processors2)}")
    
    # Test 3: Check ConfigParser methods
    print("\n4. ConfigParser available methods:")
    methods = [m for m in dir(cp1) if not m.startswith('_') and callable(getattr(cp1, m))]
    print(f"   Methods: {', '.join(methods)}")
    
    # Test 4: Check if we can filter processors manually
    print("\n5. Testing manual processor filtering:")
    filtered_processors = [p for p in processors2 if 'table' not in type(p).__name__.lower()]
    print(f"   Original processors: {len(processors2)}")
    print(f"   Filtered processors (no 'table' in name): {len(filtered_processors)}")
    print(f"   Removed: {len(processors2) - len(filtered_processors)} processor(s)")
    
    print("\n" + "=" * 80)
    print("Conclusion:")
    print("=" * 80)
    if len(table_processors1) == len(table_processors2) and len(table_processors1) > 0:
        print("Marker includes table processors regardless of paginate_output setting.")
        print("This confirms that Marker always runs table recognition internally.")
        print("The paginate_output option only controls page separators in output, not table processing.")
    else:
        print("Marker may exclude some table processors when paginate_output=False.")
    
except ImportError as e:
    print(f"❌ Marker not available: {e}")
    print("This script must be run in a Docker container with Marker installed.")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

