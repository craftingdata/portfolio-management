# Portfolio Optimization Reimplementation Plan

This document defines the high-priority implementation plan for bringing this repository closer to the Gurobi finance notebook coverage while using FMP Ultimate for market data and JerBouma's FinanceToolkit for financial analytics.

## Current Status

### Implemented

- FMP market-data retrieval is implemented in the data service layer.
- FMP authentication is implemented through Azure Key Vault using `DefaultAzureCredential`.
- Missing FMP credentials now fail loudly instead of silently falling back to synthetic data.
- The estimation layer is implemented for annualized mean return and covariance generation.
- FinanceToolkit is integrated for risk diagnostics only when an FMP API key is available.
- Focused tests cover:
  - Azure Key Vault secret retrieval behavior
  - FMP HTTP fetch behavior
  - FinanceToolkit constructor usage with the FMP-backed API-key path
  - API failure behavior when the FMP key is unavailable

### Not Implemented Yet

- Real factor-model support
- Gurobi-style mixed-integer portfolio constraints
- Rebalancing and transaction-cost formulations
- Efficient-frontier generation
- Output-driven ranking replacing the current heuristic ranking

### Current Rule

- FinanceToolkit is no longer constructed through a local no-api-key branch.
- If FinanceToolkit is used in this repo, it is expected to run with an FMP API key and therefore use FMP under the hood.
- Synthetic data remains available only as a fallback for non-authentication FMP fetch failures in the market-data layer.

## Assumptions

- FMP Ultimate is the primary source for historical prices, asset metadata, and sector classification.
- FinanceToolkit refers to https://github.com/JerBouma/FinanceToolkit and will be used where it provides reliable return, risk, and portfolio analytics utilities.
- SCIP remains the primary optimization engine for constrained and mixed-integer formulations.
- SciPy remains a fallback for continuous problems and for relaxed approximations when SCIP features are not required.

## Priority 1: Replace Synthetic Data With Provider-Based Market Data

### Goal

Remove the current synthetic-first data flow and replace it with a provider abstraction backed by FMP Ultimate.

### Scope

- Add a provider interface in the data service layer.
- Implement an FMP Ultimate adapter for:
  - historical price series
  - benchmark data if required
  - sector and industry classification
  - company metadata needed for constraints
- Preserve a deterministic offline fallback only for tests.
- Add request-level control for lookback window and frequency if needed later.

### Deliverables

- Market data provider abstraction.
- FMP-backed implementation.
- Data normalization pipeline that returns aligned prices, returns, expected returns, covariance matrix, and asset metadata.

### Tests

- Unit tests for the provider adapter with mocked FMP responses.
- Tests for missing values, inconsistent dates, and ticker subsets.
- Tests confirming deterministic offline fallback behavior.
- Tests verifying annualization and return-frequency consistency.

## Priority 2: Add an Estimation Pipeline

### Goal

Build a proper preprocessing and estimator layer before optimization so the portfolio models optimize meaningful inputs rather than raw or synthetic placeholders.

### Scope

- Compute returns from aligned price series.
- Support configurable return frequency.
- Add expected return estimation options:
  - sample mean
  - shrinkage-based estimator for mean returns
- Add covariance estimation options:
  - sample covariance
  - shrinkage or regularized covariance
- Use FinanceToolkit utilities where they provide stable, verified analytics instead of duplicating calculations.

### Deliverables

- Estimator module that produces:
  - cleaned returns matrix
  - expected returns vector
  - covariance matrix
  - optional benchmark statistics
- Configuration model for estimation method selection.

### Tests

- Unit tests for return calculations from known price sequences.
- Tests for estimator output shape, PSD handling, and numerical stability.
- Regression tests for shrinkage paths against fixed fixtures.
- Tests for invalid input cases such as too-short history and singular covariance.

## Priority 3: Bring Base Markowitz Models to Parity

### Goal

Make the optimizer layer cover the base formulations represented by the Gurobi notebook family.

### Scope

- Keep and harden:
  - maximize return under risk cap
  - minimize variance under return floor
  - maximize Sharpe ratio
- Add explicit utility maximization with a risk-aversion parameter.
- Add efficient frontier generation instead of only one-off point solutions.
- Separate model construction from solving so that each formulation is testable independently.

### Deliverables

- Refactored optimization module with explicit model builders.
- Frontier generation support.
- Consistent solver result objects.

### Tests

- Unit tests for each formulation using fixed synthetic covariance fixtures.
- Tests verifying weight sum, bounds, feasibility, and monotonic frontier behavior.
- Tests ensuring SCIP and SciPy produce materially similar outputs on continuous models.
- Tests for graceful fallback when one solver path fails.

## Priority 4: Add Factor Model Support

### Goal

Support factor-risk formulations instead of relying only on dense covariance matrices.

### Scope

- Add data structures for:
  - factor exposure matrix
  - factor covariance matrix
  - specific risk vector
- Implement factor model as objective.
- Implement factor model as constraint.
- Allow model inputs to use either full covariance or factor representation.

### Deliverables

- Factor model abstraction.
- SCIP formulations for factor-based optimization.
- Validation utilities to compare factor-implied covariance against dense covariance.

### Tests

- Unit tests for factor-implied risk calculations.
- Tests comparing factor and dense formulations on equivalent inputs.
- Performance-oriented smoke tests for larger asset counts.
- Tests for dimension mismatch and invalid factor data.

## Priority 5: Add Portfolio Constraint Families

### Goal

Introduce the discrete and portfolio-construction constraints currently missing from the API and solver layer.

### Scope

- Add schema support for:
  - minimum buy-in
  - maximum positions and cardinality
  - diversification and position bounds
  - sector allocation limits
  - short-selling and leverage bounds
  - borrowing cash or explicit cash sleeve
  - round lots
- Implement these constraints in SCIP where mixed-integer support is required.
- Expose relaxed behavior clearly when SciPy cannot support a requested formulation.

### Deliverables

- Expanded request and result schemas.
- Constraint builder layer.
- Clear validation errors for unsupported solver-constraint combinations.

### Tests

- Unit tests for each constraint builder.
- Mixed-integer feasibility tests with small portfolios.
- Tests verifying cardinality and minimum-position logic.
- Tests for sector caps using mocked metadata from FMP Ultimate.

## Priority 6: Add Rebalancing and Transaction Cost Models

### Goal

Support optimization from current holdings rather than only from an all-cash start.

### Scope

- Add request fields for current holdings and current weights.
- Implement turnover calculations.
- Add support for:
  - fixed transaction costs
  - proportional transaction fees
  - turnover constraints
  - market impact penalties or approximations
- Separate portfolio construction from rebalancing workflows.

### Deliverables

- Rebalancing model path.
- Transaction-cost-aware budget equations.
- Solver outputs that include turnover and estimated cost breakdown.

### Tests

- Unit tests for turnover and cost calculations.
- Tests comparing optimized output with and without transaction costs.
- Rebalancing tests starting from non-zero holdings.
- Tests for infeasible rebalance requests under tight constraints.

## Priority 7: Replace Heuristic Ranking With Output-Driven Selection

### Goal

Reduce reliance on static heuristic ranking and rank portfolios using actual optimization outputs and user constraints.

### Scope

- Use optimized risk and return metrics instead of static preference tables.
- Keep user risk tolerance and horizon as preference weights, not hard-coded rank order.
- Add explicit explanation fields for why a portfolio was ranked higher.

### Deliverables

- Refactored ranking logic.
- Transparent scoring model based on actual metrics.

### Tests

- Tests for ranking consistency under controlled result sets.
- Tests ensuring infeasible or degraded solutions rank below feasible solutions.
- Tests for explanation generation.

## Priority 8: API and Documentation Alignment

### Goal

Expose the expanded optimization capability through a stable API and document solver limitations clearly.

### Scope

- Expand request models to include estimator settings, constraints, holdings, and transaction cost parameters.
- Expand response models with diagnostics:
  - solver used
  - optimization status
  - feasibility warnings
  - turnover and cost metrics
- Document which features require SCIP and which support SciPy fallback.

### Deliverables

- Updated FastAPI request and response contracts.
- API documentation and examples.

### Tests

- API tests for new request validation.
- Contract tests for response payload shape.
- Error-path tests for unsupported combinations.

## Recommended Delivery Sequence

1. FMP-backed data provider and metadata pipeline.
2. Estimation pipeline using FinanceToolkit where appropriate.
3. Base Markowitz model parity and frontier support.
4. Factor model support.
5. Constraint families.
6. Rebalancing and transaction costs.
7. Ranking cleanup.
8. API expansion and docs.

## Test Strategy Summary

### Unit Tests

- Keep unit tests deterministic with fixed fixtures and mocked FMP responses.
- Test mathematical components separately from solver integration.
- Use small asset universes for mixed-integer model tests.

### Integration Tests

- Add integration tests for end-to-end optimize flows using mocked provider responses.
- Validate the full chain:
  - data fetch
  - preprocessing
  - estimation
  - optimization
  - ranking

### Solver Validation Tests

- Compare SCIP and SciPy on continuous formulations.
- Explicitly mark mixed-integer formulations as SCIP-only.
- Add tolerances for numerical equivalence rather than exact equality.

### Regression Tests

- Store small canonical fixtures for prices, returns, metadata, and expected outputs.
- Protect against silent changes in annualization, covariance scaling, and ranking behavior.

### Non-Goals For Initial Iteration

- Live integration tests against FMP Ultimate.
- Full market-impact calibration from real execution data.
- Large-scale benchmark parity with the full Gurobi notebook dataset.

## First Milestone

The first milestone should stop after these items are complete:

1. FMP Ultimate data adapter.
2. FinanceToolkit-backed estimation layer.
3. Refactored base Markowitz models.
4. Deterministic tests for the full base optimization path.

That milestone delivers a credible replacement for the current synthetic optimizer and provides the foundation needed for factor models, rebalancing, and mixed-integer constraints.
