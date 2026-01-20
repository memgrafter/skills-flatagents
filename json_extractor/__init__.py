"""JSON Extractor - Generic machine for extracting structured JSON from natural language.

Part of the Split-Brain pattern:
1. Scorer/Reasoner: Generates verbose, unconstrained natural language
2. Extractor (this): Converts that to bulletproof JSON
"""

from json_extractor.hooks import JSONExtractorHooks

__all__ = ["JSONExtractorHooks"]
