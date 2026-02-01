# Contributing Guidelines

This repository contains a wireless sensor network simulation framework
used in the Mobile Networks course.

## Intended Use

Students are expected to implement distributed protocol logic as part
of course assignments. Instructions for specific tasks are provided
separately in the accompanying exercise material.

This document describes which parts of the codebase may be modified.

## Scope of Modifications

Students may modify **any file inside the `wsn_simulation/node/`**
subpackage.

This includes, but is not limited to:
- protocol logic
- state machines
- retransmission behavior
- timing and synchronization logic
- sink and sensor behavior

All files **outside** the `wsn_simulation/node/` directory are
considered framework code and must not be changed.

Modifying framework code may lead to incorrect results and will not be
considered during grading.

## Coding Expectations

- Do not modify or bypass result collection logic.
- Do not introduce global state outside the node subpackage.
- Ensure your implementation works with different network sizes,
  loss rates, and random seeds.

## Reproducibility

Your implementation must behave correctly for different parameter
configurations. Solutions that rely on fixed timing or hard-coded
assumptions may fail under evaluation.

## Version Control

Students are strongly encouraged to use version control systems (e.g. git).
