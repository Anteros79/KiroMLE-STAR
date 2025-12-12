# Requirements Document

## Introduction

This document specifies the requirements for building an MLE-STAR (Machine Learning Engineering Agent via Search and Targeted Refinement) implementation using the Strands Agents SDK. MLE-STAR is a multi-agent framework that automates machine learning engineering tasks by generating Python code solutions. The system uses web search to retrieve effective models, iteratively refines solutions by targeting specific ML pipeline components through ablation studies, and employs ensemble strategies to combine multiple solutions.

## Glossary

- **MLE-STAR**: Machine Learning Engineering agent via Search and TArgeted Refinement - the framework being implemented
- **Strands Agent**: An AI agent built using the Strands Agents SDK that can use tools and maintain conversation context
- **Code Block**: A specific section of Python code representing a distinct ML pipeline component (e.g., feature engineering, model training)
- **Ablation Study**: An experiment that evaluates the contribution of individual ML components by modifying or disabling them
- **Refinement Plan**: A strategy proposed by an LLM to improve a specific code block
- **Ensemble Strategy**: A method to combine multiple ML solutions for improved performance
- **Validation Score**: A performance metric computed on a hold-out validation set
- **Data Leakage**: Improperly using test/validation data information during training
- **Inner Loop**: The iterative process of refining a single code block with multiple plans
- **Outer Loop**: The iterative process of selecting and refining different code blocks

## Requirements

### Requirement 1

**User Story:** As a data scientist, I want to provide a task description and dataset so that the system can automatically generate an ML solution.

#### Acceptance Criteria

1. WHEN a user provides a task description and dataset path THEN the MLE_STAR_System SHALL parse the inputs and initialize the solution generation pipeline
2. WHEN the task description is provided THEN the MLE_STAR_System SHALL extract task type, data modality, and evaluation metric information
3. WHEN datasets are provided THEN the MLE_STAR_System SHALL validate that the data files exist and are accessible
4. IF the task description is missing required information THEN the MLE_STAR_System SHALL report the missing fields to the user

### Requirement 2

**User Story:** As a data scientist, I want the system to search for effective models from the web so that I get state-of-the-art approaches rather than outdated methods.

#### Acceptance Criteria

1. WHEN generating an initial solution THEN the Retriever_Agent SHALL use web search to find relevant models for the given task
2. WHEN models are retrieved THEN the Retriever_Agent SHALL return model descriptions and example code for each candidate
3. WHEN the retrieval completes THEN the MLE_STAR_System SHALL have a configurable number of candidate models (default: 4)
4. WHEN a model is retrieved THEN the Retriever_Agent SHALL provide structured output containing model name, description, and implementation code

### Requirement 3

**User Story:** As a data scientist, I want each retrieved model to be evaluated so that the system can identify the best performing candidates.

#### Acceptance Criteria

1. WHEN a model candidate is received THEN the Candidate_Evaluation_Agent SHALL generate executable Python code using that model
2. WHEN evaluation code is generated THEN the Candidate_Evaluation_Agent SHALL include validation set splitting and metric computation
3. WHEN the code executes successfully THEN the MLE_STAR_System SHALL capture the validation performance score
4. IF the generated code fails to execute THEN the Debugger_Agent SHALL attempt to fix the errors up to a maximum retry limit

### Requirement 4

**User Story:** As a data scientist, I want the best model candidates to be merged into a single solution so that I benefit from multiple approaches.

#### Acceptance Criteria

1. WHEN multiple model candidates are evaluated THEN the Merger_Agent SHALL sort them by validation score in descending order
2. WHEN merging candidates THEN the Merger_Agent SHALL integrate models sequentially starting from the best performer
3. WHEN a merge is attempted THEN the Merger_Agent SHALL create an ensemble of the models
4. WHEN a merged solution performs worse than the current best THEN the MLE_STAR_System SHALL stop the merging process
5. WHEN merging completes THEN the MLE_STAR_System SHALL output a consolidated initial solution

### Requirement 5

**User Story:** As a data scientist, I want the system to identify which ML components have the greatest impact so that refinement efforts are focused effectively.

#### Acceptance Criteria

1. WHEN refining a solution THEN the Ablation_Study_Agent SHALL generate code that tests the impact of individual components
2. WHEN an ablation study executes THEN the MLE_STAR_System SHALL capture performance metrics for each component variation
3. WHEN ablation results are obtained THEN the Summarization_Agent SHALL parse and summarize the impact of each component
4. WHEN previous ablation summaries exist THEN the Ablation_Study_Agent SHALL use them to explore different pipeline parts

### Requirement 6

**User Story:** As a data scientist, I want the system to extract and refine the most impactful code blocks so that improvements are targeted and effective.

#### Acceptance Criteria

1. WHEN an ablation summary is available THEN the Extractor_Agent SHALL identify the code block with the most significant performance impact
2. WHEN extracting a code block THEN the Extractor_Agent SHALL also generate an initial refinement plan
3. WHEN previously refined blocks exist THEN the Extractor_Agent SHALL prioritize blocks not yet targeted
4. WHEN a code block is extracted THEN the MLE_STAR_System SHALL store it for the refinement inner loop

### Requirement 7

**User Story:** As a data scientist, I want the system to iteratively refine code blocks with multiple strategies so that the best improvement is found.

#### Acceptance Criteria

1. WHEN a code block is targeted THEN the Coder_Agent SHALL implement the refinement plan to produce a refined block
2. WHEN a refined block is produced THEN the MLE_STAR_System SHALL substitute it into the solution and evaluate performance
3. WHEN the inner loop continues THEN the Planner_Agent SHALL propose new refinement plans using previous attempts as feedback
4. WHEN the inner loop completes THEN the MLE_STAR_System SHALL select the best-performing candidate from all attempts
5. WHEN a refinement improves performance THEN the MLE_STAR_System SHALL update the current best solution

### Requirement 8

**User Story:** As a data scientist, I want the system to run multiple outer loop iterations so that different ML components are progressively improved.

#### Acceptance Criteria

1. WHEN the outer loop executes THEN the MLE_STAR_System SHALL perform a configurable number of iterations (default: 4)
2. WHEN each outer iteration completes THEN the MLE_STAR_System SHALL record the ablation summary and refined block
3. WHEN all outer iterations complete THEN the MLE_STAR_System SHALL output the final refined solution
4. WHEN tracking refinement history THEN the MLE_STAR_System SHALL maintain lists of previous ablation summaries and refined blocks

### Requirement 9

**User Story:** As a data scientist, I want multiple solutions to be combined using intelligent ensemble strategies so that I achieve better performance than any single solution.

#### Acceptance Criteria

1. WHEN multiple final solutions are available THEN the Ensemble_Planner_Agent SHALL propose an ensemble strategy
2. WHEN an ensemble strategy is proposed THEN the Ensembler_Agent SHALL implement it to combine the solutions
3. WHEN ensemble performance is evaluated THEN the Ensemble_Planner_Agent SHALL propose improved strategies using previous attempts as feedback
4. WHEN ensemble exploration completes THEN the MLE_STAR_System SHALL select the best-performing ensemble result
5. WHEN ensembling THEN the MLE_STAR_System SHALL explore a configurable number of strategies (default: 5)

### Requirement 10

**User Story:** As a data scientist, I want the system to automatically fix code errors so that the pipeline continues without manual intervention.

#### Acceptance Criteria

1. WHEN code execution triggers an error THEN the Debugger_Agent SHALL analyze the traceback and attempt correction
2. WHEN debugging THEN the Debugger_Agent SHALL iteratively update the script until successful or max retries reached
3. IF debugging fails after maximum attempts THEN the MLE_STAR_System SHALL proceed with the last working version
4. WHEN an error is fixed THEN the Debugger_Agent SHALL return the corrected script

### Requirement 11

**User Story:** As a data scientist, I want the system to detect and prevent data leakage so that my solutions generalize properly to test data.

#### Acceptance Criteria

1. WHEN a solution is generated THEN the Data_Leakage_Checker SHALL analyze preprocessing code for leakage risks
2. WHEN data leakage is detected THEN the Data_Leakage_Checker SHALL generate corrected code that uses only training statistics
3. WHEN checking for leakage THEN the Data_Leakage_Checker SHALL verify that test/validation data is not used during training preprocessing
4. WHEN leakage is corrected THEN the MLE_STAR_System SHALL replace the original code block with the corrected version

### Requirement 12

**User Story:** As a data scientist, I want the system to ensure all provided data sources are utilized so that no valuable information is overlooked.

#### Acceptance Criteria

1. WHEN an initial solution is generated THEN the Data_Usage_Checker SHALL verify that all provided data files are used
2. WHEN unused data sources are detected THEN the Data_Usage_Checker SHALL revise the solution to incorporate them
3. WHEN checking data usage THEN the Data_Usage_Checker SHALL compare the task description against the solution code
4. WHEN data usage is corrected THEN the MLE_STAR_System SHALL use the revised solution for refinement

### Requirement 13

**User Story:** As a data scientist, I want to generate a submission file from the final solution so that I can submit predictions to competitions.

#### Acceptance Criteria

1. WHEN a final solution is ready THEN the Test_Submission_Agent SHALL generate code to load test data and create predictions
2. WHEN generating submission code THEN the Test_Submission_Agent SHALL remove any subsampling used during refinement
3. WHEN submission code executes THEN the MLE_STAR_System SHALL produce a submission.csv file in the specified format
4. WHEN generating submissions THEN the Test_Submission_Agent SHALL use the full training set for final model training

### Requirement 14

**User Story:** As a developer, I want the system to be built using Strands Agents SDK so that it leverages proper multi-agent patterns and tool integration.

#### Acceptance Criteria

1. WHEN implementing agents THEN the MLE_STAR_System SHALL use Strands Agent class with appropriate tools and system prompts
2. WHEN agents need to execute code THEN the MLE_STAR_System SHALL use Python execution tools
3. WHEN agents need web search THEN the MLE_STAR_System SHALL use HTTP request or search tools
4. WHEN orchestrating agents THEN the MLE_STAR_System SHALL use Strands multi-agent patterns (Graph, Swarm, or Workflow)

### Requirement 15

**User Story:** As a developer, I want the system to have configurable parameters so that I can tune the exploration depth and resource usage.

#### Acceptance Criteria

1. WHEN initializing MLE-STAR THEN the MLE_STAR_System SHALL accept configuration for number of retrieved models
2. WHEN initializing MLE-STAR THEN the MLE_STAR_System SHALL accept configuration for inner loop iterations
3. WHEN initializing MLE-STAR THEN the MLE_STAR_System SHALL accept configuration for outer loop iterations
4. WHEN initializing MLE-STAR THEN the MLE_STAR_System SHALL accept configuration for ensemble exploration rounds
5. WHEN initializing MLE-STAR THEN the MLE_STAR_System SHALL accept configuration for maximum debugging retries
