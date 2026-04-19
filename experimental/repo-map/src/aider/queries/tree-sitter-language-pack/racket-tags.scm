;; Copyright (C) 2023-2026 Paul Gauthier and Aider contributors
;; SPDX-License-Identifier: Apache-2.0
;; Licensed under the Apache License, Version 2.0

(list
  .
  (symbol) @reference._define
  (#match? @reference._define "^(define|define/contract)$")
  .
  (list
    .
    (symbol) @name.definition.function) @definition.function)

(list
  .
  (symbol) @name.reference.call)
