"""MLE-STAR agent implementations.

This module contains agents for the MLE-STAR pipeline:

Phase 1 - Initial Solution Generation:
- Retriever Agent: Searches web for effective ML models
- Candidate Evaluator Agent: Evaluates model candidates on the task
- Merger Agent: Combines model solutions into ensembles

Phase 2 - Iterative Refinement:
- Ablation Study Agent: Generates ablation studies to identify component impacts
- Summarization Agent: Parses ablation output and extracts insights
- Extractor Agent: Identifies most impactful code blocks for refinement
- Coder Agent: Implements refinement plans on code blocks
- Planner Agent: Proposes new refinement strategies

Phase 3 - Ensemble:
- Ensemble Planner Agent: Proposes ensemble strategies to combine solutions
- Ensembler Agent: Implements ensemble strategies to merge solutions

Support Agents:
- Debugger Agent: Analyzes tracebacks and fixes code errors
- Data Leakage Checker Agent: Detects and corrects data leakage
- Data Usage Checker Agent: Verifies all data files are used
- Test Submission Agent: Generates submission code
"""

from mle_star.agents.retriever import (
    RETRIEVER_SYSTEM_PROMPT,
    create_retriever_agent,
    search_models,
    parse_model_candidates_from_response,
    retrieve_models,
)

from mle_star.agents.candidate_evaluator import (
    CANDIDATE_EVAL_SYSTEM_PROMPT,
    create_candidate_evaluator_agent,
    run_python_code,
    build_evaluation_prompt,
    evaluate_candidate,
    evaluate_all_candidates,
    sort_candidates_by_score,
)

from mle_star.agents.merger import (
    MERGER_SYSTEM_PROMPT,
    MergeResult,
    create_merger_agent,
    build_merge_prompt,
    merge_two_solutions,
    merge_candidates_sequentially,
)

from mle_star.agents.ablation_study import (
    ABLATION_STUDY_SYSTEM_PROMPT,
    AblationResult,
    create_ablation_study_agent,
    run_ablation_code,
    build_ablation_prompt,
    run_ablation_study,
    parse_ablation_results,
)

from mle_star.agents.summarizer import (
    SUMMARIZATION_SYSTEM_PROMPT,
    AblationSummary,
    create_summarization_agent,
    build_summarization_prompt,
    summarize_ablation_results,
    parse_ablation_summary,
)

from mle_star.agents.extractor import (
    EXTRACTOR_SYSTEM_PROMPT,
    ExtractedBlock,
    create_extractor_agent,
    build_extraction_prompt,
    extract_code_block,
    parse_extraction_result,
    should_skip_block,
)

from mle_star.agents.coder import (
    CODER_SYSTEM_PROMPT,
    RefinedCodeBlock,
    create_coder_agent,
    build_coder_prompt,
    refine_code_block,
    extract_code_from_response,
    substitute_code_block,
)

from mle_star.agents.planner import (
    PLANNER_SYSTEM_PROMPT,
    RefinementPlan,
    create_planner_agent,
    build_planner_prompt,
    propose_refinement_plan,
    parse_refinement_plan,
    format_plan_as_text,
    is_plan_similar_to_previous,
)

from mle_star.agents.ensemble_planner import (
    ENSEMBLE_PLANNER_SYSTEM_PROMPT,
    EnsemblePlan,
    create_ensemble_planner_agent,
    build_ensemble_planner_prompt,
    propose_ensemble_strategy,
    parse_ensemble_plan,
    format_ensemble_plan_as_text,
    is_strategy_similar_to_previous,
)

from mle_star.agents.ensembler import (
    ENSEMBLER_SYSTEM_PROMPT,
    EnsembleImplementationResult,
    create_ensembler_agent,
    build_ensembler_prompt,
    implement_ensemble,
    run_ensemble_iteration,
    explore_ensemble_strategies,
    select_best_ensemble,
)

from mle_star.agents.debugger import (
    DEBUGGER_SYSTEM_PROMPT,
    DebugResult,
    create_debugger_agent,
    build_debug_prompt,
    extract_code_from_debug_response,
    debug_code,
    debug_with_retries,
    debug_with_retries_sync,
)

from mle_star.agents.leakage_checker import (
    LEAKAGE_CHECKER_SYSTEM_PROMPT,
    LeakageCheckResult,
    create_leakage_checker_agent,
    build_leakage_check_prompt,
    parse_leakage_check_response,
    check_for_leakage,
    check_for_leakage_sync,
    contains_leakage_patterns,
)

from mle_star.agents.data_usage_checker import (
    DATA_USAGE_CHECKER_SYSTEM_PROMPT,
    DataUsageCheckResult,
    create_data_usage_checker_agent,
    extract_data_files_from_task,
    extract_used_files_from_code,
    find_missing_files,
    build_data_usage_check_prompt,
    parse_data_usage_response,
    check_data_usage,
    check_data_usage_sync,
)

from mle_star.agents.submission import (
    SUBMISSION_SYSTEM_PROMPT,
    SubmissionResult,
    create_submission_agent,
    detect_subsampling,
    build_submission_prompt,
    extract_submission_code,
    remove_subsampling_from_code,
    verify_no_subsampling,
    generate_submission,
    generate_submission_sync,
)

__all__ = [
    # Retriever Agent
    "RETRIEVER_SYSTEM_PROMPT",
    "create_retriever_agent",
    "search_models",
    "parse_model_candidates_from_response",
    "retrieve_models",
    # Candidate Evaluator Agent
    "CANDIDATE_EVAL_SYSTEM_PROMPT",
    "create_candidate_evaluator_agent",
    "run_python_code",
    "build_evaluation_prompt",
    "evaluate_candidate",
    "evaluate_all_candidates",
    "sort_candidates_by_score",
    # Merger Agent
    "MERGER_SYSTEM_PROMPT",
    "MergeResult",
    "create_merger_agent",
    "build_merge_prompt",
    "merge_two_solutions",
    "merge_candidates_sequentially",
    # Ablation Study Agent
    "ABLATION_STUDY_SYSTEM_PROMPT",
    "AblationResult",
    "create_ablation_study_agent",
    "run_ablation_code",
    "build_ablation_prompt",
    "run_ablation_study",
    "parse_ablation_results",
    # Summarization Agent
    "SUMMARIZATION_SYSTEM_PROMPT",
    "AblationSummary",
    "create_summarization_agent",
    "build_summarization_prompt",
    "summarize_ablation_results",
    "parse_ablation_summary",
    # Extractor Agent
    "EXTRACTOR_SYSTEM_PROMPT",
    "ExtractedBlock",
    "create_extractor_agent",
    "build_extraction_prompt",
    "extract_code_block",
    "parse_extraction_result",
    "should_skip_block",
    # Coder Agent
    "CODER_SYSTEM_PROMPT",
    "RefinedCodeBlock",
    "create_coder_agent",
    "build_coder_prompt",
    "refine_code_block",
    "extract_code_from_response",
    "substitute_code_block",
    # Planner Agent
    "PLANNER_SYSTEM_PROMPT",
    "RefinementPlan",
    "create_planner_agent",
    "build_planner_prompt",
    "propose_refinement_plan",
    "parse_refinement_plan",
    "format_plan_as_text",
    "is_plan_similar_to_previous",
    # Ensemble Planner Agent
    "ENSEMBLE_PLANNER_SYSTEM_PROMPT",
    "EnsemblePlan",
    "create_ensemble_planner_agent",
    "build_ensemble_planner_prompt",
    "propose_ensemble_strategy",
    "parse_ensemble_plan",
    "format_ensemble_plan_as_text",
    "is_strategy_similar_to_previous",
    # Ensembler Agent
    "ENSEMBLER_SYSTEM_PROMPT",
    "EnsembleImplementationResult",
    "create_ensembler_agent",
    "build_ensembler_prompt",
    "implement_ensemble",
    "run_ensemble_iteration",
    "explore_ensemble_strategies",
    "select_best_ensemble",
    # Debugger Agent
    "DEBUGGER_SYSTEM_PROMPT",
    "DebugResult",
    "create_debugger_agent",
    "build_debug_prompt",
    "extract_code_from_debug_response",
    "debug_code",
    "debug_with_retries",
    "debug_with_retries_sync",
    # Leakage Checker Agent
    "LEAKAGE_CHECKER_SYSTEM_PROMPT",
    "LeakageCheckResult",
    "create_leakage_checker_agent",
    "build_leakage_check_prompt",
    "parse_leakage_check_response",
    "check_for_leakage",
    "check_for_leakage_sync",
    "contains_leakage_patterns",
    # Data Usage Checker Agent
    "DATA_USAGE_CHECKER_SYSTEM_PROMPT",
    "DataUsageCheckResult",
    "create_data_usage_checker_agent",
    "extract_data_files_from_task",
    "extract_used_files_from_code",
    "find_missing_files",
    "build_data_usage_check_prompt",
    "parse_data_usage_response",
    "check_data_usage",
    "check_data_usage_sync",
    # Submission Agent
    "SUBMISSION_SYSTEM_PROMPT",
    "SubmissionResult",
    "create_submission_agent",
    "detect_subsampling",
    "build_submission_prompt",
    "extract_submission_code",
    "remove_subsampling_from_code",
    "verify_no_subsampling",
    "generate_submission",
    "generate_submission_sync",
]
