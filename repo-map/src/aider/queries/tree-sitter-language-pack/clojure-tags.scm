;; Copyright (C) 2023-2026 Paul Gauthier and Aider contributors
;; SPDX-License-Identifier: Apache-2.0
;; Licensed under the Apache License, Version 2.0

(list_lit
  meta: _*
  . (sym_lit name: (sym_name) @ignore)
  . (sym_lit name: (sym_name) @name.definition.method)
  (#match? @ignore "^def.*"))

(sym_lit name: (sym_name) @name.reference.call)
