"""
OTF Agent Hooks

Provides:
- human_review_otf: Human-in-the-loop review of supervisor analysis
- otf_execute: Execute the approved OTF agent
"""

import json
import asyncio
from typing import Any, Dict
import logging
from flatagents import MachineHooks, FlatAgent

# Allow nested event loops for running async code from sync hooks
import nest_asyncio
nest_asyncio.apply()

logger = logging.getLogger(__name__)


class OTFAgentHooks(MachineHooks):
    """
    Hooks for On-The-Fly agent execution with human-in-the-loop.

    Handles two actions:
    - human_review_otf: Review supervisor's analysis with conditional options
    - otf_execute: Create and run the OTF agent from context spec
    """

    def __init__(self, auto_approve: bool = False):
        self.auto_approve = auto_approve
        self.metrics = {
            "agents_generated": 0,
            "agents_executed": 0,
            "supervisor_rejections": 0,
            "human_denials": 0,
        }
    
    def on_action(self, action_name: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle custom actions."""
        if action_name == "human_review_otf":
            return self._human_review_otf(context)
        elif action_name == "otf_execute":
            return self._otf_execute(context)
        return context
    
    def _human_review_otf(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Human reviews the supervisor's analysis of the OTF agent spec.
        
        If supervisor rejected: Human can only acknowledge (no override)
        If supervisor approved: Human can approve or deny
        """
        print("\n" + "=" * 70)
        print("OTF AGENT REVIEW")
        print("=" * 70)
        
        # Show the original task
        print(f"\n📋 ORIGINAL TASK:")
        print(f"   {context.get('task', '(unknown)')}")
        
        # Show the generated agent spec from individual fields
        name = context.get("otf_name", "unnamed")
        system = context.get("otf_system", "(none)")
        user = context.get("otf_user", "(none)")
        temperature = context.get("otf_temperature", "N/A")
        
        print(f"\n🤖 GENERATED AGENT: {name}")
        print("-" * 50)
        print(f"Temperature: {temperature}")
        system_preview = str(system)[:500] if system else "(none)"
        print(f"\nSystem Prompt:\n{system_preview}...")
        user_preview = str(user)[:300] if user else "(none)"
        print(f"\nUser Prompt Template:\n{user_preview}...")
        
        # Show supervisor's analysis
        print("\n" + "-" * 50)
        supervisor_approved = context.get("supervisor_approved", False)
        
        if supervisor_approved:
            print("✅ SUPERVISOR APPROVED")
        else:
            print("❌ SUPERVISOR REJECTED")
            self.metrics["supervisor_rejections"] += 1
        
        print(f"\n📊 ANALYSIS:\n{context.get('supervisor_analysis', '(none)')}")
        
        if context.get("supervisor_concerns"):
            print(f"\n⚠️  CONCERNS:\n{context.get('supervisor_concerns')}")
        
        print("-" * 50)

        # Auto-approve mode: skip human review, auto-approve if supervisor approved
        if self.auto_approve:
            if supervisor_approved:
                context["human_approved"] = True
                context["human_acknowledged"] = True
                print("\n[Auto-approve] ✓ Approved! Agent will be executed.")
            else:
                context["human_approved"] = False
                context["human_acknowledged"] = True
                print("\n[Auto-approve] → Regenerating based on supervisor feedback.")
            print("=" * 70 + "\n")
            return context

        # Different options based on supervisor decision
        if supervisor_approved:
            print("\nThe supervisor approved this agent.")
            response = input("Your decision: [a]pprove / [d]eny / [q]uit: ").strip().lower()

            if response in ("a", "approve", ""):
                context["human_approved"] = True
                context["human_acknowledged"] = True
                print("✓ Approved! Agent will be executed.")
            elif response in ("q", "quit"):
                print("Quitting...")
                raise KeyboardInterrupt()
            else:
                context["human_approved"] = False
                context["human_acknowledged"] = True
                self.metrics["human_denials"] += 1
                print("✗ Denied. Will regenerate agent.")
        else:
            print("\nThe supervisor rejected this agent. You can only acknowledge.")
            response = input("Press Enter to acknowledge and regenerate, or 'q' to quit: ").strip().lower()

            if response in ("q", "quit"):
                print("Quitting...")
                raise KeyboardInterrupt()

            context["human_approved"] = False
            context["human_acknowledged"] = True
            print("→ Acknowledged. Will regenerate agent with feedback.")

        print("=" * 70 + "\n")
        return context
    
    def _otf_execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create and execute the OTF agent from the approved spec fields.
        """
        # Get spec from individual context fields
        name = context.get("otf_name", "otf-agent")
        system = context.get("otf_system", "You are a helpful creative writer.")
        user = context.get("otf_user", "{{ input.task }}")
        temperature = context.get("otf_temperature", 0.7)
        output_fields_raw = context.get("otf_output_fields", "{}")
        
        print("\n" + "=" * 70)
        print(f"🚀 EXECUTING OTF AGENT: {name}")
        print("=" * 70)
        
        # Parse output_fields if it's a string
        output_fields = {}
        if isinstance(output_fields_raw, str):
            try:
                output_fields = json.loads(output_fields_raw)
            except json.JSONDecodeError:
                output_fields = {}
        elif isinstance(output_fields_raw, dict):
            output_fields = output_fields_raw
        
        # Convert output_fields to proper schema format
        output_schema = {}
        if isinstance(output_fields, dict):
            for field_name, field_def in output_fields.items():
                if isinstance(field_def, dict):
                    output_schema[field_name] = field_def
                else:
                    # Simple type
                    output_schema[field_name] = {"type": "str", "description": str(field_def)}
        
        # Default output if none specified
        if not output_schema:
            output_schema = {
                "content": {"type": "str", "description": "The creative writing output"}
            }
        
        # Ensure temperature is a float and normalize to allowed values
        if isinstance(temperature, str):
            try:
                temperature = float(temperature)
            except ValueError:
                temperature = 0.6
        if temperature != 1.0:
            temperature = 0.6

        normalized_user = str(user).replace("<<input.task>>", "{{ input.task }}").strip()
        
        agent_config = {
            "spec": "flatagent",
            "spec_version": "0.7.1",
            "data": {
                "name": name,
                "model": {
                    "profile": "default",
                    "temperature": temperature
                },
                "system": system,
                "user": normalized_user,
                "output": output_schema
            }
        }
        
        try:
            # Create the agent with profiles from context
            profiles_dict = context.get("_profiles")
            agent = FlatAgent(config_dict=agent_config, profiles_dict=profiles_dict)
            self.metrics["agents_generated"] += 1
            
            # Execute it
            import asyncio
            result = asyncio.run(agent.call(task=context.get("task", "")))
            
            self.metrics["agents_executed"] += 1
            
            # Store result
            if result.output:
                context["otf_result"] = result.output
            elif result.content:
                context["otf_result"] = {"content": result.content}
            else:
                context["otf_result"] = {"content": "(empty response)"}
            
            print("\n📝 OUTPUT:")
            print("-" * 50)
            if isinstance(context["otf_result"], dict):
                for key, value in context["otf_result"].items():
                    print(f"{key}: {value}")
            else:
                print(context["otf_result"])
            print("-" * 50)
            
        except Exception as e:
            logger.error(f"OTF agent execution failed: {e}")
            context["otf_result"] = {"error": str(e)}
            print(f"\n❌ Error: {e}")
        
        print("=" * 70 + "\n")
        return context
    
    def get_metrics(self) -> Dict[str, Any]:
        """Return collected metrics."""
        return self.metrics.copy()
