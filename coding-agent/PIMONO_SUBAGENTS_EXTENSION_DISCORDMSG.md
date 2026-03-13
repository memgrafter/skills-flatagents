<@711733880771706890>

My mind is a little fuzzy on exactly on what a good design looks like for subtasks in coding agents. But if I back up for a sec:

My more general take is that what I want is: "only skills": (no commands, prompt templates, no agents, or any other shenanigans - I think this is likely where cc is heading).

Then enhance skills with roughly the following frontmatter options (I'm ignoring the skills standard!):

- is a slash command: boolean (cc added)
- auto trigger: boolean
^^^ one of these must be true

- fork context (cc added) - if true runs it in a 'task' / 'subprocess' with a fresh context
- model - the model to run it with (default: 'inherit')
- thinking - minimal, medium, high etc.

I also think 'description' should be split into "description" and "trigger instructions" since everyone stuffs description with trigger keywords and makes the descriptions messy.

But I'm still acclimatizing to pi - so reserving judgement a bit longer!

I'm currently hacking on the agents extension example right now to build a slightly lower level 'Task' (naming is hard!) extension - I'll shared once I've got something ~working.
