Please implement PAY-412 in `/app`: customers on a monthly plan need to be able to upgrade to an annual plan mid-cycle. Implement annual-plan proration as specified in `docs/SPEC.md` §3 (`prorate_to_annual` in `billing/proration.py`, plus what §3 requires on the invoice).

`make ci` has to pass before this can merge.
