# NL-FDEP v4.13 — AJ_24038155 Dialect v1.4 runtime type inspection

Pipeline: **NL-FDEP v4.13**  
Dialect: **AJ_24038155 Dialect v1.4**

## Change

v4.13 advances the active language from AJ v1.3 to v1.4 and adds the explicit runtime type-inspection intrinsic `CALL ISINSTANCE(value, type_reference)`. The change is motivated by frozen baseline Algorithm 19, whose reference Python explicitly uses `isinstance(...)` to select numeric, string and mixed-type swap behaviour.

The parser emits a dedicated `IsInstanceNode`; the flow representation preserves the test explicitly; the compiler lowers built-in AJ type names to Python type objects and emits Python `isinstance(...)`.

No implicit type inspection or conversion is introduced. Existing v1.3 casts and `QUIT` semantics are unchanged.
