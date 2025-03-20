"""
Parser for software development specification documents.
"""

import re
from pathlib import Path
from typing import Dict, Any, List, Optional
import yaml
import markdown
from bs4 import BeautifulSoup

from autocoder.utils.logger import logger


class SpecificationParser:
    """Parser for software development specification documents in markdown format."""
    
    def __init__(self, spec_path: Optional[str] = None):
        self.spec_path = Path(spec_path) if spec_path else None
        self.spec_content = ""
        self.parsed_data: Dict[str, Any] = {
            "metadata": {},
            "description": "",
            "architecture": "",
            "input_output": "",
            "requirements": "",
            "test_cases": [],
            "dependencies": [],
            "error_handling": "",
            "performance": "",
            "interfaces": "",
            "code_prompts": [],
        }
        
        if self.spec_path:
            self._load_spec_file()
    
    def _load_spec_file(self):
        """Load the specification from a file."""
        if not self.spec_path or not self.spec_path.exists():
            raise FileNotFoundError(f"Specification file not found: {self.spec_path}")
        
        logger.info(f"Parsing specification file: {self.spec_path}")
        with open(self.spec_path, "r", encoding="utf-8") as f:
            self.spec_content = f.read()
    
    def parse_specification_content(self, content: str) -> Dict[str, Any]:
        """
        Parse specification content directly from a string.
        
        Args:
            content: The specification content as a string
            
        Returns:
            Dict[str, Any]: The parsed specification data
        """
        self.spec_content = content
        return self.parse()
    
    def parse(self) -> Dict[str, Any]:
        """Parse the specification and extract all relevant information."""
        if not self.spec_content:
            raise ValueError("No specification content to parse. Either provide a spec_path or call parse_specification_content().")
            
        # Extract YAML front matter if present
        self._extract_metadata()
        
        # Convert markdown to HTML for structured parsing
        html = markdown.markdown(self.spec_content)
        soup = BeautifulSoup(html, "html.parser")
        
        # Extract sections, test cases, dependencies, and code prompts
        self._extract_sections(soup)
        self._extract_test_cases(soup)
        self._extract_dependencies(soup)
        self._extract_code_prompts(soup)
        
        # If we couldn't extract test cases from HTML, try parsing from markdown directly
        if not self.parsed_data["test_cases"]:
            self._extract_test_cases_from_markdown()
            
        # If we couldn't extract dependencies from HTML, try parsing from markdown directly
        if not self.parsed_data["dependencies"]:
            self._extract_dependencies_from_markdown()
        
        logger.debug("Specification parsing complete")
        return self.parsed_data
    
    def _extract_metadata(self):
        """Extract metadata from YAML front matter if present."""
        yaml_pattern = r"^---\s*$(.*?)^---\s*$"
        match = re.search(yaml_pattern, self.spec_content, re.MULTILINE | re.DOTALL)
        
        if match:
            try:
                yaml_content = match.group(1)
                metadata = yaml.safe_load(yaml_content)
                if isinstance(metadata, dict):
                    self.parsed_data["metadata"] = metadata
                    logger.debug("Extracted metadata from YAML front matter")
            except yaml.YAMLError as e:
                logger.warning(f"Failed to parse YAML front matter: {str(e)}")
    
    def _extract_sections(self, soup: BeautifulSoup):
        """Extract sections based on headings."""
        # Map of section titles to their corresponding keys in parsed_data
        section_mapping = {
            "功能描述": "description",
            "架構設計": "architecture",
            "輸入/輸出規格": "input_output",
            "技術要求": "requirements",
            "錯誤處理": "error_handling",
            "性能要求": "performance",
            "介面定義": "interfaces",
            # Additional English mappings
            "Description": "description",
            "Architecture": "architecture",
            "Input/Output": "input_output",
            "Requirements": "requirements",
            "Error Handling": "error_handling",
            "Performance": "performance",
            "Interfaces": "interfaces",
        }
        
        # Find all headings
        headings = soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"])
        
        for i, heading in enumerate(headings):
            heading_text = heading.get_text().strip()
            
            # Check if this heading matches any of our known sections
            section_key = None
            for title, key in section_mapping.items():
                if title in heading_text:
                    section_key = key
                    break
            
            if section_key:
                # Extract the content between this heading and the next
                content = []
                current = heading.next_sibling
                next_heading = headings[i + 1] if i + 1 < len(headings) else None
                
                while current and current != next_heading:
                    if current.name:  # Only process tag elements, not strings
                        content.append(str(current))
                    current = current.next_sibling
                
                # Join the content and store it
                self.parsed_data[section_key] = "".join(content)
                logger.debug(f"Extracted section: {heading_text}")
    
    def _extract_test_cases(self, soup: BeautifulSoup):
        """Extract test cases from the specification."""
        # Look for test case sections
        test_section = None
        for heading in soup.find_all(["h1", "h2", "h3", "h4"]):
            if "測試案例" in heading.get_text() or "Test Case" in heading.get_text() or "Tests" in heading.get_text():
                test_section = heading
                break
        
        if not test_section:
            return
        
        # Look for individual test cases (h3, h4 level headings under the Test Cases section)
        test_case_headings = []
        
        # Find all headings after the test section
        current = test_section.next_sibling
        while current:
            if current.name in ["h1", "h2", "h3", "h4", "h5", "h6"]:
                if current.name > test_section.name:  # This is a subheading
                    test_case_headings.append(current)
                elif current.name <= test_section.name:  # This is a new section
                    break
            
            if hasattr(current, 'next_sibling'):
                current = current.next_sibling
            else:
                break
        
        # If no specific test case headings, extract code blocks directly from the test section
        if not test_case_headings:
            current = test_section.next_sibling
            code_blocks = []
            
            # Collect all code blocks in this section
            while current:
                if current.name == "pre":
                    code_blocks.append(current)
                elif current.name in ["h1", "h2", "h3", "h4"] and current.name <= test_section.name:
                    break
                
                if hasattr(current, 'next_sibling'):
                    current = current.next_sibling
                else:
                    break
            
            # Process the code blocks
            if len(code_blocks) >= 1:
                test_case = {
                    "description": test_section.get_text(),
                    "code": code_blocks[0].get_text() if code_blocks else "",
                    "expected_output": code_blocks[1].get_text() if len(code_blocks) > 1 else ""
                }
                
                if test_case["code"]:
                    self.parsed_data["test_cases"].append(test_case)
                    logger.debug(f"Extracted test case directly from section: {test_section.get_text()}")
        
        # Process each test case heading if we found any
        for i, heading in enumerate(test_case_headings):
            test_case = {
                "description": heading.get_text(),
                "code": "",
                "expected_output": ""
            }
            
            # Find next heading or end of document
            current = heading.next_sibling
            next_heading = None
            if i < len(test_case_headings) - 1:
                next_heading = test_case_headings[i + 1]
            else:
                # Check if there's a new section after this
                temp = heading.next_sibling
                while temp:
                    if temp.name in ["h1", "h2", "h3", "h4"] and temp.name <= test_section.name:
                        next_heading = temp
                        break
                    if hasattr(temp, 'next_sibling'):
                        temp = temp.next_sibling
                    else:
                        break
            
            code_blocks = []
            
            while current and current != next_heading:
                if current.name == "pre":
                    code_blocks.append(current)
                
                if hasattr(current, 'next_sibling'):
                    current = current.next_sibling
                else:
                    break
            
            # Process code blocks - first is code, second might be expected output
            if code_blocks:
                test_case["code"] = code_blocks[0].get_text()
                
                # Check if there's a second code block that might be expected output
                if len(code_blocks) > 1:
                    # Check if there's a specific marker for expected output
                    prev_node = code_blocks[1].previous_sibling
                    is_output = False
                    
                    if prev_node and hasattr(prev_node, 'get_text'):
                        prev_text = prev_node.get_text().lower()
                        if "expected" in prev_text or "output" in prev_text or "輸出" in prev_text:
                            is_output = True
                    
                    if is_output:
                        test_case["expected_output"] = code_blocks[1].get_text()
                    else:
                        # If no marker, use the second block as code if first was short
                        if len(test_case["code"]) < len(code_blocks[1].get_text()):
                            test_case["code"] = code_blocks[1].get_text()
                        else:
                            test_case["expected_output"] = code_blocks[1].get_text()
            
            if test_case["code"]:
                self.parsed_data["test_cases"].append(test_case)
                logger.debug(f"Extracted test case: {test_case['description']}")
    
    def _extract_test_cases_from_markdown(self):
        """Fallback method to extract test cases directly from markdown content."""
        # Find the test section
        test_section_match = re.search(r'#\s*(測試案例|Test Cases|Tests)', self.spec_content, re.IGNORECASE)
        if not test_section_match:
            return
        
        # Get the position where the test section starts
        start_pos = test_section_match.start()
        
        # Find the next heading after the test section
        next_section_match = re.search(r'^#(?!#)', self.spec_content[start_pos+1:], re.MULTILINE)
        end_pos = len(self.spec_content)
        if next_section_match:
            end_pos = start_pos + 1 + next_section_match.start()
        
        # Extract the test section content
        test_section_content = self.spec_content[start_pos:end_pos]
        
        # Check for subheadings (test cases)
        sub_headings = re.finditer(r'^##\s+(.*?)$', test_section_content, re.MULTILINE)
        sub_heading_positions = []
        
        for match in sub_headings:
            sub_heading_positions.append({
                "position": match.start(), 
                "title": match.group(1).strip()
            })
        
        # If there are subheadings, extract code blocks from each
        if sub_heading_positions:
            for i, heading in enumerate(sub_heading_positions):
                # Determine the end of this sub-section
                start = heading["position"]
                if i < len(sub_heading_positions) - 1:
                    end = sub_heading_positions[i + 1]["position"]
                else:
                    end = len(test_section_content)
                
                # Extract content for this test case
                test_case_content = test_section_content[start:end]
                
                # Find code blocks in this test case
                code_blocks = re.findall(r'```(?:\w+)?\n(.*?)```', test_case_content, re.DOTALL)
                
                if code_blocks:
                    test_case = {
                        "description": heading["title"],
                        "code": code_blocks[0] if code_blocks else "",
                        "expected_output": code_blocks[1] if len(code_blocks) > 1 else ""
                    }
                    
                    # Check if there's an expected output marker before the second code block
                    if len(code_blocks) > 1:
                        # Look for "Expected Output:" or similar text before the second code block
                        output_marker = re.search(r'(?:Expected Output|輸出).*?```', test_case_content, re.IGNORECASE | re.DOTALL)
                        if output_marker:
                            test_case["expected_output"] = code_blocks[1]
                    
                    if test_case["code"]:
                        self.parsed_data["test_cases"].append(test_case)
                        logger.debug(f"Extracted test case from markdown subheading: {heading['title']}")
        
        # If no subheadings or no test cases found yet, extract code blocks directly
        if not sub_heading_positions or not self.parsed_data["test_cases"]:
            # Find all code blocks in this section
            code_blocks = re.findall(r'```(?:\w+)?\n(.*?)```', test_section_content, re.DOTALL)
            
            if len(code_blocks) >= 1:
                test_case = {
                    "description": test_section_match.group(0),
                    "code": code_blocks[0] if code_blocks else "",
                    "expected_output": code_blocks[1] if len(code_blocks) > 1 else ""
                }
                
                if test_case["code"]:
                    self.parsed_data["test_cases"].append(test_case)
                    logger.debug("Extracted test case using direct markdown parsing")
    
    def _extract_dependencies(self, soup: BeautifulSoup):
        """Extract dependencies from the specification."""
        dependency_sections = []
        for heading in soup.find_all(["h1", "h2", "h3", "h4"]):
            heading_text = heading.get_text().lower()
            if "相依性" in heading_text or "依賴" in heading_text or "dependencies" in heading_text:
                dependency_sections.append(heading)
        
        for section in dependency_sections:
            current = section.next_sibling
            
            # Find the list elements that follow this heading
            while current:
                if current.name == "ul":
                    # Found an unordered list
                    for li in current.find_all("li"):
                        dependency = li.get_text().strip()
                        if dependency:
                            self.parsed_data["dependencies"].append(dependency)
                            logger.debug(f"Extracted dependency: {dependency}")
                elif current.name in ["h1", "h2", "h3", "h4"]:
                    # Reached another heading, stop processing
                    break
                
                if hasattr(current, 'next_sibling'):
                    current = current.next_sibling
                else:
                    break
        
        # If no dependencies were found using HTML parsing, try direct markdown parsing
        if not self.parsed_data["dependencies"]:
            self._extract_dependencies_from_markdown()
    
    def _extract_dependencies_from_markdown(self):
        """Fallback method to extract dependencies directly from markdown content."""
        # Find the dependencies section
        dep_section_match = re.search(r'#\s*(相依性|Dependencies|依賴)', self.spec_content, re.IGNORECASE)
        if not dep_section_match:
            return
        
        # Get the position where the dependencies section starts
        start_pos = dep_section_match.start()
        
        # Find the next heading after the dependencies section
        next_section_match = re.search(r'#\s*[^#]', self.spec_content[start_pos+1:])
        end_pos = len(self.spec_content)
        if next_section_match:
            end_pos = start_pos + 1 + next_section_match.start()
        
        # Extract the dependencies section content
        dep_section_content = self.spec_content[start_pos:end_pos]
        
        # Find all list items in this section
        dependencies = re.findall(r'- (.*?)(?:\n|$)', dep_section_content)
        
        for dep in dependencies:
            dep = dep.strip()
            if dep:
                self.parsed_data["dependencies"].append(dep)
                logger.debug(f"Extracted dependency using direct markdown parsing: {dep}")
    
    def _extract_code_prompts(self, soup: BeautifulSoup):
        """Extract code generation prompts from the specification."""
        prompt_sections = []
        for heading in soup.find_all(["h1", "h2", "h3", "h4"]):
            heading_text = heading.get_text().lower()
            if "提示" in heading_text or "prompt" in heading_text or "生成規範" in heading_text:
                prompt_sections.append(heading)
        
        for section in prompt_sections:
            prompt = {
                "title": section.get_text(),
                "content": ""
            }
            
            content_parts = []
            current = section.next_sibling
            
            while current:
                if current.name in ["h1", "h2", "h3", "h4"]:
                    # Reached another heading, stop processing
                    break
                
                if current.name:
                    content_parts.append(str(current))
                
                if hasattr(current, 'next_sibling'):
                    current = current.next_sibling
                else:
                    break
            
            prompt["content"] = "".join(content_parts)
            if prompt["content"]:
                self.parsed_data["code_prompts"].append(prompt)
                logger.debug(f"Extracted code prompt: {prompt['title']}")
    
    def generate_prompt(self, parsed_data: Optional[Dict[str, Any]] = None) -> str:
        """
        Generate a prompt for the AI model based on the parsed specification.
        
        Args:
            parsed_data: Optional parsed specification data. If not provided, uses self.parsed_data.
            
        Returns:
            str: The generated prompt
        """
        data = parsed_data or self.parsed_data
        
        prompt = "# Software Development Specification\n\n"
        
        # Add metadata if available
        if data["metadata"]:
            prompt += "## Metadata\n\n"
            for key, value in data["metadata"].items():
                prompt += f"- **{key}**: {value}\n"
            prompt += "\n"
        
        # Add description
        if data["description"]:
            prompt += "## Functional Description\n\n"
            prompt += data["description"] + "\n\n"
        
        # Add architecture
        if data["architecture"]:
            prompt += "## Architecture Design\n\n"
            prompt += data["architecture"] + "\n\n"
        
        # Add input/output specifications
        if data["input_output"]:
            prompt += "## Input/Output Specifications\n\n"
            prompt += data["input_output"] + "\n\n"
        
        # Add technical requirements
        if data["requirements"]:
            prompt += "## Technical Requirements\n\n"
            prompt += data["requirements"] + "\n\n"
        
        # Add error handling
        if data["error_handling"]:
            prompt += "## Error Handling\n\n"
            prompt += data["error_handling"] + "\n\n"
        
        # Add performance considerations
        if data["performance"]:
            prompt += "## Performance Considerations\n\n"
            prompt += data["performance"] + "\n\n"
        
        # Add interfaces
        if data["interfaces"]:
            prompt += "## Interfaces\n\n"
            prompt += data["interfaces"] + "\n\n"
        
        # Add test cases
        if data["test_cases"]:
            prompt += "## Test Cases\n\n"
            for i, test in enumerate(data["test_cases"], 1):
                prompt += f"### Test Case {i}: {test.get('description', '')}\n"
                if test.get("code"):
                    prompt += f"```\n{test['code']}\n```\n"
                if test.get("expected_output"):
                    prompt += f"Expected Output:\n```\n{test['expected_output']}\n```\n"
        
        # Add dependencies
        if data["dependencies"]:
            prompt += "## Dependencies\n\n"
            for dep in data["dependencies"]:
                prompt += f"- {dep}\n"
        
        # Add specific code prompts if available
        if data["code_prompts"]:
            prompt += "## Code Generation Guidelines\n\n"
            for prompt in data["code_prompts"]:
                prompt += f"### {prompt['title']}\n\n"
                prompt += prompt['content'] + "\n\n"
        
        # Add a clear instruction at the end
        prompt += "\n## Task\n\n"
        prompt += "Based on the above specifications, please generate high-quality, well-documented Python code "
        prompt += "that implements all the required functionality. The code should follow PEP 8 style guidelines, "
        prompt += "include type annotations, handle errors appropriately, and be thoroughly tested against the "
        prompt += "provided test cases.\n\n"
        prompt += "Please organize the code into appropriate modules and classes, with clear separation of concerns. "
        prompt += "Ensure that the code is efficient, maintainable, and follows best practices for Python development.\n\n"
        prompt += "Include comprehensive docstrings and comments to explain the purpose and functionality of each component."
        
        return prompt
    
    @staticmethod
    def is_valid_spec_file(file_path: str) -> bool:
        """Check if a file appears to be a valid specification file."""
        path = Path(file_path)
        
        # Check file extension
        if path.suffix.lower() not in [".md", ".markdown"]:
            return False
        
        # Check if file exists
        if not path.exists():
            return False
        
        # Basic content check
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read(1024)  # Read just the beginning
                
                # Check for some typical spec file headers
                patterns = [
                    r"#\s*(功能描述|Description)",
                    r"#\s*(架構設計|Architecture)",
                    r"#\s*(規格|Specification)",
                    r"#\s*(需求|Requirements)"
                ]
                
                for pattern in patterns:
                    if re.search(pattern, content, re.IGNORECASE):
                        return True
                
                # Check for YAML front matter
                if re.match(r"^---\s*$", content, re.MULTILINE):
                    return True
                
                return False
        except Exception:
            return False 