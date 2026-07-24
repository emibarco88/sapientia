# 5. Frontend Architecture

## 5.1 Route strategy

The existing domain-first route remains the primary experience:

- `/domains/[domain]`

New supporting routes:

- `/domains/[domain]/story`
- `/domains/[domain]/objects/[objectId]`

Existing workspace routes remain available for compatibility and technical exploration.

## 5.2 Page composition

### Domain page

1. Domain header and current assessment metadata.
2. Contextual Ask bar.
3. “Tell me the story” primary action.
4. Executive Summary.
5. Business Health.
6. What Changed and Why.
7. Findings, Risks and Opportunities.
8. Recommendations.
9. Evidence coverage.
10. Timeline preview.

### Story page or panel

A focused consultant-style briefing with progressive sections and inline evidence references.

### Business Object Profile

1. Identity and definition.
2. Why it matters.
3. Current status.
4. Related intelligence.
5. Recent changes.
6. Evidence.
7. Relationships.
8. Suggested AI questions.

## 5.3 Proposed component structure

```text
ui/components/intelligence-experience/
  ExecutiveSummaryCard.tsx
  BusinessHealthCard.tsx
  HealthDriverList.tsx
  BusinessStoryCard.tsx
  ChangeStoryCard.tsx
  IntelligenceObjectCard.tsx
  IntelligenceObjectList.tsx
  RecommendationCard.tsx
  EvidenceCard.tsx
  EvidenceDrawer.tsx
  EvidenceCoverage.tsx
  TellTheStoryButton.tsx
  TellTheStoryPanel.tsx
  IntelligenceTimeline.tsx
  BusinessObjectProfile.tsx
  ContextualQuestions.tsx
  NarrativeSkeleton.tsx
  NarrativeEmptyState.tsx
  NarrativeErrorState.tsx

ui/features/intelligence-experience/
  api.ts
  types.ts
  hooks/
    useDomainNarrative.ts
    useBusinessObjectProfile.ts
```

## 5.4 State rules

- Domain must come from the route, never a hard-coded Finance constant.
- Switching domain cancels stale requests and clears prior-domain state.
- Assessment ID may be selected explicitly; otherwise latest is used.
- Evidence drawers load lazily where possible.
- AI generation is an explicit mutation; reading an existing narrative is a GET.

## 5.5 Design principles

- Executive language first.
- Progressive disclosure.
- Evidence visible without overwhelming the primary narrative.
- Confidence represented with words and details, not decorative percentages alone.
- Empty states explain what is missing and how Sapientia can obtain it.
- Graph interactions navigate to a Business Object Profile rather than displaying an unexplained node panel.

## 5.6 Accessibility

- All status states must include text, not colour alone.
- Narrative sections use semantic headings.
- Drawers and dialogs must trap focus and support Escape.
- Evidence links and relationship actions must be keyboard accessible.
- Loading states announce progress.
