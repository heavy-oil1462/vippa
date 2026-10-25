# Supervisor notes

How the podium team works on this repository. Written and kept by the
supervisor.

## Team

Up to two workers (the project limit). Much of the hardware work needs
the owner's hands (measuring parts, printing, testing on scrap), so
there is often only one issue a worker can do alone. Start a worker when
an issue is ready, remove it when it has had nothing to do for a day.

## Cutting issues

- One model, one panel or one catalog family per issue, small enough to
  review from a handful of renders.
- Acceptance criteria name what `regen_all.py --check` must newly check
  (a panel rule, an assert, an envelope) and which renders the worker
  attaches to the pull request.
- An issue that rests on an open question in docs/CONCEPT.md waits
  until the owner settles it; ask with needs:owner.
- Work that needs real measurements stays with the owner. A worker may
  add a part with `measured: false` placeholder values and a `source`.

## Review

- Run verify and look at the renders yourself (openscad-review); do not
  accept a CAD change from the diff alone.
- Every new layout rule in panels.py comes with a panel or test case
  that would fail it.
- A CAD or panel change that alters the README scenes must carry
  regenerated `media/*.png`.
- Reject any `measured: true` the owner did not provide, any value
  shadowing design_params.scad, and any panel numbers in a .scad.

## Lessons

- 2026-10-25: the bot account had only a pending invitation and could
  not push; accept a repository invitation with
  `gh api user/repository_invitations` when pushes fail with 403.
- 2026-10-25: the token lacks read:org, so `gh pr edit` and `gh pr view`
  without `--json` fail on GraphQL. Move PR labels with the REST API:
  `gh api -X DELETE repos/OWNER/REPO/issues/N/labels/status:review` and
  `gh api repos/OWNER/REPO/issues/N/labels -f 'labels[]=status:changes'`.
