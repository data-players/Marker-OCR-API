#!/usr/bin/env python3
"""Test script to see what Marker actually outputs."""
import sys
import logging

# Setup logging to see what Marker logs
logging.basicConfig(
    level=logging.DEBUG,
    format='%(levelname)s - %(name)s - %(message)s',
    stream=sys.stdout
)

# Import Marker
from marker.converters.pdf import PdfConverter
from marker.config.parser import ConfigParser

# Enable Marker's internal logging
marker_logger = logging.getLogger('marker')
marker_logger.setLevel(logging.DEBUG)

print("=" * 80)
print("TEST: Marker output capture")
print("=" * 80)

# Test file
test_file = "./data/uploads/dummy.pdf"  # Dummy PDF de test

try:
    print("\n1. Creating PdfConverter...")
    config_parser = ConfigParser({
        "output_format": "json",
        "force_ocr": False,
        "paginate_output": False
    })
    converter = PdfConverter(
        config=config_parser.generate_config_dict(),
        artifact_dict=None,
        processor_list=config_parser.get_processors(),
        renderer=config_parser.get_renderer()
    )
    
    print("\n2. Converting PDF (watch for tqdm/logs)...")
    print("-" * 80)
    rendered = converter(test_file)
    print("-" * 80)
    
    print(f"\n3. Done! Output type: {type(rendered)}")
    print(f"   Content length: {len(str(rendered)) if rendered else 0}")
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
print("END OF TEST")
print("=" * 80)

