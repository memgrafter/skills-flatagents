;; Copyright (C) 2023-2026 Paul Gauthier and Aider contributors
;; SPDX-License-Identifier: Apache-2.0
;; Licensed under the Apache License, Version 2.0

(binary_operator
    lhs: (identifier) @name.definition.function
    operator: "<-"
    rhs: (function_definition)
) @definition.function

(binary_operator
    lhs: (identifier) @name.definition.function
    operator: "="
    rhs: (function_definition)
) @definition.function

(call
    function: (identifier) @name.reference.call
) @reference.call

(call
    function: (namespace_operator
        rhs: (identifier) @name.reference.call
    )
) @reference.call
