# Staff Classification Review

## Summary

Staff exclusion is implemented and tested. The supplied footage does not
demonstrate a positive staff classification because the canonical generated
stream contains no `is_staff=true` events.

## Implementation

The tracker uses a transparent long-presence proxy:

```python
state.is_staff = state.is_staff or timestamp - state.first_seen >= timedelta(minutes=8)
```

Emitted events preserve `is_staff`, the database stores it, and analytics
exclude staff rows with:

```sql
SELECT * FROM events WHERE store_id=? AND is_staff=0
```

## Automated Test Evidence

`tests/test_api.py::test_all_staff_events_are_excluded` ingests staff-marked
events and verifies that visitor metrics remain zero. The broader metrics test
also includes a staff entry alongside a customer session.

## Dataset Evidence

```text
canonical_events=326
is_staff_true=0
is_staff_false=326
```

## Assessment

| Question | Result |
|---|---|
| Feature implemented? | Yes |
| API exclusion tested? | Yes |
| Demonstrated by supplied footage? | No |

The implementation should be described as a conservative proxy, not a
validated uniform classifier. No synthetic staff events were added to the
canonical artifact.
