#!/usr/bin/env python
import sys
import subprocess
import os

def check_environment():
    """Check if the environment is properly set up"""
    print(f"Running with Python {sys.version}")
    
    # Check virtual environment
    in_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
    if not in_venv:
        print("WARNING: Not running in a virtual environment!")
    else:
        print(f"✅ Virtual environment active: {sys.prefix}")
    
    # Try to import fitz
    try:
        import fitz
        print(f"✅ PyMuPDF is installed (fitz module found at {fitz.__file__})")
        return True
    except ImportError:
        print("❌ PyMuPDF is not installed in this Python environment")
        
        # Try to find where it might be installed
        try:
            result = subprocess.run(
                ["pip", "show", "pymupdf"], 
                capture_output=True,
                text=True
            )
            if "Location:" in result.stdout:
                location = [line for line in result.stdout.split('\n') if "Location:" in line][0]
                print(f"PyMuPDF may be installed at: {location}")
                
                # Check if it's in another Python version
                if sys.prefix not in location:
                    print("\n⚠️ VERSION MISMATCH DETECTED!")
                    print(f"You're running Python from: {sys.prefix}")
                    print(f"But PyMuPDF is installed in: {location}")
                    
                    # Try to determine the Python version where it's installed
                    if "/python3." in location:
                        py_version = location.split("/python3.")[1].split("/")[0]
                        print(f"\nTry running your script with Python 3.{py_version}:")
                        print(f"python3.{py_version} main.py")
                    
                    # Suggest using the venv's Python
                    venv_python = os.path.join(os.path.dirname(sys.executable), "python")
                    if os.path.exists(venv_python):
                        print("\nOR use the virtual environment's Python directly:")
                        print(f"{venv_python} main.py")
            else:
                print("PyMuPDF is not installed by pip in any Python environment")
                
            # Suggest installing
            print("\nTo install PyMuPDF in this environment:")
            print("pip install PyMuPDF")
        except Exception as e:
            print(f"Error checking pip: {e}")
        
        return False

def check_other_dependencies():
    """Check other important dependencies"""
    dependencies = {
        "langchain": "LangChain",
        "crewai": "CrewAI",
        "langgraph": "LangGraph",
        "requests": "Requests",
        "dotenv": "python-dotenv"
    }
    
    for module, name in dependencies.items():
        try:
            exec(f"import {module}")
            print(f"✅ {name} is installed")
        except ImportError:
            print(f"❌ {name} is NOT installed")
        
if __name__ == "__main__":
    print("=== Environment Check ===\n")
    pdf_support = check_environment()
    
    print("\n=== Other Dependencies ===")
    check_other_dependencies()
    
    print("\n=== Summary ===")
    if pdf_support:
        print("✅ PDF support is available")
        print("\nEnvironment looks good! You can run your application.")
    else:
        print("❌ PDF support is NOT available")
        print("\nPlease fix the environment issues before running your application.")
        
        # Suggest using simplified version
        print("\nAlternative: You can use the simplified version without PDF processing:")
        print("1. Edit src/utils/__init__.py to use attachment_fallback instead")
        print("2. Run the application with your current Python")