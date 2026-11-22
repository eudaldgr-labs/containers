<p align="center">
  <img src=".assets/logo.png" width="128" height="128" alt="eudaldgr-labs containers logo">
</p>

<h1 align="center">eudaldgr-labs containers</h1>

<p align="center">
  <a href="https://github.com/eudaldgr-labs/containers/actions/workflows/build.yaml"><img src="https://github.com/eudaldgr-labs/containers/actions/workflows/build.yaml/badge.svg" alt="Build Status"></a>
  <a href="https://containers.eudald.gr/"><img src="https://img.shields.io/badge/CVE-Dashboard-blue" alt="CVE Dashboard"></a>
  <a href="https://github.com/eudaldgr-labs/containers/blob/main/LICENSE"><img src="https://img.shields.io/github/license/eudaldgr-labs/containers" alt="License"></a>
</p>

<p align="center">
  Hardened, distroless container images built with <a href="https://github.com/chainguard-dev/melange">melange</a> + <a href="https://github.com/chainguard-dev/apko">apko</a> on <a href="https://github.com/wolfi-dev">Wolfi</a>.
  <br>
  <a href="https://containers.eudald.gr/"><b>containers.eudald.gr</b></a> — live vulnerability reports, updated daily.
</p>

---

### Every image is:

- **Distroless** — no shell, no package manager at runtime.
- **Minimal CVEs** — rebuilt daily with the latest Wolfi security patches.
- **Signed** — with [cosign](https://github.com/sigstore/cosign) keyless signing.
- **SBOM included** — SPDX generated automatically by apko.
- **Multi-arch** — supporting both `x86_64` and `aarch64`.

### Available Images

| Image                                            | Description                     | Build Strategy                     |
| :----------------------------------------------- | :------------------------------ | :--------------------------------- |
| `ghcr.io/eudaldgr-labs/adguard`                  | AdGuard Home DNS server         | Compiled from source (Go + npm)    |
| `ghcr.io/eudaldgr-labs/bentopdf`                 | Browser-based PDF tools         | Source-built frontend + nginx      |
| `ghcr.io/eudaldgr-labs/bitcoin-core`             | Bitcoin Core daemon             | Compiled from source (CMake)       |
| `ghcr.io/eudaldgr-labs/bitcoin-knots`            | Bitcoin Knots daemon            | Compiled from source (CMake)       |
| `ghcr.io/eudaldgr-labs/chown`                    | chown CLI                       | Custom build with musl (.NET)      |
| `ghcr.io/eudaldgr-labs/configarr`                | Arr configuration manager       | Source-built Node bundle + .NET    |
| `ghcr.io/eudaldgr-labs/dotnet`                   | .NET Runtime                    | Wolfi packages (apko-only)         |
| `ghcr.io/eudaldgr-labs/electrs`                  | Electrum Rust Server            | Compiled from source (Rust)        |
| `ghcr.io/eudaldgr-labs/fulcrum`                  | Fulcrum SPV server              | Compiled from source (qmake)       |
| `ghcr.io/eudaldgr-labs/garage`                   | S3 object storage               | Compiled from source (Rust)        |
| `ghcr.io/eudaldgr-labs/garage-webui`             | Garage web interface            | Compiled from source (Go + pnpm)   |
| `ghcr.io/eudaldgr-labs/ghost`                    | Ghost publishing platform       | Official npm package + yarn        |
| `ghcr.io/eudaldgr-labs/go`                       | Go programming language         | Wolfi package (apko-only)          |
| `ghcr.io/eudaldgr-labs/i2pd`                     | I2P daemon                      | Compiled from source (make)        |
| `ghcr.io/eudaldgr-labs/libtorrent`               | libtorrent-rasterbar library    | Compiled from source (CMake)       |
| `ghcr.io/eudaldgr-labs/libtorrent-v1`            | libtorrent-rasterbar 1.x        | Compiled from source (CMake)       |
| `ghcr.io/eudaldgr-labs/lidarr`                   | Lidarr music manager            | Compiled from source (.NET + yarn) |
| `ghcr.io/eudaldgr-labs/lnd`                      | Lightning Network Daemon        | Compiled from source (Go)          |
| `ghcr.io/eudaldgr-labs/miniupnpc`                | MiniUPnP CLI/Library            | Compiled from source (make)        |
| `ghcr.io/eudaldgr-labs/openssl`                  | OpenSSL CLI                     | Wolfi package (apko-only)          |
| `ghcr.io/eudaldgr-labs/openssl-static`           | OpenSSL static library          | Repacked from Wolfi openssl-dev    |
| `ghcr.io/eudaldgr-labs/plex`                     | Plex Media Server               | Official Debian package            |
| `ghcr.io/eudaldgr-labs/postgres`                 | PostgreSQL database             | Wolfi package (apko-only)          |
| `ghcr.io/eudaldgr-labs/prometheus-minimal`       | Prometheus monitoring           | Compiled from source (Go)          |
| `ghcr.io/eudaldgr-labs/prowlarr`                 | Prowlarr indexer manager        | Compiled from source (.NET + yarn) |
| `ghcr.io/eudaldgr-labs/python`                   | Python 3.11–3.14 runtimes       | Wolfi packages (apko-only)         |
| `ghcr.io/eudaldgr-labs/qbittorrent`              | qBittorrent nox client          | Source-built + VueTorrent          |
| `ghcr.io/eudaldgr-labs/qbittorrent-libtorrentv1` | qBittorrent with libtorrent 1.x | Source-built + VueTorrent          |
| `ghcr.io/eudaldgr-labs/qt-minimal`               | Minimal Qt 6                    | Compiled from source (CMake)       |
| `ghcr.io/eudaldgr-labs/radarr`                   | Radarr movie manager            | Compiled from source (.NET + yarn) |
| `ghcr.io/eudaldgr-labs/rocksdb`                  | RocksDB static library          | Compiled from source (make)        |
| `ghcr.io/eudaldgr-labs/seerr`                    | Seerr request manager           | Compiled from source (Node + pnpm) |
| `ghcr.io/eudaldgr-labs/sonarr`                   | Sonarr TV manager               | Compiled from source (.NET + yarn) |
| `ghcr.io/eudaldgr-labs/sqlite`                   | SQLite CLI                      | Wolfi package (apko-only)          |
| `ghcr.io/eudaldgr-labs/tautulli`                 | Tautulli analytics for Plex     | Compiled from source (Python)      |
| `ghcr.io/eudaldgr-labs/tor`                      | Tor anonymity network           | Compiled from source (autoconf)    |
| `ghcr.io/eudaldgr-labs/valkey`                   | In-memory data store            | Compiled from source (make)        |
| `ghcr.io/eudaldgr-labs/vaultwarden`              | Vaultwarden password manager    | Compiled from source (Rust)        |

### Verify Image Signatures

All images are signed with [cosign](https://github.com/sigstore/cosign) keyless signing via Sigstore. Verify any image with:

```bash
cosign verify \
  --certificate-identity-regexp="https://github.com/eudaldgr-labs/containers" \
  --certificate-oidc-issuer="https://token.actions.githubusercontent.com" \
  ghcr.io/eudaldgr-labs/tor:latest
```

### Image Tags

Version tags such as `0.4.8-r0`, `0.4.8`, `0.4`, `0`, and `latest` are refreshed by the daily rebuild pipeline so they receive Wolfi security updates.

Each rebuild also publishes a tag with the first 12 characters of the multi-architecture image digest, such as `0.4.8-r0-f83c10a9421b`. These tags are intended for pinned deployments. If one already exists, the workflow verifies that it still points to the same digest instead of overwriting it.

### Python runtimes

The recipes cover **3.11, 3.12, 3.13, 3.14 and 3.15**. The Python 3.10 recipe has been retired. Only 3.15 publishes `latest`.

Each `apps/python-3.x` directory publishes to `ghcr.io/eudaldgr-labs/python:3.x`, with exact patch/revision aliases. Only 3.15 publishes `latest`; no competing `:3` alias is emitted. `publish.json`'s optional `streamTag` bounds the generated aliases to a minor release. These are runtime images without pip or a shell; install application dependencies during your application build.

```bash
just apko python-3.14 aarch64
docker run --rm ghcr.io/eudaldgr-labs/python-3.14:test --version
```

### Build isolation and reports

Package matrices keep running after sibling failures. Each dependent build checks the exact local APKs it needs, per architecture, before building; unrelated failures do not block later tiers or images. A missing dependency still fails its consumer, and the workflow summary remains red for real failures. Tier barriers remain, so later builds wait for earlier tiers to finish.

Local builds and CI use the digest-pinned Melange and Apko images in [`.mise/config.toml`](.mise/config.toml). No job downloads a Melange release binary. APK consumers receive exact local version constraints. Valkey's APK is named `eudaldgr-labs-valkey` to avoid Wolfi's versioned packages that provide the generic `valkey` name; its image remains `ghcr.io/eudaldgr-labs/valkey`. Each package artifact contains only that package's APKs; consumers download their dependency closure.

Pull requests build changed packages and their consumers, including prerequisites. Shared build configuration changes select the whole catalog. Scheduled, main-branch and manual runs rebuild everything.

Downloaded APK indexes are rebuilt with the run's signing key, including pull requests. Main-branch publishing is not cancelled by a newer push. Automatic deletion of untagged GHCR versions is disabled because multi-architecture manifests and signatures may still reference them.

Each image is built once per architecture on a native runner. The final image is scanned before a candidate digest is uploaded. Publication requires both architecture candidates from the same commit, run and attempt, builds the multi-architecture index from those digests, signs it, and then updates public aliases (`latest` last). Failed builds, scans or signatures cannot promote a candidate. Registry errors during alias promotion can still leave aliases partially updated; tags across a registry are not transactional.

Grype produces JSON and SARIF in one scan; Trivy supplies a second scan. Vulnerability findings remain advisory, as before. Scanner execution errors block publication. SARIF upload failures are advisory; the scan evidence artifacts must upload successfully. Reports record the source revision, run, archive SHA-256 and candidate digest when available.

The dashboard consumes reports and recipes from the same completed main-branch run, including failed runs. Missing architecture scans are marked **Incomplete scan**, never counted as clean. Tags in scan reports describe intended publication; follow the build link to check publishing results.

The `main` ruleset, managed by safe-settings in [eudaldgr-labs/.github](https://github.com/eudaldgr-labs/.github), requires the `Build Success` check and merges through a merge queue. The build also runs on `merge_group`, where it signs with an ephemeral key and never publishes. Pull requests are labelled `area/*` and `app/<name>` by the Labeler workflow.

Renovate extends the organisation policy in [eudaldgr-labs/.github](https://github.com/eudaldgr-labs/.github) (`renovate-config.json`: commit format, labels, groups, release ages, automerge). `.renovaterc.json5` holds everything specific to this repository: annotated `package.version` and bundled `*-version` variables in Melange recipes with epoch maintenance, exact Wolfi APK pins (`name=version-rN`) in recipes, pipelines and images through Renovate's `apk` datasource, upstream tag formats, compatibility constraints and groups. Package version updates reset the epoch; bundled-variable and build-environment APK updates increment it once per recipe. Each recipe gets its own branch, so recipes sharing an upstream (libtorrent and libtorrent-v1) never share a PR.

```bash
mise install
just setup
just report
```

### Build Locally

Activate [Mise](https://mise.jdx.dev/getting-started.html) in your shell, then:

```bash
mise install
just setup
just build tor aarch64
just build qbittorrent x86_64  # builds its local dependencies first
just apko python-3.14 aarch64
```

Mise pins Python, Just, Lefthook, yq and the linters. `just lint` checks Just/Mise formatting, Actions, shell syntax and whitespace. Docker is a prerequisite; Melange and Apko run in digest-pinned containers.

`just build <name> [arch]` builds and tests the required APKs with Melange, then assembles the image.

`just` lists commands. `just melange <name>` builds one APK from existing prerequisites; `just melangecheck <name>` tests it; `just test <name>` builds and tests its dependency closure. `just apko <name>` assembles from existing APKs. `just scan <name>` scans that archive with Grype and Trivy; scanner errors fail, CVE findings are advisory. `just push <name>` explicitly pushes an existing local tag. `TAG=dev OWNER=my-user just build tor x86_64` overrides the image destination. Default architecture is `aarch64`.

`mise install` installs local Lefthook hooks. The check-only pre-commit hooks come from the shared `lefthook.common.toml` in [eudaldgr-labs/.github](https://github.com/eudaldgr-labs/.github). Use `just fmt` to format the task and tool configuration. Docker builds remain explicit or run in CI.

Recipes live in `apps/<name>/`, automation code in `scripts/` and shared Melange pipelines in `.pipelines/`. `.github/` contains GitHub workflows and the reused Melange build action. The dependency graph currently has a base tier and two dependent tiers; discovery rejects deeper graphs until the workflow is extended.

Prometheus, Garage and Seerr carry security pins for their application dependencies in an `eudaldgr-labs/bump` step, applied with omnibump by every build. A daily workflow plans patch-level fixes in Melange and opens one bot pull request per recipe; Renovate pull requests get their pins re-planned for the new release. Builds never query vulnerability databases, so the same commit always builds the same dependencies. Run `just remediate <package> [arch]` to refresh pins locally. [How remediation works, its policy and limitations](docs/remediation.md).

Ghost reads `/ghost/etc/config.production.json` through its application config symlink. Mount configuration there and persistent content under `/ghost/var`; logs live under `/ghost/log`. The config directory does not need to be `HOME`, so the image does not override `HOME`.

PostgreSQL is a runtime image: provision its data directory before running it. Its default Unix socket directory is `/postgres/run`. Configarr schedules use five cron fields in UTC, with Sunday as `0` or `7` and the usual day-of-month/day-of-week matching rules.

### Acknowledgements

Inspired by projects like [linuxserver](https://github.com/linuxserver), [rtvkiz/minimal](https://github.com/rtvkiz/minimal), [home-operations](https://github.com/home-operations), and [11notes](https://github.com/11notes).  
Their work in containerization, homelabs, and simplicity has strongly influenced this repository, which follows a similar philosophy focused on hardened, reproducible OCI images.

---

<p align="center">
  Released under the <a href="LICENSE">Apache License 2.0</a>.
</p>
