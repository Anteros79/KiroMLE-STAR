"""Data models for MLE-STAR agent."""

from dataclasses import dataclass, field
from typing import Optional
import re


@dataclass
class TaskDescription:
    """Represents an ML task to solve.
    
    Attributes:
        description: Full text description of the ML task
        task_type: Type of ML task (classification, regression, seq2seq, etc.)
        data_modality: Type of data (tabular, image, text, audio)
        evaluation_metric: Metric used to evaluate model performance
        dataset_path: Path to the dataset files
        submission_format: Optional format specification for submission file
    """
    
    description: str
    task_type: str
    data_modality: str
    evaluation_metric: str
    dataset_path: str
    submission_format: Optional[str] = None
    
    @classmethod
    def parse_from_text(cls, text: str) -> "TaskDescription":
        """Parse a task description from free-form text.
        
        Extracts task type, data modality, evaluation metric, and dataset path
        from the provided text description.
        
        Args:
            text: Free-form text describing the ML task
            
        Returns:
            TaskDescription instance with extracted fields
        """
        # Extract task type
        task_type = cls._extract_task_type(text)
        
        # Extract data modality
        data_modality = cls._extract_data_modality(text)
        
        # Extract evaluation metric
        evaluation_metric = cls._extract_evaluation_metric(text)
        
        # Extract dataset path
        dataset_path = cls._extract_dataset_path(text)
        
        # Extract submission format if present
        submission_format = cls._extract_submission_format(text)
        
        return cls(
            description=text,
            task_type=task_type,
            data_modality=data_modality,
            evaluation_metric=evaluation_metric,
            dataset_path=dataset_path,
            submission_format=submission_format,
        )

    
    @staticmethod
    def _extract_task_type(text: str) -> str:
        """Extract task type from text description."""
        text_lower = text.lower()
        
        # Check for specific task types
        task_patterns = [
            (r'\b(multi[- ]?class\s+classification|multiclass)\b', 'multiclass_classification'),
            (r'\b(binary\s+classification)\b', 'binary_classification'),
            (r'\b(classification)\b', 'classification'),
            (r'\b(regression)\b', 'regression'),
            (r'\b(seq2seq|sequence[- ]to[- ]sequence)\b', 'seq2seq'),
            (r'\b(time[- ]?series)\b', 'time_series'),
            (r'\b(clustering)\b', 'clustering'),
            (r'\b(object[- ]?detection)\b', 'object_detection'),
            (r'\b(segmentation)\b', 'segmentation'),
            (r'\b(recommendation)\b', 'recommendation'),
            (r'\b(ranking)\b', 'ranking'),
            (r'\b(generation)\b', 'generation'),
        ]
        
        for pattern, task_type in task_patterns:
            if re.search(pattern, text_lower):
                return task_type
        
        return "unknown"
    
    @staticmethod
    def _extract_data_modality(text: str) -> str:
        """Extract data modality from text description."""
        text_lower = text.lower()
        
        modality_patterns = [
            (r'\b(tabular|csv|structured\s+data|dataframe)\b', 'tabular'),
            (r'\b(image|images|vision|visual|photo|picture)\b', 'image'),
            (r'\b(text|nlp|natural\s+language|document|corpus)\b', 'text'),
            (r'\b(audio|sound|speech|voice)\b', 'audio'),
            (r'\b(video)\b', 'video'),
            (r'\b(multimodal)\b', 'multimodal'),
        ]
        
        for pattern, modality in modality_patterns:
            if re.search(pattern, text_lower):
                return modality
        
        return "unknown"
    
    @staticmethod
    def _extract_evaluation_metric(text: str) -> str:
        """Extract evaluation metric from text description."""
        text_lower = text.lower()
        
        metric_patterns = [
            (r'\b(accuracy)\b', 'accuracy'),
            (r'\b(auc[- ]?roc|roc[- ]?auc)\b', 'auc_roc'),
            (r'\b(f1[- ]?score|f1)\b', 'f1_score'),
            (r'\b(precision)\b', 'precision'),
            (r'\b(recall)\b', 'recall'),
            (r'\b(rmse|root\s+mean\s+squared?\s+error)\b', 'rmse'),
            (r'\b(mse|mean\s+squared?\s+error)\b', 'mse'),
            (r'\b(mae|mean\s+absolute\s+error)\b', 'mae'),
            (r'\b(r2|r\^?2|r[- ]?squared)\b', 'r2'),
            (r'\b(log[- ]?loss|logloss)\b', 'log_loss'),
            (r'\b(map|mean\s+average\s+precision)\b', 'map'),
            (r'\b(bleu)\b', 'bleu'),
            (r'\b(rouge)\b', 'rouge'),
        ]
        
        for pattern, metric in metric_patterns:
            if re.search(pattern, text_lower):
                return metric
        
        return "unknown"
    
    @staticmethod
    def _extract_dataset_path(text: str) -> str:
        """Extract dataset path from text description."""
        # Look for common path patterns
        path_patterns = [
            r'(?:dataset|data|path|file)[:\s]+["\']?([^\s"\']+)["\']?',
            r'["\']([^"\']+\.csv)["\']',
            r'["\']([^"\']+/data/[^"\']+)["\']',
            r'(?:located\s+(?:at|in)|from)\s+["\']?([^\s"\']+)["\']?',
        ]
        
        for pattern in path_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return ""
    
    @staticmethod
    def _extract_submission_format(text: str) -> Optional[str]:
        """Extract submission format from text description."""
        # Look for submission format specifications
        format_patterns = [
            r'submission\s+format[:\s]+["\']?([^"\'\.]+)["\']?',
            r'submit\s+(?:a\s+)?["\']?([^"\']+\.csv)["\']?',
            r'output\s+format[:\s]+["\']?([^"\'\.]+)["\']?',
        ]
        
        for pattern in format_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None



@dataclass
class ModelCandidate:
    """A retrieved model candidate from web search.
    
    Attributes:
        name: Name of the model/approach
        description: Description of the model and its capabilities
        example_code: Example implementation code for the model
        validation_score: Score achieved on validation set (None if not yet evaluated)
        generated_code: Full generated code for this candidate (None if not yet generated)
    """
    
    name: str
    description: str
    example_code: str
    validation_score: Optional[float] = None
    generated_code: Optional[str] = None


@dataclass
class SolutionState:
    """Tracks the current state of solution development.
    
    Attributes:
        current_code: The current Python code solution
        validation_score: Current validation performance score
        ablation_summaries: List of summaries from previous ablation studies
        refined_blocks: List of code blocks that have been refined
        outer_iteration: Current outer loop iteration number
        inner_iteration: Current inner loop iteration number
    """
    
    current_code: str
    validation_score: float
    ablation_summaries: list[str] = field(default_factory=list)
    refined_blocks: list[str] = field(default_factory=list)
    outer_iteration: int = 0
    inner_iteration: int = 0


@dataclass
class RefinementAttempt:
    """Records a single refinement attempt in the inner loop.
    
    Attributes:
        plan: The refinement plan/strategy being attempted
        refined_code_block: The refined version of the code block
        full_solution: The complete solution with the refined block substituted
        validation_score: Validation score achieved with this refinement
        iteration: The iteration number of this attempt
    """
    
    plan: str
    refined_code_block: str
    full_solution: str
    validation_score: float
    iteration: int


@dataclass
class EnsembleResult:
    """Result of an ensemble strategy attempt.
    
    Attributes:
        strategy: Description of the ensemble strategy used
        merged_code: The merged solution code
        validation_score: Validation score achieved by the ensemble
        iteration: The iteration number of this ensemble attempt
    """
    
    strategy: str
    merged_code: str
    validation_score: float
    iteration: int
