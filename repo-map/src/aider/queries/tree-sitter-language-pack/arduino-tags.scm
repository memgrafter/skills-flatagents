;; Copyright (C) 2023-2026 Paul Gauthier and Aider contributors
;; SPDX-License-Identifier: Apache-2.0
;; Licensed under the Apache License, Version 2.0

(function_declarator
  declarator: (identifier) @name.definition.function) @definition.function

(call_expression
  function: (identifier) @name.reference.call) @reference.call
