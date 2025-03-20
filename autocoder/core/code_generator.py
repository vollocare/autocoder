"""
Code generator module for the Autocoder tool.
"""

import os
import sys
import time
import tempfile
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Set

from autocoder.core.api_client import APIClient
from autocoder.core.spec_parser import SpecificationParser
from autocoder.utils.config import config
from autocoder.utils.logger import logger


class CodeGenerator:
    """Code generator class that creates code from specifications using the AI model."""
    
    def __init__(self, api_client: Optional[APIClient] = None):
        self.api_client = api_client or APIClient()
        self.max_iterations = config.get("max_test_iterations", 50)
        self.current_iteration = 0
        self.last_code_output: Dict[str, str] = {}
        self.last_error: Optional[str] = None
        self.output_dir: str = ""
    
    def generate(self, specification_content: str, output_dir: str, max_iterations: int = 50) -> bool:
        """
        Generate code from a specification.
        
        Args:
            specification_content: The content of the specification file
            output_dir: The directory to write the generated code to
            max_iterations: Maximum number of iterations to try generating valid code
            
        Returns:
            bool: True if code was successfully generated, False otherwise
        """
        logger.info(f"Generating code from specification content")
        logger.info(f"Output directory: {output_dir}")
        
        # Make sure the output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        self.max_iterations = max_iterations
        self.last_error = None
        self.current_iteration = 0
        
        # Use the specification parser to extract information
        spec_parser = SpecificationParser()
        spec_data = spec_parser.parse_specification_content(specification_content)
        
        # Generate a prompt for the AI model using the specification data
        prompt = spec_parser.generate_prompt(spec_data)
        
        # Use a standard system prompt for code generation
        system_prompt = (
            "You are an expert Python developer tasked with generating high-quality, maintainable code based on detailed specifications. "
            "Focus on writing clean, efficient, and well-documented code. Follow PEP 8 style guidelines and include type annotations. "
            "Organize the code into appropriate modules and classes with clear separation of concerns. "
            "Handle all potential errors and edge cases appropriately. "
            "Return the complete implementation, including all necessary files and their contents. "
            "For each file, specify the complete file path and the entire contents of the file using the following format:\n\n"
            "```file:path/to/file.py\n"
            "# File contents go here\n"
            "```\n\n"
            "Include at least the following files: main implementation modules, utility modules, and test files."
        )
        
        success = False
        # 設定輸出的實際目錄
        self.output_dir = output_dir
        
        # Get repository files for context before the first iteration
        repo_files = self._get_repository_files(self.output_dir)
        
        # Start the code generation loop
        for iteration in range(self.max_iterations):
            self.current_iteration = iteration + 1
            
            logger.info(f"Code generation iteration {self.current_iteration}/{self.max_iterations}")
            
            # Generate code using the AI model
            code_output = self._generate_code(prompt, system_prompt, iteration, repo_files)
            if not code_output:
                logger.error("Failed to generate code")
                break
            
            # Extract and save files from the code output
            extracted_files = self._extract_files(code_output)
            if not extracted_files:
                logger.error("No valid files found in the generated code")
                break
            
            # Write files to the output directory
            file_paths = self._write_files(extracted_files, output_dir)
            if not file_paths:
                logger.error("Failed to write files to output directory")
                break
            
            # Test the generated code
            success, error = self._test_code(file_paths, output_dir)
            if success:
                logger.success("Code generated successfully and passed all tests")
                break
            
            # Store the error for the next iteration
            self.last_error = error
            
            # Update the prompt with the error for the next iteration
            prompt = self._update_prompt_with_error(prompt, error, extracted_files, self.output_dir)
            
            logger.warning(f"Code test failed, retrying (iteration {self.current_iteration}/{self.max_iterations})")
            
            # Add a small delay to avoid overwhelming the API
            time.sleep(1)
        
        return success
    
    def _generate_code(self, prompt: str, system_prompt: str, iteration: int, repo_files: Optional[Dict[str, str]] = None) -> str:
        """Generate code using the AI model."""
        logger.info("Sending request to AI model")
        
        # Adjust temperature based on iteration
        # Start with higher creativity and gradually become more conservative
        temperature = max(0.4, 0.7 - iteration * 0.05)
        
        # Add error context if available and this isn't the first iteration
        context = None
        if iteration > 0 and self.last_error:
            context = (
                f"The previous code generation attempt failed with the following error:\n"
                f"```\n{self.last_error}\n```\n"
                f"Please fix the issues and regenerate the code."
            )
        
        # Add repository context using Qwen 2.5 Coder format
        repo_context = ""
        if repo_files:
            # Get repository name (last part of the absolute path)
            repo_name = os.path.basename(os.path.abspath("."))
            
            repo_context = f"<|repo_name|>{repo_name}\n"
            
            # Add each file with the file separator
            for file_path, content in repo_files.items():
                repo_context += f"<|file_sep|>{file_path}\n{content}\n"
            
            logger.debug(f"Added repository context with {len(repo_files)} files")
        
        try:
            response = self.api_client.generate_code(
                prompt=prompt,
                context=context,
                repo_context=repo_context,
                system_prompt=system_prompt,
                temperature=temperature
            )
            
            if not response:
                logger.error("Empty response from AI model")
                return ""
            
            return response
        
        except Exception as e:
            logger.error(f"Error generating code: {str(e)}")
            return ""
    
    def _extract_files(self, code_output: str) -> Dict[str, str]:
        """Extract files from the generated code output."""
        extracted_files: Dict[str, str] = {}
        
        # Store the original code output for reference
        self.last_code_output = {"raw_output": code_output}
        
        # Regular expression pattern for file blocks would be too complex here,
        # so we'll use a more straightforward string parsing approach
        
        lines = code_output.splitlines()
        current_file = None
        current_content = []
        
        for line in lines:
            # Check for file marker at the beginning of a line
            if line.startswith("```file:") or line.startswith("```python:") or line.startswith("```filepath:"):
                # If we were already processing a file, save it
                if current_file and current_content:
                    extracted_files[current_file] = "\n".join(current_content)
                    self.last_code_output[current_file] = "\n".join(current_content)
                    current_content = []
                
                # Extract new filename
                parts = line.split(":", 1)
                if len(parts) > 1:
                    current_file = parts[1].strip()
                    # Remove trailing backticks if present
                    current_file = current_file.rstrip("`").strip()
                else:
                    current_file = None
            
            # Check for end of code block
            elif line.strip() == "```" and current_file:
                # Save the current file
                if current_file and current_content:
                    extracted_files[current_file] = "\n".join(current_content)
                    self.last_code_output[current_file] = "\n".join(current_content)
                    current_content = []
                    current_file = None
            
            # If we're within a file block, add the line to content
            elif current_file is not None:
                current_content.append(line)
        
        # Handle the case where the last file doesn't have a closing marker
        if current_file and current_content:
            extracted_files[current_file] = "\n".join(current_content)
            self.last_code_output[current_file] = "\n".join(current_content)
        
        logger.info(f"Extracted {len(extracted_files)} files from generated code")
        return extracted_files
    
    def _write_files(self, files: Dict[str, str], output_dir: str) -> List[str]:
        """Write the extracted files to the output directory."""
        file_paths = []
        
        # Create the output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        for file_path, content in files.items():
            # Convert to absolute path
            full_path = os.path.join(output_dir, file_path)
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
            try:
                with open(full_path, "w", encoding="utf-8") as f:
                    f.write(content)
                
                file_paths.append(full_path)
                logger.debug(f"Wrote file: {full_path}")
            
            except Exception as e:
                logger.error(f"Failed to write file {full_path}: {str(e)}")
        
        logger.info(f"Wrote {len(file_paths)} files to output directory")
        return file_paths
    
    def _test_code(self, file_paths: List[str], output_dir: str) -> Tuple[bool, Optional[str]]:
        """Test the generated code by running pytest on the test files."""
        test_files = [path for path in file_paths if "test" in os.path.basename(path).lower()]
        
        if not test_files:
            logger.warning("No test files found in generated code")
            return False, "No test files were generated"
        
        logger.info(f"Found {len(test_files)} test files")
        
        # Create a temporary script to install dependencies
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as temp:
            setup_script = (
                "import sys\n"
                "import subprocess\n"
                "import pkg_resources\n\n"
                "def install_missing_packages(packages):\n"
                "    installed = {pkg.key for pkg in pkg_resources.working_set}\n"
                "    missing = [pkg for pkg in packages if pkg.lower() not in installed]\n"
                "    if missing:\n"
                "        print(f'Installing missing packages: {missing}')\n"
                "        subprocess.check_call([sys.executable, '-m', 'pip', 'install'] + missing)\n"
                "    else:\n"
                "        print('All required packages are already installed')\n\n"
                "# List of possible required packages\n"
                "packages = ['pytest', 'mypy', 'flake8']\n\n"
                "# Check for any other dependencies in setup.py or requirements.txt\n"
                "try:\n"
                "    with open('setup.py', 'r') as f:\n"
                "        setup_content = f.read()\n"
                "        # Very basic extraction of install_requires\n"
                "        if 'install_requires' in setup_content:\n"
                "            import re\n"
                "            match = re.search(r'install_requires\\s*=\\s*\\[(.+?)\\]', setup_content, re.DOTALL)\n"
                "            if match:\n"
                "                deps = match.group(1)\n"
                "                for dep in re.finditer(r'[\"\\']([\\w\\->=<.]+)[\"\\']', deps):\n"
                "                    packages.append(dep.group(1))\n"
                "except (FileNotFoundError, IOError):\n"
                "    pass\n\n"
                "try:\n"
                "    with open('requirements.txt', 'r') as f:\n"
                "        for line in f:\n"
                "            line = line.strip()\n"
                "            if line and not line.startswith('#'):\n"
                "                packages.append(line)\n"
                "except (FileNotFoundError, IOError):\n"
                "    pass\n\n"
                "install_missing_packages(packages)\n"
            )
            
            temp.write(setup_script.encode())
            temp.flush()
            setup_script_path = temp.name
        
        try:
            # Run the dependency setup script
            logger.info("Checking and installing dependencies...")
            
            # Use the new command method with verbose output
            setup_result = logger.command(
                f"{sys.executable} {setup_script_path}",
                cwd=output_dir
            )
            
            if not setup_result["success"]:
                logger.error("Failed to install dependencies")
                return False, f"Dependency installation failed: {setup_result['stderr']}"
            
            # Run the tests
            logger.info("Running tests...")
            test_result = logger.command(
                f"{sys.executable} -m pytest {' '.join(test_files)} -v",
                cwd=output_dir
            )
            
            # Display test summary
            if test_result["success"]:
                logger.success("All tests passed!")
                if logger.verbose:
                    logger.info("Test output:\n" + test_result["stdout"])
                return True, None
            else:
                logger.error("Tests failed")
                # Return the error output for debugging
                return False, test_result["stderr"] or test_result["stdout"]
            
        except Exception as e:
            logger.error(f"Error running tests: {str(e)}")
            return False, str(e)
        
        finally:
            # Clean up the temporary file
            try:
                os.unlink(setup_script_path)
            except (OSError, IOError):
                pass
    
    def _get_repository_files(self, output_dir: str) -> Dict[str, str]:
        """
        Collect all relevant files from the repository for context.
        
        Args:
            output_dir: The output directory where generated code is stored.
            
        Returns:
            Dict[str, str]: Dictionary mapping file paths to file contents.
        """
        repo_files = {}
        excluded_patterns = [
            "mermaid.md",
            os.path.join("**", "specs", "**"),
            os.path.join("**", ".git", "**"),
            "**/*.git*",
            "**/__pycache__/**",
            "**/*.pyc",
            "**/*.pyo",
            "**/*.so",
            "**/*.o",
            "**/*.a",
            "**/*.log",
            "**/.pytest_cache/**",
            "**/sample/**",  # Exclude sample directories
            "**/*.md",       # Exclude markdown files
        ]
        
        # 限制檔案數量和總大小
        MAX_FILES = 20  # 限制最多收集10個文件
        MAX_TOTAL_SIZE = 20000  # 限制總字符數約20K
        current_total_size = 0
        
        # 需翹取得的是輸出的實際檔案
        root_dir = output_dir
        logger.debug(f"Collecting repository files from: {root_dir}")
        
        # Function to check if a path should be excluded
        def is_excluded(path: str) -> bool:
            from fnmatch import fnmatch
            rel_path = os.path.relpath(path, root_dir)
            return any(fnmatch(rel_path, pattern) for pattern in excluded_patterns)
        
        # 優先收集的文件类型，按照優先級排序
        priority_patterns = [
            "**/*.py",       # Python源碼
            "**/__init__.py", # 包初始化文件
            "**/cli.py",      # CLI相關文件
            "**/core/*.py",   # 核心模組
        ]
        
        # 優先收集的文件
        priority_files = []
        
        # 首先找出所有優先級文件
        for pattern in priority_patterns:
            for root, dirs, files in os.walk(root_dir):
                # Filter out excluded directories
                dirs[:] = [d for d in dirs if not is_excluded(os.path.join(root, d))]
                
                for file in files:
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, root_dir)
                    
                    from fnmatch import fnmatch
                    if fnmatch(rel_path, pattern) and not is_excluded(file_path):
                        if file_path not in priority_files:
                            priority_files.append(file_path)
        
        # 處理優先文件
        for file_path in priority_files:
            if len(repo_files) >= MAX_FILES or current_total_size >= MAX_TOTAL_SIZE:
                break
                
            try:
                if os.path.getsize(file_path) > 1024 * 50:  # Skip files larger than 50KB
                    continue
                
                # Try to read the file as text
                with open(file_path, 'r', encoding='utf-8') as f:
                    file_content = f.read()
                    
                # 檢查加入這個文件後是否會超過總大小限制
                if current_total_size + len(file_content) > MAX_TOTAL_SIZE:
                    # 如果會超過，跳過這個文件
                    continue
                    
                # Store file content with relative path
                rel_path = os.path.relpath(file_path, root_dir)
                repo_files[rel_path] = file_content
                current_total_size += len(file_content)
                
            except (UnicodeDecodeError, IOError, OSError):
                # Skip files that can't be read as text
                continue
        
        # 如果還有空間，收集其他文件
        if len(repo_files) < MAX_FILES and current_total_size < MAX_TOTAL_SIZE:
            for root, dirs, files in os.walk(root_dir):
                if len(repo_files) >= MAX_FILES or current_total_size >= MAX_TOTAL_SIZE:
                    break
                    
                # Filter out excluded directories
                dirs[:] = [d for d in dirs if not is_excluded(os.path.join(root, d))]
                
                for file in files:
                    if len(repo_files) >= MAX_FILES or current_total_size >= MAX_TOTAL_SIZE:
                        break
                        
                    file_path = os.path.join(root, file)
                    if is_excluded(file_path):
                        continue
                    
                    # 跳过已經收集的文件
                    rel_path = os.path.relpath(file_path, root_dir)
                    if rel_path in repo_files:
                        continue
                    
                    # Skip large files
                    try:
                        if os.path.getsize(file_path) > 1024 * 50:  # Skip files larger than 50KB
                            continue
                        
                        # Try to read the file as text
                        with open(file_path, 'r', encoding='utf-8') as f:
                            file_content = f.read()
                            
                        # 檢查加入這個文件後是否會超過總大小限制
                        if current_total_size + len(file_content) > MAX_TOTAL_SIZE:
                            # 如果會超過，跳過這個文件
                            continue
                            
                        # Store file content with relative path
                        repo_files[rel_path] = file_content
                        current_total_size += len(file_content)
                        
                    except (UnicodeDecodeError, IOError, OSError):
                        # Skip files that can't be read as text
                        continue
        
        logger.debug(f"Collected {len(repo_files)} repository files for context (total size: {current_total_size} chars)")
        return repo_files
    
    def _update_prompt_with_error(self, prompt: str, error: Optional[str], files: Dict[str, str], output_dir: str) -> str:
        """Update the prompt with error information for the next iteration."""
        if not error:
            return prompt
        
        # Add the error information to the prompt
        error_context = (
            "\n\n# Previous Error\n"
            f"The previous code generation attempt failed with the following error:\n"
            f"```\n{error}\n```\n"
            f"Please fix the issues and regenerate the code."
        )
        
        # 先找出問題文件，優先包含這些文件
        problematic_files = {}
        if files:
            # Look for file references in the error message
            for file_path in files.keys():
                file_name = os.path.basename(file_path)
                if file_name in error:
                    problematic_files[file_path] = files[file_path]
        
        # Add problematic files first if any were identified
        if problematic_files:
            error_context += "\n\n# Problematic Files\n"
            for file_path, content in problematic_files.items():
                error_context += f"\nThe problematic file was `{file_path}`:\n"
                error_context += f"```python\n{content}\n```\n"
        
        # 只為沒有問題文件的情況收集存儲庫文件
        # 或者錯誤信息超過1000字符的情況（可能需要更多上下文）
        if not problematic_files or len(error) > 1000:
            # Collect repository files for context, but limit the number
            repo_files = self._get_repository_files(output_dir)
            
            # 限制添加的文件數量
            MAX_REPO_FILES = 5
            if len(repo_files) > MAX_REPO_FILES:
                logger.debug(f"Limiting repository context to {MAX_REPO_FILES} files (from {len(repo_files)} collected)")
                # 按文件大小排序，優先保留較小的文件
                sorted_files = sorted(repo_files.items(), key=lambda x: len(x[1]))
                repo_files = dict(sorted_files[:MAX_REPO_FILES])
            
            # Add repository context using Qwen 2.5 Coder format
            if repo_files:
                # Get repository name (last part of the absolute path)
                repo_name = os.path.basename(os.path.abspath("."))
                
                error_context += "\n\n# Repository Context\n"
                error_context += f"<|repo_name|>{repo_name}\n"
                
                # Add each file with the file separator
                for file_path, content in repo_files.items():
                    error_context += f"<|file_sep|>{file_path}\n{content}\n"
        
        return prompt + error_context 