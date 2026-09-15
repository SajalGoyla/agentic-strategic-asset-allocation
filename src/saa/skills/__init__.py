"""Deterministic skills shared by agents (Ang, Azimbayev & Kim 2026, Section 3.2).

A skill is a methodology document (``SKILL.md``) plus Python that does the computation. Skills read
data only through ``DataStore``, return typed output models, and never call an LLM; agents call
them and reason about the results.
"""
