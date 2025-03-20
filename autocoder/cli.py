"""
Command-line interface for the Autocoder tool.
"""

import os
import sys
import click
import time
from pathlib import Path
from typing import List, Optional

from autocoder.core.api_client import APIClient
from autocoder.core.spec_parser import SpecificationParser
from autocoder.core.code_generator import CodeGenerator
from autocoder.utils.config import config
from autocoder.utils.logger import logger, LogLevel


@click.group()
@click.version_option(version="0.1.0")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@click.option("--quiet", "-q", is_flag=True, help="Minimize output")
@click.option("--no-color", is_flag=True, help="Disable colored output")
def cli(verbose: bool, quiet: bool, no_color: bool):
    """Autocoder: AI-powered automatic code generation tool.
    
    Generate, test, and validate code automatically using AI models.
    All output directories specified with --output-dir will be created if they don't exist.
    """
    # Configure logging based on options
    if verbose:
        logger.set_verbose(True)
    if quiet:
        logger.set_verbose(False)
        logger.min_level = LogLevel.WARNING
    if no_color:
        logger.set_colors_enabled(False)


@cli.command("generate")
@click.argument("spec_path", type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True))
@click.option("--output-dir", "-o", type=click.Path(file_okay=False), help="Output directory for generated code (will be created if it doesn't exist)")
@click.option("--api-endpoint", type=str, help="API endpoint for the model")
@click.option("--temperature", type=float, help="Model temperature (0.0-1.0)")
@click.option("--max-iterations", type=int, help="Maximum number of generation/test iterations")
def generate(
    spec_path: str,
    output_dir: Optional[str] = None,
    api_endpoint: Optional[str] = None,
    temperature: Optional[float] = None,
    max_iterations: Optional[int] = None
):
    """Generate code from a specification file."""
    # Start timing
    start_time = time.time()
    
    # Validate spec file
    if not SpecificationParser.is_valid_spec_file(spec_path):
        logger.error(f"The file '{spec_path}' does not appear to be a valid specification file.")
        sys.exit(1)
    
    # Determine output directory
    if not output_dir:
        spec_base = os.path.basename(spec_path).split(".")[0]
        output_dir = os.path.join(os.getcwd(), f"{spec_base}_output")
        logger.info(f"No output directory specified. Using: {output_dir}")
    else:
        # Ensure the path is absolute
        output_dir = os.path.abspath(output_dir)
        logger.info(f"Output directory: {output_dir}")
    
    # Output directory will be created by the code generator if it doesn't exist
    
    # Print environment information in verbose mode
    if logger.verbose:
        logger.debug(f"Python version: {sys.version}")
        logger.debug(f"Operating system: {sys.platform}")
        logger.debug(f"Working directory: {os.getcwd()}")
    
    # Override configuration if provided
    if api_endpoint:
        config.set("model.api_endpoint", api_endpoint)
        logger.debug(f"Using custom API endpoint: {api_endpoint}")
    
    if temperature is not None:
        config.set("model.temperature", temperature)
        logger.debug(f"Using custom temperature: {temperature}")
    
    if max_iterations is not None:
        config.set("max_test_iterations", max_iterations)
        logger.debug(f"Using custom max iterations: {max_iterations}")
    
    # Create API client and code generator
    api_client = APIClient()
    code_generator = CodeGenerator(api_client)
    
    # Print config information in verbose mode
    if logger.verbose:
        logger.debug(f"API endpoint: {config.get('model.api_endpoint')}")
        logger.debug(f"Temperature: {config.get('model.temperature')}")
        logger.debug(f"Top P: {config.get('model.top_p')}")
        logger.debug(f"Max tokens: {config.get('model.max_tokens')}")
        logger.debug(f"Quantization: {config.get('model.quantize')}")
        logger.debug(f"Max iterations: {config.get('max_test_iterations')}")
    
    # Generate code
    logger.info(f"Starting code generation from specification: {spec_path}")
    try:
        # Read the specification file
        with open(spec_path, 'r', encoding='utf-8') as f:
            spec_content = f.read()
        
        # Use the new generate method instead of generate_from_spec
        success = code_generator.generate(
            specification_content=spec_content, 
            output_dir=output_dir,
            max_iterations=config.get("max_test_iterations")
        )
        
        # Calculate and display total elapsed time
        elapsed_time = time.time() - start_time
        minutes, seconds = divmod(elapsed_time, 60)
        time_str = f"{int(minutes)}m {seconds:.2f}s" if minutes > 0 else f"{seconds:.2f}s"
        
        if success:
            logger.success(f"Code generated successfully in {time_str}")
            logger.info(f"Output directory: {output_dir}")
            
            # Print command history in verbose mode
            if logger.verbose:
                logger.print_command_history()
            
            return 0
        else:
            logger.error(f"Code generation failed after {code_generator.current_iteration} iterations ({time_str})")
            logger.info(f"Partial code was saved to: {output_dir}")
            
            # Print command history in verbose mode
            if logger.verbose:
                logger.print_command_history()
            
            return 1
    
    except Exception as e:
        elapsed_time = time.time() - start_time
        minutes, seconds = divmod(elapsed_time, 60)
        time_str = f"{int(minutes)}m {seconds:.2f}s" if minutes > 0 else f"{seconds:.2f}s"
        
        logger.critical(f"Error during code generation: {str(e)}")
        logger.error(f"Process aborted after {time_str}")
        
        # Print command history in verbose mode
        if logger.verbose:
            logger.print_command_history()
        
        return 1


@cli.command("understand")
@click.argument("code_path", type=click.Path(exists=True, readable=True))
@click.option("--output-file", "-o", type=click.Path(dir_okay=False), help="Output file for documentation")
def understand(code_path: str, output_file: Optional[str] = None):
    """Analyze existing code and generate documentation."""
    logger.info("Code understanding functionality is not yet implemented")
    logger.info("This feature will be available in a future version")
    return 1


@cli.command("refactor")
@click.argument("code_path", type=click.Path(exists=True, readable=True))
@click.option("--target", "-t", type=str, help="Specific file or directory to refactor")
@click.option("--output-dir", "-o", type=click.Path(file_okay=False), help="Output directory for refactored code (will be created if it doesn't exist)")
def refactor(code_path: str, target: Optional[str] = None, output_dir: Optional[str] = None):
    """Refactor existing code to improve structure and performance."""
    # Determine output directory
    if not output_dir:
        code_base = os.path.basename(code_path)
        output_dir = os.path.join(os.getcwd(), f"{code_base}_refactored")
        logger.info(f"No output directory specified. Using: {output_dir}")
    else:
        # Ensure the path is absolute
        output_dir = os.path.abspath(output_dir)
    
    # Output directory will be created when needed
    
    logger.info("Code refactoring functionality is not yet implemented")
    logger.info("This feature will be available in a future version")
    return 1


@cli.command("test")
@click.argument("code_path", type=click.Path(exists=True, readable=True))
@click.option("--output-dir", "-o", type=click.Path(file_okay=False), help="Output directory for generated tests (will be created if it doesn't exist)")
def test(code_path: str, output_dir: Optional[str] = None):
    """Generate and run tests for existing code."""
    # Determine output directory
    if not output_dir:
        code_base = os.path.basename(code_path)
        output_dir = os.path.join(os.getcwd(), f"{code_base}_tests")
        logger.info(f"No output directory specified. Using: {output_dir}")
    else:
        # Ensure the path is absolute
        output_dir = os.path.abspath(output_dir)
    
    # Output directory will be created when needed
    
    logger.info("Test generation functionality is not yet implemented")
    logger.info("This feature will be available in a future version")
    return 1


@cli.command("interactive")
def interactive():
    """Start interactive development mode."""
    logger.info("Interactive mode is not yet implemented")
    logger.info("This feature will be available in a future version")
    return 1


@cli.command("config")
@click.option("--model", type=str, help="Path to model or model identifier")
@click.option("--api", type=str, help="API endpoint URL")
@click.option("--list", "list_config", is_flag=True, help="List current configuration")
@click.option("--global", "global_config", is_flag=True, help="Apply to global configuration")
def config_cmd(model: Optional[str], api: Optional[str], list_config: bool, global_config: bool):
    """Configure model settings."""
    if list_config:
        # Display current configuration
        print("\nCurrent Configuration:")
        print(f"API Endpoint:    {config.get('model.api_endpoint')}")
        print(f"Temperature:     {config.get('model.temperature')}")
        print(f"Top P:           {config.get('model.top_p')}")
        print(f"Max Tokens:      {config.get('model.max_tokens')}")
        print(f"Quantization:    {config.get('model.quantize')}")
        print(f"Max Iterations:  {config.get('max_test_iterations')}")
        print(f"Verbose Mode:    {config.get('verbose')}")
        print(f"Colors Enabled:  {config.get('colors_enabled')}")
        return 0
    
    # Update configuration
    changes_made = False
    
    if model:
        config.set("model.model_path", model)
        changes_made = True
        print(f"Model path set to: {model}")
    
    if api:
        config.set("model.api_endpoint", api)
        changes_made = True
        print(f"API endpoint set to: {api}")
    
    if changes_made:
        config.save(global_config=global_config)
        if global_config:
            print("Global configuration updated")
        else:
            print("Project configuration updated")
    
    return 0


def main():
    """Main entry point for the Autocoder tool."""
    return cli() 