import os
import subprocess
import sys
from datetime import datetime
from typing import List, Optional, Dict


class LogsBranchManager:
    def __init__(self, branch_name: str = "logs"):
        self.branch_name = branch_name
        self.temp_dir = "../temp_logs"
        
    def _run_git_command(self, command: List[str], check: bool = True) -> subprocess.CompletedProcess:
        try:
            return subprocess.run(
                command, 
                capture_output=True, 
                text=True, 
                check=check,
                cwd=os.getcwd()
            )
        except subprocess.CalledProcessError as e:
            print(f"Git command failed: {' '.join(command)}")
            raise
    
    def _branch_exists_remotely(self) -> bool:
        try:
            result = self._run_git_command([
                "git", "ls-remote", "--exit-code", "--heads", 
                "origin", self.branch_name
            ], check=False)
            return result.returncode == 0
        except Exception:
            return False
    
    def _ensure_temp_directory(self):
        if not os.path.exists(self.temp_dir):
            os.makedirs(self.temp_dir)
    
    def _change_to_repo_root(self) -> str:
        original_cwd = os.getcwd()
        if os.path.basename(original_cwd) == 'utils':
            repo_root = os.path.dirname(original_cwd)
            os.chdir(repo_root)
        return original_cwd
    
    def setup_git_config(self, name: str = "Genshin Auto Daily Bot", email: str = "action@github.com"):
        self._run_git_command(["git", "config", "user.name", name])
        self._run_git_command(["git", "config", "user.email", email])
    
    def fetch_existing_files(self, file_patterns: List[str]) -> Dict[str, str]:
        if not self._branch_exists_remotely():
            return {}
        
        original_cwd = self._change_to_repo_root()
        fetched_files = {}
        
        try:
            self._run_git_command(["git", "fetch", "origin", f"{self.branch_name}:{self.branch_name}"])
            
            current_branch_result = self._run_git_command(["git", "branch", "--show-current"])
            current_branch = current_branch_result.stdout.strip()
            
            self._run_git_command(["git", "checkout", self.branch_name])
            self._ensure_temp_directory()
            
            for pattern in file_patterns:
                fetched_files.update(self._fetch_pattern_files(pattern))
            
            self._run_git_command(["git", "checkout", current_branch])
            return fetched_files
            
        except Exception:
            self._safe_checkout("main")
            return {}
        finally:
            self._safe_chdir(original_cwd)
    
    def _fetch_pattern_files(self, pattern: str) -> Dict[str, str]:
        fetched = {}
        try:
            find_result = self._run_git_command([
                "git", "ls-files", f"logs/{pattern}"
            ], check=False)
            
            if find_result.returncode == 0:
                files = [f.strip() for f in find_result.stdout.split('\n') if f.strip()]
                for file_path in files:
                    if os.path.exists(file_path):
                        temp_path = os.path.join(self.temp_dir, os.path.basename(file_path))
                        self._copy_file(file_path, temp_path)
                        fetched[os.path.basename(file_path)] = temp_path
        except Exception:
            pass
        return fetched
    
    def _copy_file(self, src: str, dst: str):
        with open(src, 'r', encoding='utf-8') as source:
            content = source.read()
        with open(dst, 'w', encoding='utf-8') as destination:
            destination.write(content)
    
    def _safe_checkout(self, branch: str):
        try:
            self._run_git_command(["git", "checkout", branch], check=False)
        except:
            pass
    
    def _safe_chdir(self, path: str):
        try:
            os.chdir(path)
        except:
            pass
    
    def restore_files_to_working_directory(self, fetched_files: Dict[str, str], target_dir: str = "."):
        original_cwd = self._change_to_repo_root()
        
        try:
            for filename, temp_path in fetched_files.items():
                try:
                    target_path = os.path.join(target_dir, filename)
                    if os.path.exists(temp_path):
                        self._copy_file(temp_path, target_path)
                except Exception:
                    pass
        finally:
            self._safe_chdir(original_cwd)
    
    def cleanup_temp_files(self):
        try:
            if os.path.exists(self.temp_dir):
                import shutil
                shutil.rmtree(self.temp_dir)
        except Exception:
            pass
    
    def create_or_switch_to_logs_branch(self):
        try:
            current_branch_result = self._run_git_command(["git", "branch", "--show-current"])
            
            if self._branch_exists_remotely():
                self._run_git_command(["git", "fetch", "origin", f"{self.branch_name}:{self.branch_name}"])
                self._run_git_command(["git", "checkout", self.branch_name])
                
                self._clean_non_logs_files()
            else:
                self._run_git_command(["git", "checkout", "--orphan", self.branch_name])
                self._clean_all_files()
            
            self._ensure_logs_directory()
            self._create_readme()
                
        except Exception as e:
            print(f"Error creating/switching to logs branch: {e}")
            raise
    
    def _clean_non_logs_files(self):
        try:
            result = self._run_git_command(["git", "ls-files"], check=False)
            if result.returncode == 0:
                files = [f.strip() for f in result.stdout.strip().split('\n') if f.strip()]
                files_to_remove = [f for f in files if f and not f.startswith('logs/')]
                
                for file_path in files_to_remove:
                    self._run_git_command(["git", "rm", "-f", file_path], check=False)
        except Exception:
            pass
    
    def _clean_all_files(self):
        try:
            self._run_git_command(["git", "rm", "-rf", "."], check=False)
        except:
            pass
    
    def _ensure_logs_directory(self):
        if not os.path.exists("logs"):
            os.makedirs("logs")
    
    def _create_readme(self):
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
    
    def commit_and_push_logs(self, files_to_commit: List[str], commit_message: Optional[str] = None):
        original_cwd = self._change_to_repo_root()
        temp_backup_dir = None
        
        try:
            temp_backup_dir = self._backup_files(files_to_commit)
            self._remove_conflicting_files(files_to_commit)
            
            self.create_or_switch_to_logs_branch()
            
            files_copied = self._restore_files_to_logs(temp_backup_dir)
            
            if files_copied or os.path.exists("README.md"):
                self._commit_files(files_copied, commit_message)
                self._push_to_remote()
                
        except Exception as e:
            print(f"Error committing and pushing logs: {e}")
            raise
        finally:
            self._safe_checkout("main")
            self._restore_files_from_backup(temp_backup_dir, files_to_commit)
            self._cleanup_backup(temp_backup_dir)
            self._safe_chdir(original_cwd)
    
    def _backup_files(self, files_to_commit: List[str]) -> str:
        temp_backup_dir = "temp_commit_backup"
        if os.path.exists(temp_backup_dir):
            import shutil
            shutil.rmtree(temp_backup_dir)
        os.makedirs(temp_backup_dir)
        
        for file_path in files_to_commit:
            if os.path.exists(file_path):
                backup_path = os.path.join(temp_backup_dir, os.path.basename(file_path))
                self._copy_file(file_path, backup_path)
        
        return temp_backup_dir
    
    def _remove_conflicting_files(self, files_to_commit: List[str]):
        for file_path in files_to_commit:
            if os.path.exists(file_path):
                os.remove(file_path)
    
    def _restore_files_to_logs(self, temp_backup_dir: str) -> List[str]:
        files_copied = []
        if not os.path.exists(temp_backup_dir):
            return files_copied
        
        for filename in os.listdir(temp_backup_dir):
            backup_path = os.path.join(temp_backup_dir, filename)
            target_path = os.path.join("logs", filename)
            
            try:
                self._copy_file(backup_path, target_path)
                files_copied.append(target_path)
            except Exception:
                pass
        
        return files_copied
    
    def _commit_files(self, files_copied: List[str], commit_message: Optional[str]):
        files_to_add = ["README.md"] + files_copied
        for file_to_add in files_to_add:
            if os.path.exists(file_to_add):
                self._run_git_command(["git", "add", file_to_add])
        
        if commit_message is None:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')
            commit_message = f"Update logs - {timestamp}"
        
        try:
            self._run_git_command(["git", "commit", "-m", commit_message])
        except subprocess.CalledProcessError:
            pass
    
    def _push_to_remote(self):
        try:
            self._run_git_command(["git", "push", "origin", self.branch_name])
        except subprocess.CalledProcessError:
            self._run_git_command(["git", "push", "--set-upstream", "origin", self.branch_name])
    
    def _restore_files_from_backup(self, temp_backup_dir: str, original_files: List[str]):
        if not temp_backup_dir or not os.path.exists(temp_backup_dir):
            return
        
        for original_path in original_files:
            backup_filename = os.path.basename(original_path)
            backup_path = os.path.join(temp_backup_dir, backup_filename)
            
            if os.path.exists(backup_path):
                try:
                    self._copy_file(backup_path, original_path)
                except Exception:
                    pass
    
    def _cleanup_backup(self, temp_backup_dir: str):
        if temp_backup_dir and os.path.exists(temp_backup_dir):
            try:
                import shutil
                shutil.rmtree(temp_backup_dir)
            except Exception:
                pass


def main():
    if len(sys.argv) < 2:
        print("Usage: python logs_manager.py <command> [args...]")
        print("Commands:")
        print("  fetch <patterns>  - Fetch files matching patterns (e.g., '*.log,*.txt')")
        print("  commit <files>    - Commit files to logs branch (e.g., 'file1.log,file2.txt')")
        return
    
    manager = LogsBranchManager()
    command = sys.argv[1]
    
    if command == "fetch":
        patterns = sys.argv[2].split(',') if len(sys.argv) > 2 else ['*.log', '*.txt']
        
        manager.setup_git_config()
        fetched = manager.fetch_existing_files(patterns)
        manager.restore_files_to_working_directory(fetched)
        manager.cleanup_temp_files()
        
    elif command == "commit":
        files = sys.argv[2].split(',') if len(sys.argv) > 2 else ['genshin-checkin.log', 'redeemed_codes.txt']
        
        manager.setup_git_config()
        manager.commit_and_push_logs(files)
        
    else:
        print(f"Unknown command: {command}")


if __name__ == "__main__":
    main()
