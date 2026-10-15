# source_e Algorithm 5 — regex `REPLACE_ALL` compatibility recovery (v3.25)

source_e 5 supplies the complete operation:

```text
FUNCTION REMOVE_PUNCTUATION(sentence)
  RETURN REPLACE_ALL(sentence, "[^a-zA-Z0-9\s]", "")
END FUNCTION
```

The pattern itself is direct evidence that `REPLACE_ALL` is being used as a regular-expression substitution operation: it contains a negated character class and the regex whitespace escape `\s`.

## GC227 — evidenced regex `REPLACE_ALL`

GC227 is deliberately narrower than a global `REPLACE_ALL` rewrite. It activates only for a free call with exactly three top-level arguments where both pattern and replacement are quoted literals and the pattern contains direct regex syntax evidence. Member methods, other arities, and plain literal replacement calls remain untouched.

Before frozen AJ string lexing, GC227 protects backslashes inside the supplied regex pattern and replacement so regex escapes such as `\s` and replacement backreferences survive representation unchanged. The compatibility form is then:

```text
RETURN CALL regex_replace(sentence, STRING("[^a-zA-Z0-9\\s]"), EMPTY STRING)
```

`regex_replace` is an internal compatibility intrinsic and lowers to Python `re.sub(pattern, replacement, text)`. It adds no new frozen AJ grammar.

For the supplied example, `"Hello, world!"` becomes `"Hello world"`, and whitespace remains preserved by the source-supplied `\s` expression.

AJ_24038155 Dialect v1.1 remains frozen.
