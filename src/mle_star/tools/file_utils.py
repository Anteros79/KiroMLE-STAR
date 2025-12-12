"""File utilities for dataset validation in MLE-STAR agents."""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class DatasetValidationResult:
    """Result of dataset path validation."""
    path: str
    exists: bool
    is_accessible: bool
    is_file: bool
    is_directory: bool
    file_size: Optional[int] = None
    error_message: Optional[str] = None
    
    @property
    def is_valid(self) -> bool:
        """Check if the dataset path is valid and accessible."""
        return self.exists and self.is_accessible


def validate_dataset_path(path: str) -> DatasetValidationResult:
    """Validate that a dataset path exists and is accessible.
    
    Args:
        path: Path to the dataset file or directory
        
    Returns:
        DatasetValidationResult with validation details
    """
    path_obj = Path(path)
    
    # Check existence
    exists = path_obj.exists()
    if not exists:
        return DatasetValidationResult(
            path=path,
            exists=False,
            is_accessible=False,
            is_file=False,
            is_directory=False,
            error_message=f"Path does not exist: {path}"
        )
    
    # Check if file or directory
    is_file = path_obj.is_file()
    is_directory = path_obj.is_dir()
    
    # Check accessibility (read permission)
    is_accessible = os.access(path, os.R_OK)
    if not is_accessible:
        return DatasetValidationResult(
            path=path,
            exists=True,
            is_accessible=False,
            is_file=is_file,
            is_directory=is_directory,
            error_message=f"Path is not readable: {path}"
        )
    
    # Get file size if it's a file
    file_size = None
    if is_file:
        try:
            file_size = path_obj.stat().st_size
        except OSError:
            pass
    
    return DatasetValidationResult(
        path=path,
        exists=True,
        is_accessible=True,
        is_file=is_file,
        is_directory=is_directory,
        file_size=file_size,
        error_message=None
    )


def validate_multiple_paths(paths: list[str]) -> dict[str, DatasetValidationResult]:
    """Validate multiple dataset paths.
    
    Args:
        paths: List of paths to validate
        
    Returns:
        Dictionary mapping paths to their validation results
    """
    return {path: validate_dataset_path(path) for path in paths}


def find_data_files(
    directory: str,
    extensions: Optional[list[str]] = None
) -> list[str]:
    """Find data files in a directory.
    
    Args:
        directory: Directory to search
        extensions: List of file extensions to look for (default: common data formats)
        
    Returns:
        List of paths to data files found
    """
    if extensions is None:
        extensions = [".csv", ".parquet", ".json", ".xlsx", ".xls", ".tsv", ".feather"]
    
    directory_path = Path(directory)
    if not directory_path.is_dir():
        return []
    
    data_files = []
    for ext in extensions:
        data_files.extend(str(p) for p in directory_path.glob(f"*{ext}"))
        data_files.extend(str(p) for p in directory_path.glob(f"**/*{ext}"))
    
    # Remove duplicates while preserving order
    seen = set()
    unique_files = []
    for f in data_files:
        if f not in seen:
            seen.add(f)
            unique_files.append(f)
    
    return unique_files
