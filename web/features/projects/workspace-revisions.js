// Single owner of workspace/edit revision counters and stale-response tokens.
// The composition root still owns project data and UI invalidation effects.
// No global singleton: separate instances cannot invalidate each other.
export function createWorkspaceRevisions() {
  let workspace = 0;
  let edit = 0;
  let validationGeneration = 0;

  const versions = () => ({workspaceRevision: workspace, editRevision: edit});
  const matches = context => context.workspaceRevision === workspace &&
    context.editRevision === edit;
  const capture = (project, filename) => ({
    ...versions(), snapshot: JSON.stringify(project), filename,
  });
  const isCurrent = (context, project, filename) =>
    matches(context) && filename === context.filename &&
    JSON.stringify(project) === context.snapshot;

  return Object.freeze({
    get workspace() { return workspace; },
    get edit() { return edit; },
    versions,
    matches,
    capture,
    isCurrent,
    sessionContext(project) {
      return {...versions(), projectSnapshot: JSON.stringify(project)};
    },
    markEdit() { edit += 1; },
    replace() { workspace += 1; },
    beginValidation(project, filename) {
      return {...capture(project, filename), project,
        generation: ++validationGeneration};
    },
    validationCurrent(context, project, filename) {
      return validationGeneration === context.generation &&
        project === context.project && isCurrent(context, project, filename);
    },
  });
}
