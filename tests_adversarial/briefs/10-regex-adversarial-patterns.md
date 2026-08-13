# Regex Stress Test Requirements

## Functional Requirements

- THE System SHALL process input strings matching the pattern aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaab without catastrophic backtracking.
- WHEN the user enters a value like "((((((((((((((((((((nested)))))))))))))))))))))", THE System SHALL validate bracket balance within 100ms.
- THE System SHALL reject filenames containing the characters \, /, :, *, ?, ", <, >, | per the POSIX specification.
- WHEN the log line reads "is been are were was being be been edited", THE System SHALL not misinterpret this as passive voice in a quoted context.
- THE System SHALL accept requirement text that includes regex-like metacharacters: ^$.*+?()[]{}|\\ without parser failure.
- IF the user submits a field value of exactly "ly ly ly ly ly ly ly ly ly ly ly ly ly ly ly ly ly ly ly ly", THEN THE System SHALL store it without triggering adverb warnings on non-word boundaries.
- THE System SHALL handle the edge case where a requirement line is exactly: "...".
- WHEN the input contains consecutive EARS keywords with no spacing such as "WHENWHENWHENWHEN", THE System SHALL not enter an infinite loop.
- THE System SHALL support requirement IDs containing dots, hyphens, and underscores: REQ-2.1_alpha.
- WHILE the parser is processing a line containing 1000 consecutive word characters without spaces (aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa), THE System SHALL complete parsing without timeout.
