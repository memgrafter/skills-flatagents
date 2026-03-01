# Typed Hook Actions for Compiled SDKs

Problem
The current hook action interface is stringly-typed: `action: write_files`
routes to `onAction("write_files", ...)`. This is awkward for compiled languages
and makes it easy to drift between machine specs and hook implementations.

Goals
- Provide a typed surface for hook actions in compiled SDKs (enum/consts).
- Allow runtime validation that declared actions are implemented.
- Keep the YAML model simple and backward compatible.

Proposal A: Declare Actions in the Machine Spec

Add an optional `actions` registry to `flatmachine.d.ts`:

data:
  actions:
    write_files:
      description: "Apply SEARCH/REPLACE diffs"
      input_schema:
        changes: string
        working_dir: string
        user_cwd: string
      output_schema:
        applied_changes: list
        apply_errors: list

States can continue to reference the action by name:

states:
  write:
    action: write_files

Benefits:
- Schema-driven codegen: compiled SDKs can emit `enum ActionId`.
- Runtime validation: fail fast if `action` is not declared.

Proposal B: Action Bindings in Hooks Config

Add an optional action binding map under `hooks`:

hooks:
  module: shared.file_write_machine
  class: FileWriteHooks
  actions:
    write_files: write_files

Benefits:
- Runtime can check that declared actions exist on hooks.
- Allows multiple hooks or adapter layers to expose a stable action name.

Recommended Path
Adopt Proposal A as the primary typed surface (codegen target) and allow
Proposal B as a runtime validation layer when hooks are used.

Compatibility
- Existing machines remain valid (actions remain optional).
- SDKs can treat `actions` as advisory until they implement validation.

Runtime Interface Notes
- Keep `onAction(action: string, context: dict)` for compatibility.
- For typed SDKs, expose `onAction(action: ActionId, ...)` and map to string.
- If `actions` is declared, validate `state.action` against it at load time.
- Optionally validate that hooks expose the declared actions.

Example (Combined)

spec: flatmachine
spec_version: "0.7.7"

data:
  name: file-writer
  actions:
    write_files:
      description: "Apply SEARCH/REPLACE diffs"
      input_schema:
        changes: string
        working_dir: string
        user_cwd: string
      output_schema:
        applied_changes: list
        apply_errors: list
  hooks:
    module: shared.file_write_machine
    class: FileWriteHooks
    actions:
      write_files: write_files

  states:
    start:
      type: initial
      transitions:
        - to: write
    write:
      action: write_files
      transitions:
        - to: done
    done:
      type: final
      output:
        applied_changes: "{{ context.applied_changes }}"
        apply_errors: "{{ context.apply_errors }}"

Notes for Codegen
- Emit `enum ActionId { WriteFiles = "write_files" }`
- Emit input/output structs if `input_schema`/`output_schema` are defined.
- Allow SDKs to reject undeclared action strings at parse time.
