# Matching Service

The matching service compares a user's observed LEGO inventory against candidate set inventories.

## Rules

For exact matching, a set is complete when for every `(part_id, color_id)`:

`available_quantity >= required_quantity`

The engine should also expose:

- missing quantity by piece
- supplied/required totals
- exact completeness ratio
- exact-build boolean
- deterministic ranking inputs

Future modes can add color-flexible and approved substitution rules without changing the exact-match contract.
