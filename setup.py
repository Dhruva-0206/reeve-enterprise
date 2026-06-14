#!/usr/bin/env python3
"""
Setup script for Enterprise Knowledge Investigator
Validates configuration and prepares the system
"""
import os
import sys
from pathlib import Path

def check_python_version():
    """Verify Python 3.10+"""
    if sys.version_info < (3, 10):
        print("❌ Python 3.10+ required")
        sys.exit(1)
    print(f"✓ Python {sys.version.split()[0]}")


def check_dependencies():
    """Check if required packages are installed"""
    required = {
        "reeve": "Reeve",
        "fastapi": "FastAPI",
        "uvicorn": "Uvicorn",
        "pydantic": "Pydantic",
        "dotenv": "Python-dotenv",
        "github": "PyGithub",
        "jira": "Jira",
        "slack_sdk": "Slack SDK",
    }
    
    missing = []
    for module, name in required.items():
        try:
            __import__(module)
            print(f"✓ {name}")
        except ImportError:
            print(f"❌ {name}")
            missing.append(name)
    
    if missing:
        print(f"\nMissing packages: {', '.join(missing)}")
        print("Install with: pip install -r requirements.txt")
        return False
    return True


def check_env_file():
    """Check for .env file"""
    env_path = Path(".env")
    env_example = Path(".env.example")
    
    if env_path.exists():
        print("✓ .env file exists")
        return True
    else:
        print("❌ .env file not found")
        if env_example.exists():
            print(f"  Copy from template: cp .env.example .env")
        return False


def check_api_keys():
    """Check if required API keys are set"""
    from config import validate_configuration
    
    config = validate_configuration()
    
    print("\nAPI Configuration:")
    for source, configured in config.items():
        status = "✓" if configured else "❌"
        print(f"  {status} {source.upper()}")
    
    if config["reeve"]:
        print("\n✓ Reeve configured - Memory system ready")
    else:
        print("\n❌ Reeve not configured - Get API key from https://mcp.reeve.co.in")
        return False
    
    # At least one source should be configured
    sources_configured = any(config.get(k) for k in ["github", "jira", "slack"])
    if not sources_configured:
        print("⚠ No data sources configured")
        print("  Configure at least GitHub, Jira, or Slack in .env")
        return False
    
    return True


def create_directories():
    """Create necessary directories"""
    dirs = [
        "logs",
        "data",
        "cache",
    ]
    for d in dirs:
        Path(d).mkdir(exist_ok=True)
        print(f"✓ {d}/ exists")


def main():
    print("=" * 60)
    print("Enterprise Knowledge Investigator - Setup")
    print("=" * 60)
    
    print("\n1. Checking Python version...")
    check_python_version()
    
    print("\n2. Checking dependencies...")
    if not check_dependencies():
        sys.exit(1)
    
    print("\n3. Checking .env file...")
    if not check_env_file():
        print("\n⚠ Missing .env file. Creating from template...")
        if Path(".env.example").exists():
            with open(".env.example") as f:
                example = f.read()
            with open(".env", "w") as f:
                f.write(example)
            print("  .env created - Please fill in your API keys")
    
    print("\n4. Checking directories...")
    create_directories()
    
    print("\n5. Validating API configuration...")
    try:
        if not check_api_keys():
            print("\n⚠ Setup incomplete - Configure API keys in .env")
            sys.exit(1)
    except Exception as e:
        print(f"\n⚠ Error validating configuration: {e}")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("✓ Setup complete!")
    print("=" * 60)
    print("\nNext steps:")
    print("  1. Review your .env file configuration")
    print("  2. Test configuration: python cli.py status config")
    print("  3. Ingest data: python cli.py ingest all")
    print("  4. Start server: python cli.py server start")
    print("  5. Visit http://localhost:8000/docs for API docs")
    print("\nFor more info: https://localhost:8000 or python cli.py --help")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nSetup cancelled.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        sys.exit(1)
