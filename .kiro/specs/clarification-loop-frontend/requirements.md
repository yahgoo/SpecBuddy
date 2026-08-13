# Requirements: Clarification Loop Frontend

## Overview

Add a "Clarify" action to each finding in the analysis view that invokes the
clarification endpoint, presents two rewrite options (A and B), and persists
the user's selection. The UI makes no speculative state changes; the full
analysis state refreshes in a single update after the server completes the
persist-and-rescore transaction.

This spec is the frontend counterpart to the clarification-loop-backend spec.

---

## Functional Requirements

### FR-1: Clarify Button Per Finding

WHEN the system displays a finding card THE System SHALL render a "Clarify" button on that card.

WHEN a finding has a suggested rewrite THE System SHALL display the "Clarify" button alongside the existing rewrite-action button.

WHEN a finding has no suggested rewrite THE System SHALL display the "Clarify" button as the sole action.

WHEN any clarify or rewrite operation is in-flight THE System SHALL disable all action buttons across all finding cards.

### FR-2: Fetch Clarification Options

WHEN the user clicks the "Clarify" button on a finding THE System SHALL send a request to the clarification endpoint with the spec identifier, line number, and check identifier.

WHEN the clarification request is in-flight THE System SHALL change the button text to "Loading…" and disable all action buttons.

WHEN the clarification request is in-flight THE System SHALL keep the score, findings, and rewrites unchanged.

WHEN the clarification request succeeds THE System SHALL expand an inline options panel on the finding card.

WHEN the clarification request fails with an error THE System SHALL display an inline error message beneath the finding card and restore all buttons to their idle state.

### FR-3: Display Two Options

WHEN the options panel opens THE System SHALL display the current effective line text above two option cards labelled "A" and "B".

WHEN the system renders an option card THE System SHALL show the label as a badge, the rewritten text in a monospace block, and the rationale as helper text beneath the rewritten text.

WHEN the options panel is visible THE System SHALL display a "Select A" button on option A and a "Select B" button on option B.

WHEN the options panel is visible THE System SHALL display a "Cancel" button that dismisses the panel without sending any request.

WHEN the options panel is visible THE System SHALL not display free-text input or additional options beyond A and B.

### FR-4: Persist Selected Option

WHEN the user clicks "Select A" or "Select B" THE System SHALL send a selection request to the persist endpoint with the spec identifier, line number, check identifier, and selected label.

WHEN the selection request is in-flight THE System SHALL change the clicked button text to "Applying…" and disable all buttons in the options panel.

WHEN the selection request is in-flight THE System SHALL keep the score, verdict, tier, findings, and rewrites unchanged.

WHEN the selection request succeeds THE System SHALL replace the entire analysis state with the full response in a single state update.

WHEN the selection request returns a conflict error THE System SHALL display an inline message "Line has changed — please re-clarify." and collapse the options panel.

WHEN the selection request returns any other error THE System SHALL display the error message inline beneath the finding and collapse the options panel.

### FR-5: No Speculative UI Changes

WHILE any clarify or selection request is in-flight THE System SHALL not update the score, verdict, tier, findings, rewrites, requirements, or report fields.

WHEN the analysis state updates THE System SHALL derive the new state from the server response rather than from local computation.

### FR-6: Single State Update

WHEN a successful selection response arrives THE System SHALL update all derived views (score card, stats row, mission board, findings list, accepted rewrites, parsed requirements, and report) in a single render cycle.

WHEN a successful selection response arrives THE System SHALL not produce intermediate renders showing partial new data.

---

## Non-Functional Requirements

### NFR-1: Service Module Extension

THE System SHALL expose a function that accepts a spec identifier, line number, and check identifier and returns a promise resolving to the clarification response containing options.

THE System SHALL expose a function that accepts a spec identifier, line number, check identifier, and selected label and returns a promise resolving to the full analysis response.

WHEN either function receives a non-success status THE System SHALL throw an error containing the detail text from the response body.

### NFR-2: Type Definitions

THE System SHALL define a ClarifyOption type with a label field constrained to "A" or "B", a rewritten-text field of type string, and a rationale field of type string.

THE System SHALL define a ClarifyResponse type with spec-identifier, line-number, check-identifier, effective-line, and options fields WHERE options is a two-element tuple of ClarifyOption.

### NFR-3: Accessibility

WHEN the options panel opens THE System SHALL move keyboard focus to the panel container.

WHEN the options panel closes THE System SHALL return keyboard focus to the "Clarify" button.

THE System SHALL make the options panel navigable by Tab key between "Select A", "Select B", and "Cancel" buttons.

THE System SHALL assign accessible labels to each button that distinguish the two options for assistive technology.

### NFR-4: Loading State Isolation

THE System SHALL track the clarify loading state in a dedicated flag distinct from the existing rewrite loading state using a discriminator composed of line number and check identifier.

THE System SHALL combine both loading states into a shared busy guard that disables all action buttons WHEN either state is active.

### NFR-5: No New Dependencies

THE System SHALL introduce no new packages for the clarification feature.

### NFR-6: Consistent Visual Style

THE System SHALL reuse existing button, badge, and code-block styles for the options panel.

THE System SHALL introduce new class names for panel layout without duplicating existing style rules.

---

## Unwanted Behavior

IF the clarification queue receives a conflict response indicating that the line has changed since option generation THEN THE System SHALL display the message "Line has changed — please re-clarify." and collapse the options panel without modifying the analysis state.

IF the clarification endpoint returns an unexpected response shape missing the options field THEN THE System SHALL display an inline error "Unable to load options" and restore the finding card to its default state.

---

## Acceptance Criteria

WHEN THE System displays a finding THEN THE System SHALL show a "Clarify" button on the finding card.

WHEN the user clicks "Clarify" THEN THE System SHALL call the clarification endpoint and display two options labelled "A" and "B" inline.

WHEN THE System displays options THEN THE System SHALL show no additional options or free-text input.

WHEN the user selects an option THEN THE System SHALL call the selection endpoint and not change the UI until the response arrives.

WHEN the selection response succeeds THEN THE System SHALL update the entire analysis state in a single state assignment.

WHEN the selection response returns a conflict error THEN THE System SHALL display an inline stale-data error and collapse the panel.

WHEN the clarification request fails THEN THE System SHALL display an inline error and restore the finding card to its default state.

WHEN any clarify or selection request is in-flight THEN THE System SHALL disable all action buttons across all findings.

WHEN the user clicks "Cancel" in the options panel THEN THE System SHALL close the panel without sending any request.

WHEN the full UI refreshes after a successful selection THEN THE System SHALL reflect the updated score, verdict, tier, findings, rewrites, missions, and report in one render cycle.

---

## Out of Scope

- Server-side implementation (covered by the clarification-loop-backend spec).
- More than two options per finding.
- Speculative score previews or animations predicting the new score.
- Persisting panel open or closed state across re-analyses.
- Undo after persisting a clarification (use existing remove-rewrite flow).
- AI-generated or user-editable rewrite text.
