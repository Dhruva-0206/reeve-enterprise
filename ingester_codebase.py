"""
Codebase data ingester - reads local files and stores them in Reeve
"""
import os
from datetime import datetime
from models import NormalizedEvent, Entity

class CodebaseIngester:
    """Fetch and normalize GitHub repository codebase files"""

    def __init__(self):
        from config import github_config
        from github import Github
        if not github_config.is_configured:
            raise ValueError("GitHub configuration incomplete")
        self.client = Github(github_config.token)
        self.owner = github_config.owner
        self.repos = github_config.repos
        self.allowed_extensions = (".py", ".md", ".html", ".sh", ".txt", ".json", ".yml", ".yaml", ".js", ".ts", ".css")

    def ingest_files(self) -> list[NormalizedEvent]:
        """Read files from GitHub repo and create normalized events"""
        events = []
        for repo_name in self.repos:
            try:
                repo = self.client.get_user(self.owner).get_repo(repo_name)
                tree = repo.get_git_tree(repo.default_branch, recursive=True)
                
                for t in tree.tree:
                    if t.type == 'blob' and t.path.endswith(self.allowed_extensions):
                        try:
                            # Fetch file content
                            file_content = repo.get_contents(t.path)
                            content = file_content.decoded_content.decode("utf-8")
                            
                            entity = Entity(
                                id=f"github:file:{repo_name}/{t.path}",
                                type="file",
                                title=f"{repo_name}/{t.path}",
                                source="github",
                                url=file_content.html_url,
                                created_at=datetime.utcnow(),
                                updated_at=datetime.utcnow(),
                            )
                            
                            event = NormalizedEvent(
                                id=f"github:file_added:{repo_name}/{t.path}",
                                event_type="file_added",
                                entity=entity,
                                timestamp=datetime.utcnow(),
                                actor="system",
                                content=content,
                            )
                            events.append(event)
                        except Exception as e:
                            print(f"Error reading file {t.path}: {e}")
            except Exception as e:
                print(f"Error accessing repo {repo_name}: {e}")
                
        return events
