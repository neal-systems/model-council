# Delegation plan contract

A plan is derived from a recorded cut. Every `part` has an ID, one bounded
question, its own acceptance statement, a treatment, and explicit dependencies.
Anything marked `whole` remains an owner decision and is never dispatched.

Dependencies are returned as ordered waves. Missing dependencies and cycles are
errors because silently dropping them would create a plan that cannot be run.
The plan describes work; it does not claim that work ran.
