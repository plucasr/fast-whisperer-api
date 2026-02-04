import os
from github import Github, GithubException
from dotenv import load_dotenv

load_dotenv()

# Initialize PyGithub
g = Github(os.getenv("GITHUB_ACCESS_TOKEN"))

def get_readme_content(repo_url: str) -> str:
    """
    Fetches the content of the README.md file from a GitHub repository.
    
    Args:
        repo_url: The full URL of the repository (e.g., "https://github.com/owner/repo")
        
    Returns:
        The content of the README.md file, or an empty string if not found.
    """
    try:
        # Extract owner/repo from URL
        # Typical URL: https://github.com/owner/repo
        parts = repo_url.strip("/").split("/")
        if len(parts) < 2:
            return "Error: Invalid GitHub URL"
            
        full_name = f"{parts[-2]}/{parts[-1]}"
        repo = g.get_repo(full_name)
        
        # Try common README names
        for name in ["README.md", "readme.md", "README.txt", "README"]:
            try:
                content_file = repo.get_contents(name)
                return content_file.decoded_content.decode("utf-8")
            except GithubException:
                continue
                
        return "Error: No README found"
        
    except Exception as e:
        return f"Error fetching README: {str(e)}"

def list_repo_files(repo_url: str, extensions: list = None) -> list:
    """
    Lists files in a repository that match specific extensions.
    
    Args:
        repo_url: The full URL of the repository.
        extensions: A list of file extensions to filter by (e.g., ['.json', '.sqlite']).
        
    Returns:
        A list of dicts containing file metadata (name, url, size, type).
    """
    if extensions is None:
        extensions = []
        
    found_files = []
    
    try:
        parts = repo_url.strip("/").split("/")
        if len(parts) < 2:
            return []
            
        full_name = f"{parts[-2]}/{parts[-1]}"
        repo = g.get_repo(full_name)
        
        # Recursive function to traverse contents
        def traverse(path=""):
            contents = repo.get_contents(path)
            while contents:
                file_content = contents.pop(0)
                if file_content.type == "dir":
                    try: 
                        contents.extend(repo.get_contents(file_content.path))
                    except: 
                        pass # Ignore dirs we can't access
                else:
                    # Check extension
                    if any(file_content.name.endswith(ext) for ext in extensions):
                        found_files.append({
                            "name": file_content.name,
                            "download_url": file_content.download_url,
                            "size": file_content.size,
                            "path": file_content.path,
                            "type": file_content.name.split(".")[-1]
                        })
                        
        traverse()
        return found_files

    except Exception as e:
        print(f"Error inspecting repo {repo_url}: {e}")
        return []
