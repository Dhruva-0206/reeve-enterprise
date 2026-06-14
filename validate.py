"""
Validation script to ensure all components are properly set up
Run this after installation to verify system readiness
"""
import sys
import os
import json
from pathlib import Path


def validate_files():
    """Check all required files exist"""
    required_files = [
        "config.py",
        "models.py",
        "memory_manager.py",
        "ingester_github.py",
        "ingester_jira.py",
        "ingester_slack.py",
        "orchestrator.py",
        "main.py",
        "cli.py",
        "requirements.txt",
        "README.md",
        ".env.example",
    ]
    
    print("Checking files...")
    missing = []
    for f in required_files:
        if Path(f).exists():
            print(f"  ✓ {f}")
        else:
            print(f"  ✗ {f}")
            missing.append(f)
    
    return len(missing) == 0


def validate_imports():
    """Check all imports work"""
    print("\nChecking imports...")
    imports = {
        "config": ["reeve_config", "github_config", "jira_config", "slack_config"],
        "models": ["NormalizedEvent", "Entity", "InvestigationResult"],
        "memory_manager": ["ReeveMemoryManager"],
        "ingester_github": ["GitHubIngester"],
        "ingester_jira": ["JiraIngester"],
        "ingester_slack": ["SlackIngester"],
        "orchestrator": ["DataOrchestrator"],
    }
    
    all_ok = True
    for module, items in imports.items():
        try:
            mod = __import__(module)
            for item in items:
                if hasattr(mod, item):
                    print(f"  ✓ {module}.{item}")
                else:
                    print(f"  ✗ {module}.{item} - not found")
                    all_ok = False
        except Exception as e:
            print(f"  ✗ {module} - {e}")
            all_ok = False
    
    return all_ok


def validate_env():
    """Check environment configuration"""
    print("\nChecking environment...")
    env_path = Path(".env")
    
    if not env_path.exists():
        print("  ✗ .env file not found")
        return False
    
    print("  ✓ .env file exists")
    
    # Check for sensitive info
    with open(".env") as f:
        content = f.read()
        if "sk-" in content and "your-" in content:
            print("  ⚠ .env contains template values - fill in your actual keys")
            return True
        elif "your-" in content or "example" in content.lower():
            print("  ⚠ .env contains placeholder values")
            return True
    
    print("  ✓ .env appears configured")
    return True


def validate_config():
    """Test configuration loading"""
    print("\nValidating configuration...")
    try:
        from config import (
            reeve_config,
            github_config,
            jira_config,
            slack_config,
            validate_configuration,
        )
        
        status = validate_configuration()
        for source, configured in status.items():
            marker = "✓" if configured else "✗"
            print(f"  {marker} {source}")
        
        return status["reeve"]  # Reeve is required
    except Exception as e:
        print(f"  ✗ Error loading config: {e}")
        return False


def test_api_connections():
    """Test connections to APIs (if configured)"""
    print("\nTesting API connections...")
    
    results = {}
    
    # Test GitHub
    try:
        from config import github_config
        if github_config.is_configured:
            from ingester_github import GitHubIngester
            ingester = GitHubIngester()
            print("  ✓ GitHub API connection successful")
            results["github"] = True
        else:
            print("  ⊘ GitHub not configured")
            results["github"] = None
    except Exception as e:
        print(f"  ✗ GitHub API error: {str(e)[:50]}")
        results["github"] = False
    
    # Test Jira
    try:
        from config import jira_config
        if jira_config.is_configured:
            from ingester_jira import JiraIngester
            ingester = JiraIngester()
            print("  ✓ Jira API connection successful")
            results["jira"] = True
        else:
            print("  ⊘ Jira not configured")
            results["jira"] = None
    except Exception as e:
        print(f"  ✗ Jira API error: {str(e)[:50]}")
        results["jira"] = False
    
    # Test Slack
    try:
        from config import slack_config
        if slack_config.is_configured:
            from ingester_slack import SlackIngester
            ingester = SlackIngester()
            print("  ✓ Slack API connection successful")
            results["slack"] = True
        else:
            print("  ⊘ Slack not configured")
            results["slack"] = None
    except Exception as e:
        print(f"  ✗ Slack API error: {str(e)[:50]}")
        results["slack"] = False
    
    # Test Reeve
    try:
        from config import reeve_config
        if reeve_config.api_key:
            from reeve import query_memory
            print("  ✓ Reeve configured")
            results["reeve"] = True
        else:
            print("  ✗ Reeve API key missing")
            results["reeve"] = False
    except Exception as e:
        print(f"  ✗ Reeve error: {str(e)[:50]}")
        results["reeve"] = False
    
    return results


def main():
    print("=" * 60)
    print("Enterprise Knowledge Investigator - Validation")
    print("=" * 60 + "\n")
    
    checks = {
        "Files": validate_files(),
        "Imports": validate_imports(),
        "Environment": validate_env(),
        "Configuration": validate_config(),
    }
    
    print("\n" + "-" * 60)
    print("API Connections:")
    api_results = test_api_connections()
    
    print("\n" + "=" * 60)
    print("Validation Summary")
    print("=" * 60)
    
    for check, result in checks.items():
        marker = "✓" if result else "✗"
        print(f"{marker} {check}")
    
    # Check at least one source is configured
    sources_ok = any(v for k, v in api_results.items() if k != "reeve" and v is not False)
    reeve_ok = api_results.get("reeve", False)
    
    print("\n" + "-" * 60)
    if all(checks.values()) and reeve_ok and sources_ok:
        print("✓ System is ready for operation!")
        print("\nNext steps:")
        print("  1. python cli.py status check     # Verify configuration")
        print("  2. python cli.py ingest all       # Ingest data from sources")
        print("  3. python cli.py server start     # Start API server")
        print("  4. Visit http://localhost:8000/docs")
        return 0
    else:
        print("✗ System validation failed")
        if not reeve_ok:
            print("\n⚠ Reeve API key not configured")
            print("  Get API key: https://mcp.reeve.co.in")
        if not sources_ok:
            print("\n⚠ No data sources configured")
            print("  Configure at least one of: GitHub, Jira, Slack")
        return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"\n✗ Validation error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
