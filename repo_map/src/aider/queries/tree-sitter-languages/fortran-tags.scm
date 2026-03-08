;; Copyright (C) 2023-2026 Paul Gauthier and Aider contributors
;; SPDX-License-Identifier: Apache-2.0
;; Licensed under the Apache License, Version 2.0

;; derived from: https://github.com/stadelmanma/tree-sitter-fortran
;; License: MIT

(module_statement
  (name) @name.definition.class) @definition.class

(function_statement
  name: (name) @name.definition.function) @definition.function

(subroutine_statement
  name: (name) @name.definition.function) @definition.function

(module_procedure_statement
  name: (name) @name.definition.function) @definition.function
   