import os
import glob
from pathlib import Path

def analyze_project_progress():
    print("=== LLM Analysis Quiz Project Progress Analysis ===\n")
    
    # Define project components and their files
    components = {
        "API Endpoint": ["app.py", "main.py", "simple_api.py", "answer_submitter.py"],
        "Data Sourcing": ["web_scraper.py", "quiz_parser.py"],
        "Data Processing": ["data_processor.py"],
        "Quiz Solving": ["quiz_solver.py"],
        "Diagnostic Tools": ["diagnostic_tool.py", "diagnostic_tool_js.py", "run_diagnosis.py"],
        "Testing & Progress": ["check_progress.py"],
        "Configuration": ["requirements.txt", ".gitignore", "README.md"]
    }
    
    total_files = 0
    found_files = 0
    
    print("📁 PROJECT STRUCTURE ANALYSIS:")
    print("-" * 50)
    
    for component, files in components.items():
        component_score = 0
        found = []
        missing = []
        
        for file_pattern in files:
            matches = glob.glob(f"**/{file_pattern}", recursive=True)
            if matches:
                component_score += 1
                found.extend(matches)
                found_files += len(matches)
            else:
                missing.append(file_pattern)
            total_files += 1
        
        status = "✅" if component_score >= len(files) * 0.7 else "🔄" if component_score > 0 else "❌"
        print(f"{status} {component}: {component_score}/{len(files)} files")
        if found:
            print(f"   Found: {', '.join(found)}")
        if missing:
            print(f"   Missing: {', '.join(missing)}")
        print()
    
    # Calculate overall progress
    overall_progress = (found_files / total_files) * 100 if total_files > 0 else 0
    
    print("📊 OVERALL PROGRESS METRICS:")
    print("-" * 50)
    print(f"Total files found: {found_files}/{total_files}")
    print(f"Overall completion: {overall_progress:.1f}%")
    
    # Check critical files
    print("\n🔍 CRITICAL FILES CHECK:")
    critical_files = {
        "API Entry Point": "app.py",
        "Main Requirements": "requirements.txt", 
        "Git Configuration": ".gitignore",
        "Documentation": "README.md"
    }
    
    for desc, file in critical_files.items():
        if os.path.exists(file):
            print(f"✅ {desc}: {file}")
        else:
            print(f"❌ {desc}: {file} - MISSING")
    
    # File sizes analysis
    print(f"\n📏 CODEBASE SIZE:")
    py_files = glob.glob("**/*.py", recursive=True)
    total_lines = 0
    for py_file in py_files:
        try:
            with open(py_file, 'r') as f:
                total_lines += len(f.readlines())
        except:
            pass
    
    print(f"Python files: {len(py_files)}")
    print(f"Total lines of code: {total_lines}")
    
    # Next steps recommendation
    print(f"\n🎯 RECOMMENDED NEXT STEPS:")
    if overall_progress < 50:
        print("1. Focus on core API endpoint completion")
        print("2. Implement missing data processing modules") 
        print("3. Add LLM integration")
    elif overall_progress < 80:
        print("1. Enhance error handling and logging")
        print("2. Add comprehensive testing")
        print("3. Improve documentation")
    else:
        print("1. Performance optimization")
        print("2. Security hardening")
        print("3. Deployment preparation")

if __name__ == "__main__":
    analyze_project_progress()
