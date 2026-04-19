;; Copyright (C) 2023-2026 Paul Gauthier and Aider contributors
;; SPDX-License-Identifier: Apache-2.0
;; Licensed under the Apache License, Version 2.0

(class_definition
  name: (identifier) @name.definition.class) @definition.class

(function_definition
  name: (identifier) @name.definition.function) @definition.function

(function_call
  name: (identifier) @name.reference.call) @reference.call

(command (command_name) @name.reference.call) @reference.call