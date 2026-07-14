# Test guide

Separate static checks from hardware tests.

## Static checks

```bash
python3 scripts/validate-factory.py
python3 scripts/refresh-documentation.py
python3 scripts/refresh-documentation.py --check
```

For AIC8800, use the export and check scripts only with a Linux tree you allow
the scripts to modify. Their output is local validation evidence, not a
hardware test result.

## Hardware evidence

Every hardware result must identify:

1. Source revision and generated-output state.
2. Exact Image and DTB used (checksum or immutable copy preferred).
3. Board variant and power/boot media.
4. Complete serial or console log.
5. Commands, observed result, and failure details.

Do not update permanent documentation from a recollection of a boot. Store the
test record first, then refresh the generated status report.
