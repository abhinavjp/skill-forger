## Outcome
A guest cart holds at most 10 items (REQ-001) and says why (REQ-002).

## Write scope
app/cart.cfg

## Must not change
Signed-in cart behaviour.

## Changes
Set the guest cart item limit.

## Proof
REQ-001, run from the application root; expected exit code 0:

`git grep --no-index -w -F "guest_max_items=10" -- app/cart.cfg`

REQ-002: human observation only; no automated proof.

## Depends on
none
