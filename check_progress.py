import os
import glob

def check_project_progress():
    components = {
        "API Endpoint": ["api/", "app.py", "main.py", "endpoint.py"],
        "Data Sourcing": ["src/data_sourcing/", "scraping/", "data_acquisition/"],
        "Data Preparation": ["src/data_preparation/", "cleaning/", "preprocessing/"],
        "Data Analysis": ["src/data_analysis/", "analysis/"],
        "Data Visualization": ["src/data_visualization/", "visualization/"],
        "LLM Integration": ["src/llm/", "llm_integration/"],
        "Testing": ["tests/", "test_"],
        "Configuration": ["requirements.txt", "Dockerfile", "config.json", ".env"]
    }
    
    print("Project Progress Check")
    print("=" * 50)
    
    total_score = 0
    max_score = len(components) * 10
    
    for component, files in components.items():
        score = 0
        for pattern in files:
            if glob.glob(f"**/{pattern}", recursive=True):
                score += 2
        total_score += score
        status = "✅" if score > 5 else "🔄" if score > 0 else "❌"
        print(f"{status} {component}: {score}/10")
    
    progress = (total_score / max_score) * 100
    print(f"\nOverall Progress: {progress:.1f}%")
    
    # Check for critical files
    critical_files = ["requirements.txt", "README.md"]
    print("\nCritical Files:")
    for file in critical_files:
        if os.path.exists(file):
            print(f"✅ {file}")
        else:
            print(f"❌ {file}")

if __name__ == "__main__":
    check_project_progress()
