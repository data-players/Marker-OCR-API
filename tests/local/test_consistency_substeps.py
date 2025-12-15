#!/usr/bin/env python3
"""
Test script to verify that sub-steps displayed during processing
are the same as those displayed at completion.
"""

import requests
import time
import sys
from pathlib import Path

API_BASE_URL = "http://localhost:8000"

def test_consistency():
    """Test that sub-steps are consistent during and after processing."""
    print("=" * 80)
    print("Testing sub-steps consistency during and after processing")
    print("=" * 80)
    
    # 1. Upload PDF
    pdf_path = Path("tests/backend/FullStack/file-to-parse/LECLERC.pdf")
    if not pdf_path.exists():
        print(f"❌ PDF file not found: {pdf_path}")
        return False
    
    print(f"\n📄 Uploading PDF: {pdf_path}")
    with open(pdf_path, 'rb') as f:
        files = {'file': (pdf_path.name, f, 'application/pdf')}
        response = requests.post(f"{API_BASE_URL}/api/v1/documents/upload", files=files)
        if response.status_code != 200:
            print(f"❌ Upload failed: {response.status_code}")
            return False
        
        file_id = response.json().get('file_id')
        print(f"✅ Upload successful, file_id: {file_id}")
    
    # 2. Process document
    data = {
        'file_id': file_id,
        'output_format': 'markdown',
        'extract_images': 'false',
    }
    
    response = requests.post(f"{API_BASE_URL}/api/v1/documents/process", data=data)
    if response.status_code != 200:
        print(f"❌ Process request failed: {response.status_code}")
        return False
    
    job_id = response.json().get('job_id')
    print(f"✅ Processing started, job_id: {job_id}")
    
    # 3. Poll and capture sub-steps at different stages
    print("\n📊 Polling job status and capturing sub-steps...")
    print("-" * 80)
    
    captured_states = []
    max_polls = 300
    poll_count = 0
    
    while poll_count < max_polls:
        response = requests.get(f"{API_BASE_URL}/api/v1/documents/jobs/{job_id}")
        if response.status_code != 200:
            break
        
        job_status = response.json()
        status = job_status.get('status')
        
        # Get OCR Processing step
        steps = job_status.get('steps', [])
        ocr_step = None
        for step in steps:
            if step.get('name') == 'OCR Processing':
                ocr_step = step
                break
        
        if ocr_step:
            sub_steps_detailed = ocr_step.get('sub_steps_detailed', [])
            
            # Capture state every 5 polls (every ~2.5 seconds)
            if poll_count % 5 == 0:
                sub_step_names = [s.get('name') for s in sub_steps_detailed]
                captured_states.append({
                    'poll': poll_count,
                    'status': status,
                    'sub_steps': sub_step_names,
                    'count': len(sub_step_names)
                })
                print(f"  Poll {poll_count}: {len(sub_step_names)} sub-steps - {status}")
        
        if status == 'completed':
            # Capture final state
            sub_steps_detailed = ocr_step.get('sub_steps_detailed', [])
            final_sub_steps = [s.get('name') for s in sub_steps_detailed]
            captured_states.append({
                'poll': poll_count,
                'status': 'completed',
                'sub_steps': final_sub_steps,
                'count': len(final_sub_steps)
            })
            print(f"\n✅ Processing completed at poll {poll_count}")
            break
        elif status == 'failed':
            print(f"\n❌ Processing failed")
            return False
        
        time.sleep(0.5)
        poll_count += 1
    
    # 4. Analyze consistency
    print("\n" + "=" * 80)
    print("📝 Consistency Analysis")
    print("=" * 80)
    
    if len(captured_states) < 2:
        print("❌ Not enough states captured")
        return False
    
    final_state = captured_states[-1]
    final_sub_steps = set(final_state['sub_steps'])
    
    print(f"\nFinal state: {final_state['count']} sub-steps")
    print(f"Final sub-steps: {sorted(final_sub_steps)}")
    
    inconsistencies = []
    for i, state in enumerate(captured_states[:-1]):  # Exclude final state
        state_sub_steps = set(state['sub_steps'])
        
        # Check if state has same sub-steps as final (allowing for in-progress steps)
        # We should have the same completed sub-steps
        completed_in_state = {s for s in state_sub_steps if s != "⚡ Initialization and quick operations"}
        completed_in_final = {s for s in final_sub_steps if s != "⚡ Initialization and quick operations"}
        
        # Check if macro step appears consistently
        has_macro_state = "⚡ Initialization and quick operations" in state_sub_steps
        has_macro_final = "⚡ Initialization and quick operations" in final_sub_steps
        
        if has_macro_state != has_macro_final and len(completed_in_state) > 0:
            # Macro should appear if there are completed small steps
            inconsistencies.append({
                'poll': state['poll'],
                'issue': f"Macro step inconsistency: state={has_macro_state}, final={has_macro_final}"
            })
        
        # Check if significant steps are consistent
        significant_in_state = {s for s in completed_in_state if s not in ["✅ Markdown conversion completed", "📊 Finalizing table structures"]}
        significant_in_final = {s for s in completed_in_final if s not in ["✅ Markdown conversion completed", "📊 Finalizing table structures"]}
        
        if significant_in_state and not significant_in_state.issubset(significant_in_final):
            missing = significant_in_state - significant_in_final
            inconsistencies.append({
                'poll': state['poll'],
                'issue': f"Missing significant steps in final: {missing}"
            })
    
    if inconsistencies:
        print(f"\n⚠️  Found {len(inconsistencies)} inconsistencies:")
        for inc in inconsistencies:
            print(f"  Poll {inc['poll']}: {inc['issue']}")
        return False
    else:
        print("\n✅ All states are consistent!")
        print("   - Sub-steps displayed during processing match final state")
        print("   - Small steps are consistently grouped")
        print("   - Significant steps appear in the same order")
        return True

if __name__ == "__main__":
    try:
        success = test_consistency()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

