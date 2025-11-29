#!/usr/bin/env python3
"""
Standalone diagnostic tool for troubleshooting quiz problems
Run this separately from your main API
"""

import asyncio
import json
import sys
from diagnostic_tool import diagnostic_tool

async def main():
    if len(sys.argv) != 4:
        print("Usage: python run_diagnosis.py <email> <secret> <url>")
        print("Example: python run_diagnosis.py test@example.com mysecret https://example.com/quiz-123")
        return
    
    email = sys.argv[1]
    secret = sys.argv[2]
    url = sys.argv[3]
    
    print(f"🔍 Diagnosing quiz: {url}")
    print("=" * 60)
    
    diagnosis = await diagnostic_tool.diagnose_quiz_problem(url, email, secret)
    
    # Print formatted results
    print(f"📋 URL: {diagnosis['url']}")
    print()
    
    # Print steps
    for step in diagnosis['steps']:
        print(f"🔧 {step['step'].upper()}: {'✅ SUCCESS' if step['success'] else '❌ FAILED'}")
        
        if not step['success']:
            print(f"   Error: {step['details'].get('error', 'Unknown error')}")
        else:
            # Print relevant details for each step
            if step['step'] == 'scraping':
                print(f"   Status: {step['details'].get('status_code')}")
                print(f"   Content Type: {step['details'].get('content_type')}")
                print(f"   Has JS: {step['details'].get('has_js_content', False)}")
                print(f"   Text Preview: {step['details'].get('visible_text', '')[:200]}...")
                
            elif step['step'] == 'parsing':
                instructions = step['instructions']
                print(f"   Question: {instructions.get('question', 'Not found')}")
                print(f"   Data Source: {instructions.get('data_source', 'Not found')}")
                print(f"   Submit URL: {instructions.get('submit_url', 'Not found')}")
                print(f"   Answer Format: {instructions.get('answer_format', 'Not found')}")
                
            elif step['step'] == 'data_source_analysis':
                print(f"   Resolved URL: {step['details'].get('resolved_url')}")
                print(f"   Status: {step['details'].get('status_code')}")
                secrets = step['details'].get('potential_secrets', [])
                if secrets:
                    print(f"   🔑 Potential Secrets Found: {secrets}")
                else:
                    print(f"   ❌ No secrets found in content")
                print(f"   Content Preview: {step['details'].get('content_preview', '')[:200]}...")
                
            elif step['step'] == 'question_analysis':
                print(f"   Answer Type: {step['details'].get('answer_type')}")
                print(f"   Expected Action: {step['details'].get('expected_action')}")
                
            elif step['step'] == 'submission_test':
                print(f"   Submission Status: {step['details'].get('submission_status')}")
                print(f"   Correct: {step['details'].get('correct')}")
                print(f"   Reason: {step['details'].get('reason')}")
                if step['details'].get('next_url'):
                    print(f"   Next URL: {step['details'].get('next_url')}")
        
        print()
    
    # Print recommendations
    if diagnosis['recommendations']:
        print("💡 RECOMMENDATIONS:")
        for rec in diagnosis['recommendations']:
            print(f"   • {rec}")
    else:
        print("✅ No major issues detected")
    
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
