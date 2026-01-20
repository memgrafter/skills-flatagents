"""Hooks for JSON extractor machine."""

import json
import re
from flatagents import MachineHooks


class JSONExtractorHooks(MachineHooks):
    """Hooks for JSON extraction machine."""

    def on_action(self, action: str, context: dict) -> dict:
        """Handle custom actions."""
        if action == "parse_json":
            return self._parse_json(context)
        return context

    def _parse_json(self, context: dict) -> dict:
        """Parse JSON from raw agent output with multiple fallback strategies."""
        raw_output = context.get("raw_output", "")

        if not raw_output:
            context["extraction_error"] = "No output to parse"
            context["extracted"] = {}
            return context

        # Strategy 1: Direct JSON parse
        try:
            context["extracted"] = json.loads(raw_output)
            return context
        except json.JSONDecodeError:
            pass

        # Strategy 2: Find JSON object in text
        json_match = re.search(r'\{[^{}]*\}', raw_output, re.DOTALL)
        if json_match:
            try:
                context["extracted"] = json.loads(json_match.group())
                return context
            except json.JSONDecodeError:
                pass

        # Strategy 3: Find JSON with nested objects
        json_match = re.search(r'\{.*\}', raw_output, re.DOTALL)
        if json_match:
            try:
                # Clean up common issues
                json_str = json_match.group()
                json_str = re.sub(r',\s*}', '}', json_str)  # Remove trailing commas
                json_str = re.sub(r',\s*]', ']', json_str)  # Remove trailing commas in arrays
                context["extracted"] = json.loads(json_str)
                return context
            except json.JSONDecodeError:
                pass

        # Strategy 4: Extract from markdown code block
        code_block_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', raw_output)
        if code_block_match:
            try:
                context["extracted"] = json.loads(code_block_match.group(1))
                return context
            except json.JSONDecodeError:
                pass

        # Strategy 5: Line-by-line key:value extraction (fallback for evaluation format)
        extracted = {}
        schema_hints = context.get("schema", "").lower()

        for line in raw_output.split('\n'):
            line = line.strip()
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip().lower().replace(' ', '_')
                value = value.strip()

                # Try to parse value
                if key in ['score'] or 'score' in key:
                    try:
                        # Handle "0.8/1.0" or "0.8" or "80%"
                        value = value.split('/')[0].strip()
                        value = value.replace('%', '')
                        extracted['score'] = float(value) / 100 if float(value) > 1 else float(value)
                    except ValueError:
                        pass
                elif key in ['depth'] or 'depth' in key:
                    value_lower = value.lower()
                    if 'deep' in value_lower:
                        extracted['depth'] = 'deep'
                    elif 'partial' in value_lower:
                        extracted['depth'] = 'partial'
                    else:
                        extracted['depth'] = 'surface'
                elif key in ['gaps'] or 'gap' in key:
                    items = [g.strip() for g in value.split(',') if g.strip() and g.strip().lower() not in ['none', 'n/a', 'null']]
                    extracted['gaps'] = items
                elif key in ['strengths'] or 'strength' in key:
                    items = [s.strip() for s in value.split(',') if s.strip() and s.strip().lower() not in ['none', 'n/a', 'null']]
                    extracted['strengths'] = items

        if extracted:
            context["extracted"] = extracted
            return context

        # Final fallback: empty dict with error
        context["extraction_error"] = f"Could not parse JSON from: {raw_output[:200]}..."
        context["extracted"] = {}
        return context
