"""
Logs Branch Manager - Handles reading from and writing to the logs branch
"""
import os
import subprocess
import sys
from typing import List, Optional, Dict, Any


class LogsBranchManager:
    """Manages interaction with the logs branch for caching and logging"""
    
    def __init__(self, branch_name: str = "logs"):
        self.branch_name = branch_name
        self.temp_dir = "../temp_logs"
        
    def _run_git_command(self, command: List[str], check: bool = True) -> subprocess.CompletedProcess:
        """Run a git command and return the result"""
        try:
            result = subprocess.run(
                command, 
                capture_output=True, 
                text=True, 
                check=check,
                cwd=os.getcwd()
            )
            return result
        except subprocess.CalledProcessError as e:
            print(f"Git command failed: {' '.join(command)}")
            print(f"Error: {e.stderr}")
            raise
    
    def _branch_exists_remotely(self) -> bool:
        """Check if the logs branch exists on remote"""
        try:
            result = self._run_git_command([
                "git", "ls-remote", "--exit-code", "--heads", 
                "origin", self.branch_name
            ], check=False)
            return result.returncode == 0
        except Exception:
            return False
    
    def _ensure_temp_directory(self):
        """Create temporary directory if it doesn't exist"""
        if not os.path.exists(self.temp_dir):
            os.makedirs(self.temp_dir)
    
    def setup_git_config(self, name: str = "Genshin Auto Daily Bot", email: str = "action@github.com"):
        """Configure git user for commits"""
        self._run_git_command(["git", "config", "user.name", name])
        self._run_git_command(["git", "config", "user.email", email])
        print(f"Git configured: {name} <{email}>")
    
    def fetch_existing_files(self, file_patterns: List[str]) -> Dict[str, str]:
        """
        Fetch existing files from logs branch
        
        Args:
            file_patterns: List of file patterns to fetch (e.g., ['*.log', '*.txt'])
            
        Returns:
            Dict mapping filename to local path where file was saved
        """
        fetched_files = {}
        
        if not self._branch_exists_remotely():
            print(f"Branch '{self.branch_name}' does not exist remotely. Starting fresh.")
            return fetched_files
        
        # Store current working directory 
        original_cwd = os.getcwd()
        
        try:
            print(f"Fetching existing files from '{self.branch_name}' branch...")
            
            # Change to repo root if we're in utils/
            if os.path.basename(original_cwd) == 'utils':
                repo_root = os.path.dirname(original_cwd)
                os.chdir(repo_root)
                print(f"Changed to repo root: {repo_root}")
            
            # Fetch the logs branch
            self._run_git_command(["git", "fetch", "origin", f"{self.branch_name}:{self.branch_name}"])
            
            # Get current branch
            current_branch_result = self._run_git_command(["git", "branch", "--show-current"])
            current_branch = current_branch_result.stdout.strip()
            
            # Checkout logs branch temporarily
            self._run_git_command(["git", "checkout", self.branch_name])
            
            # Create temp directory
            self._ensure_temp_directory()
            
            # Copy matching files to temp directory
            for pattern in file_patterns:
                try:
                    # Find files matching pattern in logs directory
                    find_result = self._run_git_command([
                        "git", "ls-files", f"logs/{pattern}"
                    ], check=False)
                    
                    if find_result.returncode == 0:
                        files = [f.strip() for f in find_result.stdout.split('\n') if f.strip()]
                        for file_path in files:
                            if os.path.exists(file_path):
                                temp_path = os.path.join(self.temp_dir, os.path.basename(file_path))
                                # Copy file to temp directory
                                with open(file_path, 'r', encoding='utf-8') as src:
                                    content = src.read()
                                with open(temp_path, 'w', encoding='utf-8') as dst:
                                    dst.write(content)
                                fetched_files[os.path.basename(file_path)] = temp_path
                                print(f"Fetched: {file_path} -> {temp_path}")
                except Exception as e:
                    print(f"Warning: Could not fetch files for pattern '{pattern}': {e}")
            
            # Return to original branch
            self._run_git_command(["git", "checkout", current_branch])
            
            print(f"Successfully fetched {len(fetched_files)} files from logs branch")
            return fetched_files
            
        except Exception as e:
            print(f"Error fetching files from logs branch: {e}")
            # Try to return to main branch if something went wrong
            try:
                self._run_git_command(["git", "checkout", "main"], check=False)
            except:
                pass
            return {}
        finally:
            # Restore original working directory
            try:
                os.chdir(original_cwd)
            except:
                pass
    
    def restore_files_to_working_directory(self, fetched_files: Dict[str, str], target_dir: str = "."):
        """
        Restore fetched files to working directory
        
        Args:
            fetched_files: Dict from fetch_existing_files()
            target_dir: Directory to restore files to (relative to repo root)
        """
        # Store current working directory
        original_cwd = os.getcwd()
        
        try:
            # Change to repo root if we're in utils/
            if os.path.basename(original_cwd) == 'utils':
                repo_root = os.path.dirname(original_cwd)
                os.chdir(repo_root)
                print(f"Changed to repo root for file restoration: {repo_root}")
            
            for filename, temp_path in fetched_files.items():
                try:
                    target_path = os.path.join(target_dir, filename)
                    if os.path.exists(temp_path):
                        with open(temp_path, 'r', encoding='utf-8') as src:
                            content = src.read()
                        with open(target_path, 'w', encoding='utf-8') as dst:
                            dst.write(content)
                        print(f"Restored: {filename} to {target_path}")
                except Exception as e:
                    print(f"Warning: Could not restore {filename}: {e}")
        finally:
            # Restore original working directory
            try:
                os.chdir(original_cwd)
            except:
                pass
    
    def cleanup_temp_files(self):
        """Clean up temporary files"""
        try:
            if os.path.exists(self.temp_dir):
                import shutil
                shutil.rmtree(self.temp_dir)
                print("Cleaned up temporary files")
        except Exception as e:
            print(f"Warning: Could not clean up temp files: {e}")
    
    def create_or_switch_to_logs_branch(self):
        """Create logs branch if it doesn't exist, or switch to it and clean it"""
        try:
            # Get current branch to return to later
            current_branch_result = self._run_git_command(["git", "branch", "--show-current"])
            current_branch = current_branch_result.stdout.strip()
            
            if self._branch_exists_remotely():
                print(f"Switching to existing '{self.branch_name}' branch...")
                self._run_git_command(["git", "fetch", "origin", f"{self.branch_name}:{self.branch_name}"])
                self._run_git_command(["git", "checkout", self.branch_name])
                
                # Clean existing files but preserve logs directory
                print("Cleaning existing files (preserving logs directory)...")
                try:
                    # Get all tracked files and remove only those NOT in logs/ directory
                    result = self._run_git_command(["git", "ls-files"], check=False)
                    if result.returncode == 0:
                        files = [f.strip() for f in result.stdout.strip().split('\n') if f.strip()]
                        files_to_remove = []
                        for file_path in files:
                            if file_path and not file_path.startswith('logs/'):
                                files_to_remove.append(file_path)
                        
                        # Remove files individually to avoid affecting logs/ directory
                        for file_path in files_to_remove:
                            self._run_git_command(["git", "rm", "-f", file_path], check=False)
                            print(f"Removed: {file_path}")
                        
                        print(f"Preserved logs directory, removed {len(files_to_remove)} other files")
                except Exception as e:
                    print(f"Warning during cleanup: {e}")
                    pass  # Some files might not exist, that's OK
                
            else:
                print(f"Creating new '{self.branch_name}' branch...")
                self._run_git_command(["git", "checkout", "--orphan", self.branch_name])
                
                # Clear all files for clean logs branch  
                try:
                    self._run_git_command(["git", "rm", "-rf", "."], check=False)
                except:
                    pass
            
            # Ensure logs directory exists
            if not os.path.exists("logs"):
                os.makedirs("logs")
                print("Created logs directory")
            
            # Always create/recreate README for logs branch  
            readme_content = """# Logs Branch

This branch contains automated logs from Genshin Auto Daily actions.

- Generated automatically by GitHub Actions
- Contains check-in and redemption logs
- Do not manually edit files here

## Structure:
- `logs/genshin-checkin.log` - Daily check-in logs
- `logs/redeemed_codes.txt` - Cache of redeemed promotion codes
"""
            with open("README.md", 'w', encoding='utf-8') as f:
                f.write(readme_content)
            
            print("Logs branch prepared with clean state")
                
        except Exception as e:
            print(f"Error creating/switching to logs branch: {e}")
            raise
    
    def commit_and_push_logs(self, files_to_commit: List[str], commit_message: Optional[str] = None):
        """
        Commit and push log files to logs branch
        
        Args:
            files_to_commit: List of files to commit (relative paths from repo root)
            commit_message: Custom commit message
        """
        # Store current working directory (should be utils/)
        original_cwd = os.getcwd()
        temp_backup_dir = None
        
        try:
            print(f"Current working directory: {original_cwd}")
            
            # Change to repo root (parent of utils)
            repo_root = os.path.dirname(original_cwd)
            os.chdir(repo_root)
            print(f"Changed to repo root: {repo_root}")
            
            # Step 1: Backup files that need to be committed to temp directory
            temp_backup_dir = "temp_commit_backup"
            if os.path.exists(temp_backup_dir):
                import shutil
                shutil.rmtree(temp_backup_dir)
            os.makedirs(temp_backup_dir)
            
            files_backed_up = {}
            for file_path in files_to_commit:
                if os.path.exists(file_path):
                    backup_path = os.path.join(temp_backup_dir, os.path.basename(file_path))
                    with open(file_path, 'r', encoding='utf-8') as src:
                        content = src.read()
                    with open(backup_path, 'w', encoding='utf-8') as dst:
                        dst.write(content)
                    files_backed_up[file_path] = backup_path
                    print(f"Backed up: {file_path} -> {backup_path}")
            
            # Step 2: Remove untracked files that would conflict with checkout
            for file_path in files_to_commit:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    print(f"Removed conflicting file: {file_path}")
            
            # Step 3: Create/switch to logs branch (now clean)
            self.create_or_switch_to_logs_branch()
            
            # Step 4: Copy files from backup to logs branch
            files_copied = []
            for original_path, backup_path in files_backed_up.items():
                target_filename = os.path.basename(original_path)
                # Save files to logs directory
                target_path = os.path.join("logs", target_filename)
                
                if os.path.exists(backup_path):
                    try:
                        with open(backup_path, 'r', encoding='utf-8') as src:
                            content = src.read()
                        with open(target_path, 'w', encoding='utf-8') as dst:
                            dst.write(content)
                        files_copied.append(target_path)
                        print(f"Copied to logs branch: {backup_path} -> {target_path}")
                    except Exception as e:
                        print(f"Error copying {backup_path}: {e}")
            
            if not files_copied and not os.path.exists("README.md"):
                print("No files to commit")
                return
            
            # Step 5: Add and commit files
            files_to_add = ["README.md"] + files_copied
            for file_to_add in files_to_add:
                if os.path.exists(file_to_add):
                    self._run_git_command(["git", "add", file_to_add])
                    print(f"Added to staging: {file_to_add}")
            
            if commit_message is None:
                from datetime import datetime
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')
                commit_message = f"Update logs - {timestamp}"
            
            try:
                self._run_git_command(["git", "commit", "-m", commit_message])
                print(f"Committed changes: {commit_message}")
            except subprocess.CalledProcessError:
                print("No changes to commit")
            
            # Step 6: Push to remote
            try:
                self._run_git_command(["git", "push", "origin", self.branch_name])
                print(f"Pushed changes to '{self.branch_name}' branch")
            except subprocess.CalledProcessError:
                # Try setting upstream
                self._run_git_command(["git", "push", "--set-upstream", "origin", self.branch_name])
                print(f"Pushed changes to '{self.branch_name}' branch (set upstream)")
                
        except Exception as e:
            print(f"Error committing and pushing logs: {e}")
            raise
        finally:
            # Step 7: Always return to main branch
            try:
                self._run_git_command(["git", "checkout", "main"], check=False)
                print("Returned to main branch")
            except:
                pass
            
            # Step 8: Restore files from backup to working directory
            if temp_backup_dir and os.path.exists(temp_backup_dir):
                try:
                    for original_path, backup_path in files_backed_up.items():
                        if os.path.exists(backup_path):
                            with open(backup_path, 'r', encoding='utf-8') as src:
                                content = src.read()
                            with open(original_path, 'w', encoding='utf-8') as dst:
                                dst.write(content)
                            print(f"Restored: {backup_path} -> {original_path}")
                    
                    # Clean up backup directory
                    import shutil
                    shutil.rmtree(temp_backup_dir)
                    print("Cleaned up backup directory")
                except Exception as e:
                    print(f"Warning: Could not restore files from backup: {e}")
            
            # Step 9: Restore original working directory
            try:
                os.chdir(original_cwd)
                print(f"Restored working directory: {original_cwd}")
            except:
                pass


def main():
    """Command line interface for logs manager"""
    if len(sys.argv) < 2:
        print("Usage: python logs_manager.py <command> [args...]")
        print("Commands:")
        print("  fetch <patterns>  - Fetch files matching patterns (e.g., '*.log,*.txt')")
        print("  commit <files>    - Commit files to logs branch (e.g., 'file1.log,file2.txt')")
        return
    
    manager = LogsBranchManager()
    command = sys.argv[1]
    
    if command == "fetch":
        if len(sys.argv) > 2:
            patterns = sys.argv[2].split(',')
        else:
            patterns = ['*.log', '*.txt']
        
        manager.setup_git_config()
        fetched = manager.fetch_existing_files(patterns)
        print(f"Fetched files: {list(fetched.keys())}")
        manager.restore_files_to_working_directory(fetched)
        manager.cleanup_temp_files()
        
    elif command == "commit":
        if len(sys.argv) > 2:
            files = sys.argv[2].split(',')
        else:
            files = ['genshin-checkin.log', 'redeemed_codes.txt']
        
        manager.setup_git_config()
        manager.commit_and_push_logs(files)
        
    else:
        print(f"Unknown command: {command}")


if __name__ == "__main__":
    main()
