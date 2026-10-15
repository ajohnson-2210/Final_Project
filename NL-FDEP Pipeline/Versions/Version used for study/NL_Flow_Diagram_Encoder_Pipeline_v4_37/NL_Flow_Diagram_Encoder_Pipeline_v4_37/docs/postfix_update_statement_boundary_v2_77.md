# Postfix update statement-boundary correction — v2.77

## Scope

This change applies to generic compatibility normalisation when a physical source line ends in an explicit postfix increment or decrement:

    i++
    j--

and to compressed variants such as:

    i++, j++
    ELSE IF A[i] < B[j] THEN i++
    ELSE j++

## Root cause

The expression-continuation pass recognises a trailing arithmetic operator as evidence that the next physical line belongs to the same expression. Before v2.77, the final `+` in `i++` and final `-` in `j--` were therefore mistaken for dangling binary operators.

That could collapse subsequent branch lines into the postfix-update line before the existing increment/decrement, multiple-statement, and inline-branch normalisers had an opportunity to process them.

## Canonical boundary rule

A line whose final non-whitespace token is `++` or `--` is a complete statement boundary for continuation detection.

The ordinary continuation behaviour remains unchanged for genuine multiline expressions, for example:

    total <- a +
        b

No comma handling is broadened by this correction. Commas inside expressions and function-call argument lists retain their existing behaviour.

## Structural classification

This is structural recovery only.

- semantic inference: NONE
- algorithmic reconstruction: NO
- control-flow change: NO
- missing operation insertion: NO

The correction prevents premature physical-line joining and allows existing generic normalisation rules to operate on source operations that are already explicit.

## Regression coverage

v2.77 adds regression coverage for:

- source_b Algorithm 4's exact postfix/inlined-branch shape;
- postfix decrement followed by another statement;
- a genuine multiline arithmetic continuation ending in `+`;
- commas inside function-call arguments.

The distributable unit/regression suite passes after the correction.
