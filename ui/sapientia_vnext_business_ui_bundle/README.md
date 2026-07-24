# Sapientia vNext — Business-First UI

This bundle replaces the stage-oriented UX with a business-domain experience.

## What changes

- Enterprise Overview becomes the landing experience.
- Navigation is organised around actual business domains returned by `/domains`.
- Changing the selected domain now preserves the current tool context and updates the route correctly.
- The old **Understand** destination is replaced by a living business-domain page.
- The old **Assess** destination is removed from primary navigation; assessment intelligence appears directly inside each domain.
- Each domain presents an executive summary, current signal, findings, risks, opportunities, recommendations, evidence and an enterprise timeline.
- AI becomes contextual through an Ask Sapientia bar in each domain.
- Explorer is positioned as search-first and graph-second.
- Technical capabilities remain accessible under Sources, Explore and Administration.

## Install

```bash
unzip sapientia_vnext_business_ui_bundle.zip
cd sapientia_vnext_business_ui_bundle
chmod +x install.sh
./install.sh
```

Default project path:

```text
/Users/emilianobarco/Desktop/Projects/Sapientia
```

Alternative path:

```bash
./install.sh /path/to/Sapientia
```

Then:

```bash
cd /Users/emilianobarco/Desktop/Projects/Sapientia/ui
npm run dev
```

## Recommended review

1. Open `/dashboard` and confirm all domains appear.
2. Open Finance, then choose another domain from the sidebar.
3. Confirm the domain name, content, links and Ask Sapientia context all change.
4. Review findings, risks, opportunities and recommendations for relevance.
5. Open Explore and confirm the selected domain remains consistent.
6. Open Ask Sapientia and test a question in two different domains.
7. Review Sources to confirm the existing ingestion workflow remains available.

## Rollback

The installer creates a timestamped backup under:

```text
Sapientia/.sapientia_backups/
```

Run the `restore.sh` stored in that backup folder.

## Backend compatibility

No backend APIs or database objects are changed. The bundle uses the existing endpoints:

- `/domains`
- `/domains/{domain}/workspace`
- `/intelligence/assessments/domain/{domain}`
- `/intelligence/assessments/{assessment_id}/objects`
- `/ai-advisor/ask`
