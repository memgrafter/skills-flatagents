# Socratic Learning Session: distributed systems
Generated: 2026-01-19T16:28:32.653622

## Round 1
**Question:** Why would a software engineer choose to build an application using many different computers connected by a network instead of just one very powerful computer?
**Response:** This is related to vertical versus horizontal scaling. Today, vertical scaling is dominant, but has limits, so once you have scaled vertically, you must horizontally scale.  There may be some cases where horizontal scaling is preferred, but it's not common and I don't know of them, because having everything on device is always advantageous. Network is costly.  The horizontal scaling provides a much higher limit on available resources such as compute, memory, sockets, and total bandwidth, and edge availability, and comes at a large cost regarding network communication and maintenance.
**Score:** 0.40/1.0
**Depth:** partial

## Summary
**Final Mastery Score:** 0.40/1.0
**Identified Gaps:** not vertical), incorrect belief that single-device setups are "always advantageous, " overlooking the cost-effectiveness of commodity hardware versus specialized mainframes, failure to identify fault tolerance or high availability as primary drivers, fundamental misunderstanding of industry prevalence (horizontal scaling is dominant in modern cloud architectures
**Strengths:** recognizes edge availability as a benefit, correctly uses technical terminology (vertical vs. horizontal scaling), correctly identifies the trade-off between resource limits and complexity/overhead
**Rounds:** 1/1
**Termination Reason:** max_rounds