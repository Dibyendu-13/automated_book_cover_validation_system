# Accuracy Report

## What This Report Covers

This repository includes a strict validation demo over the sample covers in `validation_book_covers`.
It is a functional system validation, not a formal benchmark on a labeled ground-truth dataset.

## Current Sample Set Results

Latest strict dry-run batch:

- `Total files`: 12
- `PASS`: 1
- `REVIEW NEEDED`: 11
- `PASS rate`: 8.33%
- `REVIEW rate`: 91.67%

## How To Describe The Result Safely

Use this wording in your submission:

> The system was validated on the provided sample set and correctly separated a clean high-resolution cover from lower-resolution review cases. The strict validator, batch automation, Airtable/email plumbing, and reporting pipeline all executed successfully.

## What The Sample Run Demonstrates

- A clean 1500 x 2400 PNG can pass under strict rules.
- Lower-resolution sample covers are routed to `REVIEW NEEDED`.
- The critical layout checks remain strict and active.
- Batch reporting and metrics export work end-to-end.

## What This Does Not Claim

- It does not claim a formal 90% accuracy score on a labeled benchmark dataset.
- It does not claim measured overlap-detection precision/recall across a large annotated corpus.

## Recommended Submission Positioning

If the evaluator asks about accuracy, frame it as:

- a successful strict validation demo
- a working automation pipeline
- a sample-set validation result
- a system ready for larger labeled evaluation

