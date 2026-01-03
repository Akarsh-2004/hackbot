import os
import subprocess

REPOS = [
    "https://github.com/swisskyrepo/PayloadsAllTheThings.git",
    "https://github.com/carlospolop/hacktricks.git"
]

OUTPUT_DIR = "data/walkthroughs"

def sync_repos():
    """
    Clones or updates the targeted GitHub repositories to the output directory.
    Uses git command line tool.
    """
    if not os.path.exists("data"):
         os.makedirs("data")
         
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    for repo_url in REPOS:
        repo_name = repo_url.split("/")[-1].replace(".git", "")
        repo_path = os.path.join(OUTPUT_DIR, repo_name)
        
        if os.path.exists(repo_path):
            print(f"[+] Updating {repo_name}...")
            try:
                subprocess.run(["git", "-C", repo_path, "pull"], check=True)
            except subprocess.CalledProcessError as e:
                print(f"[-] Failed to update {repo_name}: {e}")
        else:
            print(f"[+] Cloning {repo_name}...")
            try:
                subprocess.run(["git", "clone", "--depth", "1", repo_url, repo_path], check=True)
            except subprocess.CalledProcessError as e:
                print(f"[-] Failed to clone {repo_name}: {e}")

if __name__ == "__main__":
    # Check if git is installed
    try:
        subprocess.run(["git", "--version"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except FileNotFoundError:
        print("[-] Git is not installed or not in PATH. Please install Git.")
        exit(1)
        
    sync_repos()
