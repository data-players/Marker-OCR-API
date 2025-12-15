# Marker LLM Usage Documentation

## Overview

This document explains how Marker uses LLM (Large Language Models) internally, specifically the `use_llm` parameter and its integration with Gemini API.

## How Marker Uses LLM

### Architecture

Marker uses LLM as a **post-processing step**, not for direct PDF analysis:

1. **Primary Extraction Phase** (without LLM):
   - Marker performs OCR, layout detection, and table recognition using its internal models
   - Results are extracted as markdown/JSON format
   - This phase is always executed regardless of `use_llm` setting

2. **LLM Enhancement Phase** (if `use_llm=True`):
   - Marker sends the **already extracted text/markdown** to Gemini API
   - Gemini does NOT receive the original PDF images
   - Gemini receives the text/markdown output from Marker's primary extraction
   - LLM improves: table formatting, multi-page table merging, math formulas, form value extraction

### Key Points

- **Marker LLM does NOT "see" the PDF**: It only processes the text/markdown already extracted by Marker
- **Post-processing nature**: The LLM acts as a refinement step on Marker's output
- **Default LLM**: Marker uses Gemini (`gemini-2.0-flash`) by default
- **Configuration**: Requires `GOOGLE_API_KEY` environment variable

## Code References

### Marker Configuration

**File**: `backend/app/services/document_parser.py`

```python
    def _build_marker_config(
        self,
        output_format: str,
        force_ocr: bool = False,
        extract_images: bool = False,
        paginate_output: bool = False,
        language: Optional[str] = None
    ) -> dict:
```

**Lines**: 251-304

This function builds the Marker configuration dictionary. Currently, `use_llm` is **not** set in this implementation, meaning Marker runs without LLM enhancement.

### Marker Processing Pipeline

**File**: `backend/app/services/document_parser.py`

**Lines**: 475-611

The document processing flow:
1. Creates `ConfigParser` with configuration
2. Creates `PdfConverter` with processors and renderer
3. Calls `markdown_converter(file_path)` which executes Marker's pipeline
4. Marker internally processes through stages:
   - Recognizing layout
   - Running OCR error detection
   - Detecting bounding boxes
   - Recognizing tables
   - Extracting text

If `use_llm=True` were set, Marker would add an additional step after extraction to send results to Gemini for enhancement.

### Marker Library Imports

**File**: `backend/app/services/document_parser.py`

**Lines**: 19-24

```python
from marker.converters.pdf import PdfConverter
from marker.models import create_model_dict
from marker.output import text_from_rendered
from marker.renderers.json import JSONRenderer
from marker.config.parser import ConfigParser
```

These are the core Marker components. The `ConfigParser` is responsible for interpreting configuration options including `use_llm`.

## Configuration Parameters

### Current Implementation

The current implementation does **not** set `use_llm` in the Marker configuration:

```python
config = {
    "output_format": output_format,
}

        # OCR settings
        if force_ocr:
            config["force_ocr"] = True
        
        # Image extraction settings
        config["disable_image_extraction"] = not extract_images
        
        # Pagination settings - adds page separators in markdown output
        config["paginate_output"] = paginate_output
```

### To Enable LLM (Not Currently Used)

If `use_llm` were to be enabled, it would be added like this:

```python
config["use_llm"] = True  # Requires GOOGLE_API_KEY environment variable
```

**Note**: This is not implemented because:
- We perform our own LLM post-processing
- Avoids redundant LLM calls
- Provides more control over the enhancement process

## Marker LLM Capabilities

According to Marker documentation and benchmarks:

### What LLM Improves

1. **Table Recognition**: Score improves from 0.816 to 0.907 (with `use_llm`)
2. **Multi-page Table Merging**: Better handling of tables spanning multiple pages
3. **Math Formulas**: Improved inline formula formatting
4. **Form Extraction**: Better value extraction from forms
5. **Structure Refinement**: Overall content structuring improvements

### Performance Impact

- **Speed**: Adds processing time (API calls to Gemini)
- **Cost**: Requires Google API key and incurs API costs
- **Quality**: Significant improvement in table recognition (benchmark data)

## Alternative: Custom LLM Post-Processing

Since Marker's LLM only processes already-extracted text/markdown, we can achieve equivalent results with our own LLM post-processing:

### Advantages

1. **Full Control**: Custom prompts tailored to our needs
2. **LLM Choice**: Not limited to Gemini (can use OpenAI, Claude, local models, etc.)
3. **Cost Efficiency**: Single LLM pass instead of Marker LLM + custom LLM
4. **Flexibility**: Can focus on specific improvements we need

### Implementation Location

The post-processing LLM would be implemented after Marker extraction:

**File**: `backend/app/services/document_parser.py`

**Lines**: 644-661 (result preparation)

After Marker returns results, we could add a post-processing step that:
1. Takes the markdown/JSON output from Marker
2. Sends it to our chosen LLM with custom prompts
3. Returns enhanced results

## References

- [Marker GitHub Repository](https://github.com/datalab-to/marker)
- Marker Documentation: LLM usage requires `GOOGLE_API_KEY` environment variable
- Benchmarks show `use_llm` improves table recognition from 0.816 to 0.907 score
- Marker uses Gemini by default but can be configured for other LLMs (Ollama, etc.)

## Decision Rationale

**Why we don't use Marker's `use_llm`:**

1. Marker's LLM processes text already extracted by Marker
2. We perform our own LLM post-processing with more control
3. Avoids redundant LLM API calls and costs
4. Provides flexibility in LLM choice and prompt engineering

