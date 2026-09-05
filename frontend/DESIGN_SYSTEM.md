# Recon product UI kit

## Foundations

- **Font:** DM Sans for all product UI. Use DM Mono for figures, amounts, and IDs.
- **Canvas:** `--rf-canvas`; panels use `--rf-surface` and `--rf-border`.
- **Brand action:** `--rf-brand-600`. Do not introduce blue or indigo as a primary action colour.
- **Spacing:** use the 4px scale defined in `tokens.css`; panels use 24px padding on desktop and 18px on mobile.
- **Corners:** controls use `--rf-radius-sm`, cards use `--rf-radius-md`, and panels/modals use `--rf-radius-lg`.

## Application shell

All authenticated pages load `tokens.css` and `app-shell.css` after any page stylesheet. The shell is:

1. A 264px forest-green sidebar at desktop.
2. A context topbar, followed by a page title and actions.
3. A pale neutral canvas with white panels.
4. A horizontally scrolling navigation rail below 1024px; never a stacked desktop sidebar.

Sidebar groups should remain consistent: Dashboard, Jobs, Uploads, Column mapping, Reconcile, Results, then Team, Subscription, and Settings. Use Bootstrap icons on every navigation item and apply `.active` to the link, not the list container.

## Components

### Buttons

- `.primary-btn` / `.btn-primary`: one primary action per region.
- `.secondary-btn`: secondary or cancel action.
- Use 40px minimum height and 6px radius.

### Panels

Use `.panel`, `.results-panel`, `.upload-panel`, `.mapping-panel`, or `.recon-panel` only for page-specific semantics; their shared visual treatment comes from the UI kit. Headings use `.panel-header`, `.panel-title`, `.section-heading`, or `.panel-heading`.

### Metrics

Use `.stats`, `.cards`, `.upload-stats`, `.job-info-grid`, `.result-grid`, or `.summary-grid` as a grid only. Every child receives the shared metric-card appearance from `app-shell.css`.

### Data tables

Wrap every table in `.table-wrapper`; headers are uppercase labels and figures are right-aligned where practical. Provide loading, empty, filtered-empty, and error states.

### Status

Use `.status-completed`, `.status-pending`, `.status-processing`, `.status-failed`, and `.status-default`. Colours communicate status only; they are not decoration.

### Forms

Labels sit above fields. Inputs, selects, and buttons use the same 40px control height and branded focus ring. Explain errors underneath the field.

## Page checklist

- Load `tokens.css` and `app-shell.css`.
- Use the shared sidebar and topbar.
- Use a single page title and primary action area.
- Use shared panels, metric cards, form controls, status badges, and table treatments.
- Include a mobile state and an explicit empty state.
