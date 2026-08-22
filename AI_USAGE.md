# AI Usage

This document records AI-assisted development used during the MetroPulse assessment.

## How AI Was Used

AI tools were used as an engineering and analytical assistant during development.

Major uses included:

- project planning and requirement decomposition
- SQL review and debugging
- Python debugging
- Streamlit application debugging
- dashboard layout and visualization review
- metric-definition review
- data-quality reasoning
- statistical interpretation
- documentation drafting
- README and project-structure drafting
- identifying unsupported causal claims
- reviewing analytical findings and recommendation logic

## Development Assistance

AI assistance was used to:

- diagnose Python import and package-structure errors
- debug DuckDB and SQL queries
- review SQL mart definitions
- improve dashboard visual hierarchy
- troubleshoot Plotly geographic visualization
- improve chart readability
- identify date-type comparison issues
- review payment classification logic
- review data-quality terminology
- structure statistical model comparisons
- identify analytical caveats and limitations

## Analytical Review

AI was also used to challenge analytical interpretations.

Examples include:

- distinguishing descriptive associations from causal claims
- identifying the weakness of interpreting peak-hour share against total multi-month trips
- identifying the need to expose weather sample sizes
- identifying overlap among data-quality issue populations
- distinguishing predictive model performance from causal inference
- identifying the reduction in the subway/taxi relationship after temporal controls
- reviewing recommendation logic and experimental design

## Verification

AI output was not treated as authoritative evidence.

The candidate independently verified:

- source data
- source metadata
- SQL transformations
- table grain
- row counts
- data-quality tests
- metric calculations
- statistical model outputs
- dashboard results
- repository structure
- dependency versions

Final analytical claims are based on project data, SQL outputs, statistical outputs, and executed code rather than AI-generated assertions.

## Human Responsibility

The candidate is responsible for the final code, analysis, interpretation, recommendations, documentation, and submitted results.

AI assistance does not replace verification of the underlying data or analytical conclusions.