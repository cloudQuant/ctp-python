#!/usr/bin/env python3
"""
Script to clear pip cache
"""
import subprocess
import sys
import os

def run_command(cmd, timeout=120):
    """Run command with timeout"""
    try:
        result = subprocess.run(
            cmd, 
            shell=True, 
            capture_output=True, 
            text=True, 
            timeout=timeout
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Command timed out after 120 seconds"
    except Exception as e:
        return False, "", f"Error: {str(e)}"

def clear_pip_cache():
    """Clear pip cache"""
    print("Clearing pip cache...")
    
    # Check pip cache directory
    success, output, error = run_command("pip cache dir")
    if success:
        cache_dir = output.strip()
        print(f"Pip cache directory: {cache_dir}")
    else:
        print(f"Could not get cache directory: {error}")
        return False
    
    # Clear the cache
    print("Clearing cache...")
    success, output, error = run_command("pip cache purge")
    if success:
        print("✓ Pip cache cleared successfully!")
        print(output)
        return True
    else:
        print(f"✗ Failed to clear cache: {error}")
        return False

def show_cache_info():
    """Show current cache info"""
    print("Current pip cache info:")
    success, output, error = run_command("pip cache info")
    if success:
        print(output)
    else:
        print(f"Could not get cache info: {error}")

if __name__ == "__main__":
    show_cache_info()
    print("\n" + "="*50 + "\n")
    clear_pip_cache()
    print("\n" + "="*50 + "\n")
    show_cache_info()
