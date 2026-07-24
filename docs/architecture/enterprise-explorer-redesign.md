# Enterprise Explorer Redesign 2.3.1

## Purpose

Restore the Enterprise Explorer as an interactive visual graph while retaining the graph traversal capabilities introduced in Bundle 2.3.

## Behaviour

The default canvas loads the full enterprise graph through the existing Explorer service contract. Selecting a node opens a details panel. The user can then focus the canvas on the selected node's one-, two-, or three-hop neighbourhood through the versioned Enterprise Graph traversal API.

## Architecture

```text
Explorer UI
  -> /explorer/{project}/{domain}/graph
  -> EnterpriseExplorerService
  -> EnterpriseGraphService

Selected node / focused navigation
  -> /enterprise-graph/v1/{project}/{domain}/nodes/{id}/traversal
  -> EnterpriseGraphTraversalService
  -> EnterpriseGraphService
```

## Design decisions

- The visual node-and-edge graph remains the primary Explorer experience.
- Traversal augments the graph rather than replacing it with a list.
- The full graph can always be restored from the toolbar.
- Existing Explorer filters continue to operate on either the full graph or the focused neighbourhood.
- No database migration is required.
