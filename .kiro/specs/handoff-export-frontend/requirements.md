# Requirements: Export Handoff Pack — Frontend

## Overview

An "Export Handoff Pack" button that calls the handoff-export endpoint, triggers
a browser download of the returned Markdown file, and displays loading and error
states. No new package dependencies. No modifications to any clarify-related UI
code.

---

## Functional Requirements

### FR-1: Export Button Placement and Visibility

WHEN the analysis result exists THE System SHALL render an "Export Handoff Pack" button visible to the user.

WHEN no analysis result exists THE System SHALL hide the export button.

WHEN the System renders the export button THE System SHALL place it alongside other post-analysis action buttons so it is discoverable without scrolling past findings.

### FR-2: Trigger Export on Click

WHEN the user clicks the "Export Handoff Pack" button THE System SHALL send a POST request to the handoff-export endpoint using the spec identifier from the current analysis response state.

WHEN the System sends the export request THE System SHALL set the request content-type header to "application json".

WHEN the System sends the export request THE System SHALL send an empty JSON object as the request body conforming to the handoff export request contract.

### FR-3: Browser Download on Success

WHEN the server returns a successful response containing a Markdown document field THE System SHALL trigger a browser file download.

WHEN the System triggers the download THE System SHALL use the filename field from the response as the downloaded file name, or derive a default name from the spec filename with a "-handoff.md" suffix.

WHEN the System triggers the download THE System SHALL create the file as a text-markdown Blob from the Markdown document string and use a programmatic anchor-click pattern to initiate download.

WHEN the download triggers THE System SHALL keep the user on the current page without navigation.

### FR-4: Loading State

WHEN the export request is in flight THE System SHALL display a loading indicator on or near the export button.

WHEN the export request is in flight THE System SHALL disable the export button to prevent duplicate requests.

WHEN the export request completes with either success or error THE System SHALL restore the button to its default state with interaction re-enabled.

### FR-5: Disabled While Busy

WHEN any rewrite or clarify operation is in progress THE System SHALL disable the export button.

WHEN the export request is in flight THE System SHALL disable all rewrite and clarify action buttons by contributing to the shared busy guard.

WHEN the export request is in flight THE System SHALL disable the reset-rewrites button.

### FR-6: Error State

WHEN the server returns a non-success status THE System SHALL display an inline error message to the user.

WHEN the server returns a 404 status THE System SHALL display an error message stating "spec not found".

WHEN a network error occurs THE System SHALL display an error message stating "export failed due to network error".

WHEN the System displays an error THE System SHALL clear it on the next successful export attempt or on the start of a new analysis.

### FR-7: Happy-Path Export Flow

WHEN the user clicks "Export Handoff Pack" with a valid analysis result and the server returns status 200 with a populated Markdown document THE System SHALL download a file to the user device with the correct filename and return the button to its default state within one second of response receipt.

### FR-8: TypeScript Types

WHEN the System defines the response shape THE System SHALL add a HandoffExportResponse interface to the types module containing at minimum: spec_id (number), filename (string), score (number), verdict (string), exported_at (string), and markdown_document (string).

WHEN the System defines the request shape THE System SHALL not require a dedicated request type since the body is an empty object.

---

## Non-Functional Requirements

### NFR-1: No New Dependencies

THE System SHALL use no packages beyond the existing project dependencies for this feature.

THE System SHALL use browser-native capabilities for the download mechanism: fetch, Blob, Object URL creation, Object URL revocation, and DOM anchor element with no additional libraries.

### NFR-2: No Clarify Code Modifications

THE System SHALL not modify the Clarify button rendering, chooser panel markup, clarify callback, select-option callback, clarify panel state interface, or the clarify panel state logic.

THE System SHALL not modify the existing clarify-options or select-clarify-option functions in the service module.

THE System SHALL not modify the existing ClarifyOptionsResponse or ClarifyOption interfaces in the types module.

### NFR-3: Accessibility

WHEN the System disables the export button THE System SHALL set the native disabled attribute so assistive technologies communicate the state.

WHEN the export button enters loading state THE System SHALL set aria-busy to "true" to communicate the pending state to assistive technologies.

WHEN the System displays an export error THE System SHALL use a live region with aria-live set to "polite" so screen readers announce the error.

### NFR-4: Consistent Code Style

THE System SHALL follow the existing component code style: functional component, hooks, inline state management, and same error handling patterns.

THE System SHALL follow the existing service-module pattern: async function, fetch, throw on non-OK, typed return.

THE System SHALL follow the existing types-module pattern: exported interfaces with snake_case field names matching the server JSON contract.

### NFR-5: Object URL Cleanup

WHEN the System creates an Object URL for the download THE System SHALL revoke it after the download triggers to prevent memory leaks.

---

## Unwanted Behavior

IF the user clicks the export button multiple times in less than one second THEN THE System SHALL not send multiple concurrent export requests because the disabled state prevents this.

IF the server returns a 200 response with an empty Markdown document field THEN THE System SHALL still trigger the download with an empty file rather than showing an error.

IF the user has pending rewrite or clarify state THEN THE System SHALL not block the export because the export reads server-side state that already reflects applied rewrites.

IF the download mechanism fails in the browser THEN THE System SHALL catch the error and display it inline rather than throwing an unhandled exception.

---

## Acceptance Criteria

WHEN the user clicks "Export Handoff Pack" with a valid analysis result THE System SHALL send a POST request to the handoff-export endpoint and trigger a Markdown file download on success.

WHEN the export request is in flight THE System SHALL display a loading indicator and disable the export button.

WHEN any rewrite or clarify operation is in progress THE System SHALL disable the export button.

WHEN the export is in flight THE System SHALL disable rewrite and clarify buttons.

WHEN the server returns an error THE System SHALL display an inline error message and restore the button to its default state.

WHEN no analysis result exists THE System SHALL hide the export button.

WHEN the download completes THE System SHALL revoke the Object URL and keep the user on the current page.

WHEN the System exposes the types module THE System SHALL contain a HandoffExportResponse interface with fields matching the server contract.

WHEN the System preserves clarify-related functions, interfaces, button markup, and chooser panel markup THE System SHALL keep them unmodified.

---

## Interface Notes

This section documents technical routing and implementation details referenced
by the requirements above. These notes are not requirements.

- Endpoint: POST {API_BASE}/api/specs/{spec_id}/handoff-export
- Request body: empty JSON object {}
- Response model: HandoffExportResponse with fields: spec_id, filename, score,
  verdict, exported_at, markdown_document
- Response content-type header: application/json
- Status codes: 200 on success, 404 for missing spec
- Download mechanism: Blob with type "text/markdown", Object URL via
  URL.createObjectURL, programmatic anchor click, followed by URL.revokeObjectURL
- API function: exportHandoffPack(specId: number) in frontend/src/api.ts
- Types: HandoffExportResponse interface in frontend/src/types.ts
- Component: functional component in App.tsx using React hooks
- Busy guard: export contributes to shared isBusy state

---

## Out of Scope

- Server-side implementation of the handoff export endpoint (covered by the
  backend spec).
- Custom export templates or user-configurable filenames.
- Progress bar or percentage-based progress (a simple loading state is
  sufficient).
- Notification toasts or modals (inline messaging is sufficient).
- Any AI or LLM calls from the client.
- Authentication or authorization on the export request.
- Modification of any clarify-related code.
