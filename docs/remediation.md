# Dependency security remediation

Recipes that compile an upstream application can carry security pins for its
dependencies. The pins live in the recipe, are proposed by a bot pull request and are
applied by every build with [omnibump](https://github.com/chainguard-dev/omnibump), the
same approach Wolfi uses. Builds never query vulnerability databases or pick fixes on
their own: a package build is a function of the committed recipe.

Remediation is enabled for `prometheus-minimal` (Go), `garage` (Cargo) and `seerr`
(pnpm).

## Recipe integration

Place one bump step after source preparation and before dependency installation,
compilation or copying a second dependency tree:

```yaml
- uses: eudaldgr-labs/bump
  with:
    language: go # go, rust or js
    deps: "" # written by `just remediate <recipe>`
    # policy: minor
    # modroot: subdir
```

A recipe opts in by having this step. With an empty `deps` it does nothing. With pins, it
writes them to an omnibump deps file and runs omnibump once: `--tidy` for Go,
`--fail-on-unapplied-pins` for Cargo, pnpm overrides followed by a lockfile-only install
for js. omnibump treats each pin as a floor, so a pin that a newer upstream release
already satisfies is skipped.

`deps` holds one `name@version` per line, split on the last `@`. For js the name carries a
version selector (`lodash@4.17.20@4.17.21`) so other installed versions of the same
package keep their own resolution.

For Seerr the step comes before the manifest and lockfile are copied into `package/`, so
the production tree and the build tree consume the same overrides. pnpm is pinned to
10.x: upstream requires pnpm 10.

## Planning

`just remediate <recipe> [arch]` builds a planner recipe in Melange: the recipe's own
steps up to the bump step, which is replaced by `eudaldgr-labs/remediate-plan`. The
planner therefore sees the pristine upstream manifests after the same source
preparation as the real build, and never inherits the pins it is about to recompute.

1. OSV-Scanner scans the explicit lockfiles with all packages and vulnerabilities, call
   analysis disabled and an empty config, so upstream ignore lists cannot hide findings.
   Go workspaces include each member module; dev dependencies are included.
2. For each vulnerable version, the planner considers the fixed releases allowed by the
   policy and queries OSV for each candidate, choosing the lowest one with no known
   non-withdrawn vulnerability.
3. Each candidate is applied with omnibump together with the already accepted pins,
   from the pristine manifests, exactly as the build will apply the final list. The
   result is rescanned. Downgrades, changes outside policy, newly vulnerable versions,
   or a fix that did not land reject the candidate. omnibump errors (for example a
   required Go co-update or an incompatible Cargo constraint) also leave it pending,
   with omnibump's message as the reason.
4. The final list is applied once more and rescanned; any violation aborts the plan.
   Scanner errors and OSV failures abort too: they never produce an empty list.
5. `write` rewrites only the `deps` input of the recipe and leaves the rest of the file
   byte for byte. When the list changed and the current `version`/`epoch` already exists
   on the base branch (`origin/main` by default, `REMEDIATION_BASE` to override), the
   epoch is incremented. It also writes `out/remediation/<recipe>/pr.md`, a summary of
   applied and pending findings.

The default policy is `patch`: `1.2.3` may move to a stable `1.2.x`. `policy: minor`
permits stable updates within a major; `0.x` dependencies stay on their minor, except
`golang.org/x/*`, which stay on 0.x by convention and ship fixes as minors.
Prereleases, Go pseudo-versions, majors and source backports are never proposed. A
security fix is not necessarily a SemVer patch, so some fixable findings stay pending
until the policy is widened deliberately or upstream updates.

## Automation

- `.github/workflows/remediate.yaml` runs daily and on demand. Each opted-in recipe is
  planned in a job without write credentials (`eudaldgr-labs/.github` `pr-regenerate`);
  a separate job commits the recipe as the GitHub App bot to `remediation/<recipe>` and
  opens or updates a pull request with the summary (`pr-regenerate/push`). The pull request runs
  the normal build, package tests and scans before it can be merged.
- `.github/workflows/renovate-regenerate.yaml` re-plans recipes touched by a Renovate
  pull request, so a new upstream release drops obsolete pins and gains new ones in the
  same pull request. Renovate already reset the epoch there, so no extra bump is made.

Both need the organisation GitHub App secrets `BOT_CLIENT_ID` and `BOT_APP_PRIVATE_KEY`,
and the App's bot email in `gitIgnoredAuthors` of the org preset in `eudaldgr-labs/.github`, so Renovate keeps
rebasing branches that carry the regenerated commit.

## Limits

The scan covers the source dependency inventory, not runtime reachability. Final image
scanners (Grype and Trivy, advisory) cannot necessarily see dependencies bundled into
JavaScript or native artifacts. Builds and package tests remain necessary; a successful
compile is not a complete compatibility test.

In a Go workspace omnibump applies a pin to every member module, and the policy is
checked per dependency across the whole inventory: a pin accepted for the main module
(`1.20.0 → 1.20.2`) can also move an example or tooling module that was on `1.19.x`.
Those modules are not compiled into the package, but the move is visible in the build log.

Adapters exist for Go modules and workspaces, Cargo lockfiles and pnpm. Other package
managers need an explicit adapter. Recipes with local APK build prerequisites would need
planning scheduled after those prerequisites; the current three do not.

Wolfi runtime libraries are patched separately, by the daily Apko rebuild.

## Local use

```sh
mise install
just setup
just remediate prometheus-minimal aarch64
git diff prometheus-minimal/melange.yaml
TAG=remediation-check just build prometheus-minimal aarch64
jq '{deps, blocked}' out/remediation/prometheus-minimal/plan.json
```
