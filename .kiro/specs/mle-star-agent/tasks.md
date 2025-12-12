# Implementation Plan

- [x] 1. Set up project structure and core configuration






  - [x] 1.1 Create project directory structure with src/, tests/, and config folders

    - Create `src/mle_star/` package with `__init__.py`
    - Create `src/mle_star/agents/`, `src/mle_star/tools/`, `src/mle_star/models/` subpackages
    - Create `tests/` directory with `unit/`, `property/`, `integration/` subdirectories
    - _Requirements: 14.1_

  - [x] 1.2 Implement MLEStarConfig dataclass with all configuration parameters

    - Define dataclass with num_retrieved_models, inner_loop_iterations, outer_loop_iterations, ensemble_iterations, max_debug_retries
    - Add model_id, temperature, max_tokens parameters
    - Implement to_dict() and from_dict() methods for serialization
    - _Requirements: 15.1, 15.2, 15.3, 15.4, 15.5_
  - [ ]* 1.3 Write property test for configuration round-trip
    - **Property 14: Configuration round-trip consistency**
    - **Validates: Requirements 15.1-15.5**

  - [x] 1.4 Install dependencies and create requirements.txt

    - Add strands-agents, strands-agents-tools, hypothesis for testing
    - _Requirements: 14.1_


- [x] 2. Implement data models





  - [x] 2.1 Create TaskDescription dataclass

    - Define fields: description, task_type, data_modality, evaluation_metric, dataset_path, submission_format
    - Implement parse_from_text() class method
    - _Requirements: 1.1, 1.2_
  - [ ]* 2.2 Write property test for task parsing
    - **Property 1: Task parsing extracts required fields**
    - **Validates: Requirements 1.2**

  - [x] 2.3 Create ModelCandidate dataclass

    - Define fields: name, description, example_code, validation_score, generated_code
    - _Requirements: 2.2, 2.4_

  - [x] 2.4 Create SolutionState dataclass

    - Define fields: current_code, validation_score, ablation_summaries, refined_blocks, outer_iteration, inner_iteration
    - _Requirements: 8.4_

  - [x] 2.5 Create RefinementAttempt and EnsembleResult dataclasses

    - RefinementAttempt: plan, refined_code_block, full_solution, validation_score, iteration
    - EnsembleResult: strategy, merged_code, validation_score, iteration
    - _Requirements: 7.1, 9.1_

- [x] 3. Implement core tools





  - [x] 3.1 Create execute_python tool for code execution


    - Implement subprocess-based Python execution with timeout
    - Capture stdout, stderr, and return code
    - Parse "Final Validation Performance:" from output
    - _Requirements: 3.2, 3.3, 14.2_

  - [x] 3.2 Create web_search tool for model retrieval

    - Implement search API integration (Google Search or alternative)
    - Return structured results with model descriptions and code examples
    - _Requirements: 2.1, 14.3_
  - [x] 3.3 Create file utilities for dataset validation


    - Implement validate_dataset_path() function
    - Check file existence and accessibility
    - _Requirements: 1.3_

- [x] 4. Checkpoint - Ensure all tests pass





  - Ensure all tests pass, ask the user if questions arise.

- [x] 5. Implement Phase 1 agents (Initial Solution Generation)





  - [x] 5.1 Implement Retriever Agent


    - Create agent with web_search tool and appropriate system prompt
    - Return list of ModelCandidate objects
    - _Requirements: 2.1, 2.2, 2.3, 2.4_
  - [ ]* 5.2 Write property test for model retrieval
    - **Property 2: Model retrieval returns structured candidates**
    - **Validates: Requirements 2.3, 2.4**

  - [x] 5.3 Implement Candidate Evaluation Agent

    - Create agent with execute_python tool
    - Generate evaluation code for each model candidate
    - Extract validation scores from execution output
    - _Requirements: 3.1, 3.2, 3.3_
  - [ ]* 5.4 Write property test for candidate evaluation
    - **Property 3: Candidate evaluation produces scores or errors**
    - **Validates: Requirements 3.3, 3.4**

  - [x] 5.5 Implement Merger Agent

    - Create agent that combines model solutions
    - Implement sequential merging with score comparison
    - Stop merging when performance degrades
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_
  - [ ]* 5.6 Write property test for merging logic
    - **Property 4: Merging maintains sorted order and stops on degradation**
    - **Validates: Requirements 4.1, 4.2, 4.4**

- [x] 6. Implement Phase 2 agents (Iterative Refinement)







  - [x] 6.1 Implement Ablation Study Agent
    - Create agent that generates ablation study code
    - Accept previous ablation summaries as context
    - _Requirements: 5.1, 5.4_

  - [x] 6.2 Implement Summarization Agent
    - Create agent that parses ablation study output
    - Extract component impact information
    - _Requirements: 5.3_
  - [x] 6.3 Write property test for ablation study






    - **Property 5: Ablation study captures component impacts**
    - **Validates: Requirements 5.2, 5.3**
  - [x] 6.4 Implement Extractor Agent
    - Create agent that identifies most impactful code block
    - Prioritize unrefined blocks
    - Generate initial refinement plan
    - _Requirements: 6.1, 6.2, 6.3, 6.4_
  - [ ]* 6.5 Write property test for extractor prioritization
    - **Property 6: Extractor prioritizes unrefined blocks**
    - **Validates: Requirements 6.3**
  - [x] 6.6 Implement Coder Agent
    - Create agent that implements refinement plans
    - Return refined code blocks
    - _Requirements: 7.1_

  - [x] 6.7 Implement Planner Agent
    - Create agent that proposes new refinement strategies
    - Use previous attempts as feedback
    - _Requirements: 7.3_


  - [x] 6.8 Write property test for inner loop selection




    - **Property 7: Inner loop selects best performer**
    - **Validates: Requirements 7.4, 7.5**

- [x] 7. Implement Phase 3 agents (Ensemble)






  - [x] 7.1 Implement Ensemble Planner Agent

    - Create agent that proposes ensemble strategies
    - Use previous ensemble attempts as feedback
    - _Requirements: 9.1, 9.3_

  - [x] 7.2 Implement Ensembler Agent

    - Create agent that implements ensemble strategies
    - Combine multiple solutions into merged code
    - _Requirements: 9.2_
  - [ ]* 7.3 Write property test for ensemble selection
    - **Property 9: Ensemble selects best strategy**
    - **Validates: Requirements 9.4**

- [x] 8. Checkpoint - Ensure all tests pass





  - Ensure all tests pass, ask the user if questions arise.


- [x] 9. Implement support agents





  - [x] 9.1 Implement Debugger Agent

    - Create agent that analyzes tracebacks and fixes code
    - Implement retry logic with configurable max retries
    - Return last working version on failure
    - _Requirements: 10.1, 10.2, 10.3, 10.4_
  - [ ]* 9.2 Write property test for debugger retry limit
    - **Property 10: Debugger respects retry limit**
    - **Validates: Requirements 10.2, 10.3**

  - [x] 9.3 Implement Data Leakage Checker Agent

    - Create agent that analyzes preprocessing code
    - Detect and correct data leakage patterns
    - _Requirements: 11.1, 11.2, 11.3, 11.4_
  - [ ]* 9.4 Write property test for leakage correction
    - **Property 11: Leakage checker produces valid corrections**
    - **Validates: Requirements 11.2, 11.3**

  - [x] 9.5 Implement Data Usage Checker Agent

    - Create agent that verifies all data files are used
    - Revise solution to incorporate missing files
    - _Requirements: 12.1, 12.2, 12.3, 12.4_
  - [ ]* 9.6 Write property test for data usage correction
    - **Property 12: Data usage checker incorporates missing files**
    - **Validates: Requirements 12.2, 12.3**

  - [x] 9.7 Implement Test Submission Agent

    - Create agent that generates submission code
    - Remove subsampling and use full training set
    - _Requirements: 13.1, 13.2, 13.3, 13.4_
  - [ ]* 9.8 Write property test for submission generation
    - **Property 13: Submission removes subsampling**
    - **Validates: Requirements 13.2, 13.4**


- [x] 10. Implement graph orchestration




  - [x] 10.1 Create InitialSolutionGraph using GraphBuilder


    - Add nodes: retriever, evaluator, merger, leakage_check, usage_check
    - Define edges for sequential flow
    - _Requirements: 14.4_

  - [x] 10.2 Create RefinementLoopNode custom node

    - Implement inner loop logic with configurable iterations
    - Track best solution and attempts
    - _Requirements: 7.2, 7.4, 7.5_

  - [x] 10.3 Create RefinementGraph with cyclic edges
    - Add nodes: ablation, summarize, extract, refine
    - Add conditional edge for outer loop continuation
    - Set max_node_executions for safety
    - _Requirements: 8.1, 8.2, 8.3_
  - [ ]* 10.4 Write property test for outer loop history
    - **Property 8: Outer loop maintains growing history**

    - **Validates: Requirements 8.2, 8.4**
  - [x] 10.5 Create EnsembleGraph

    - Add nodes: ensemble_planner, ensembler
    - Add conditional edge for iteration
    - _Requirements: 9.5_




- [x] 11. Implement main orchestrator


  - [x] 11.1 Create MLEStarOrchestrator class
    - Initialize with MLEStarConfig
    - Manage shared state across phases
    - _Requirements: 1.1_
  - [x] 11.2 Implement run() method

    - Execute Phase 1, 2, 3 in sequence
    - Handle errors and state recovery
    - _Requirements: 1.1, 10.3_

  - [x] 11.3 Implement parallel solution generation for ensemble


    - Run refinement pipeline multiple times
    - Collect solutions for ensemble phase
    - _Requirements: 9.1_



- [x] 12. Checkpoint - Ensure all tests pass



  - Ensure all tests pass, ask the user if questions arise.



- [x] 13. Integration and end-to-end testing



  - [x]* 13.1 Write integration tests for Phase 1 flow


    - Test retriever → evaluator → merger pipeline
    - _Requirements: 2.1, 3.1, 4.1_

  - [x]* 13.2 Write integration tests for Phase 2 flow

    - Test ablation → summarize → extract → refine loop
    - _Requirements: 5.1, 6.1, 7.1_


  - [x]* 13.3 Write integration tests for Phase 3 flow
    - Test ensemble planner → ensembler iteration
    - _Requirements: 9.1, 9.2_

  - [x]* 13.4 Write end-to-end test with sample tabular task
    - Test full pipeline on simple classification task
    - Verify submission file generation
    - _Requirements: 1.1, 13.3_


- [x] 14. Final Checkpoint - Ensure all tests pass




  - Ensure all tests pass, ask the user if questions arise.

- [x] 15. Build frontend interface for testing and proof of concept






  - [x] 15.1 Set up frontend project structure

    - Create React/Next.js application with TypeScript
    - Set up Tailwind CSS for styling
    - Configure API routes for backend communication
    - _Requirements: Frontend UI_

  - [x] 15.2 Implement main dashboard layout

    - Create header with MLE-STAR branding
    - Design sidebar navigation for different phases
    - Implement responsive layout
    - _Requirements: Frontend UI_

  - [x] 15.3 Create task input interface

    - Build form for task description input
    - Add dataset file upload component
    - Implement configuration panel for MLE-STAR parameters
    - _Requirements: 1.1, 15.1-15.5_

  - [x] 15.4 Implement pipeline visualization

    - Create visual representation of the three phases
    - Show agent nodes and their connections
    - Display real-time status updates during execution
    - _Requirements: Frontend UI_

  - [x] 15.5 Build results display components

    - Create solution code viewer with syntax highlighting
    - Display validation scores and metrics
    - Show refinement history and ablation results
    - _Requirements: Frontend UI_

  - [x] 15.6 Implement execution controls

    - Add start/stop/pause buttons for pipeline execution
    - Create progress indicators for each phase
    - Display logs and agent outputs in real-time
    - _Requirements: Frontend UI_
  - [x] 15.7 Create submission preview and download


    - Display generated submission.csv preview
    - Add download button for submission file
    - Show final ensemble results
    - _Requirements: 13.3_


- [x] 16. Final Checkpoint - Ensure frontend and backend integration works




  - Ensure all tests pass, ask the user if questions arise.
