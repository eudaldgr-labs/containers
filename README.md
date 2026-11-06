<p align="center">
  <img src=".assets/logo.png" width="128" height="128" alt="VegOps Containers Logo">
</p>

<h1 align="center">VegOps Containers</h1>

<p align="center">
  <a href="https://github.com/eudaldgr-labs/containers/actions/workflows/build.yaml"><img src="https://github.com/eudaldgr-labs/containers/actions/workflows/build.yaml/badge.svg" alt="Build Status"></a>
  <a href="https://vegops.sh/containers/"><img src="https://img.shields.io/badge/CVE-Dashboard-blue" alt="CVE Dashboard"></a>
  <a href="https://github.com/eudaldgr-labs/containers/blob/main/LICENSE"><img src="https://img.shields.io/github/license/vegops/containers" alt="License"></a>
</p>

<p align="center">
  Hardened, distroless container images built with <a href="https://github.com/chainguard-dev/melange">melange</a> + <a href="https://github.com/chainguard-dev/apko">apko</a> on <a href="https://github.com/wolfi-dev">Wolfi</a>.
  <br>
  <a href="https://vegops.sh/containers/"><b>vegops.sh/containers</b></a> — live vulnerability reports, updated daily.
</p>

---

### Every image is:

- **Distroless** — no shell, no package manager at runtime.
- **Minimal CVEs** — rebuilt daily with the latest Wolfi security patches.
- **Signed** — with [cosign](https://github.com/sigstore/cosign) keyless signing.
- **SBOM included** — SPDX generated automatically by apko.
- **Multi-arch** — supporting both `x86_64` and `aarch64`.

### Available Images

| Image                               | Description                  | Build Strategy                     |
| :---------------------------------- | :--------------------------- | :--------------------------------- |
| `ghcr.io/eudaldgr-labs/adguard`            | AdGuard Home DNS server      | Compiled from source (Go + npm)    |
| `ghcr.io/eudaldgr-labs/bentopdf`           | Browser-based PDF tools      | Source-built frontend + nginx     |
| `ghcr.io/eudaldgr-labs/bitcoin-core`       | Bitcoin Core daemon          | Compiled from source (CMake)      |
| `ghcr.io/eudaldgr-labs/bitcoin-knots`      | Bitcoin Knots daemon         | Compiled from source (CMake)       |
| `ghcr.io/eudaldgr-labs/chown`              | chown CLI                    | Custom build with musl (.NET)      |
| `ghcr.io/eudaldgr-labs/configarr`          | Arr configuration manager    | Source-built Node bundle + .NET   |
| `ghcr.io/eudaldgr-labs/dotnet`             | .NET Runtime                 | Wolfi packages (apko-only)         |
| `ghcr.io/eudaldgr-labs/electrs`            | Electrum Rust Server         | Compiled from source (Rust)        |
| `ghcr.io/eudaldgr-labs/fulcrum`            | Fulcrum SPV server           | Compiled from source (qmake)       |
| `ghcr.io/eudaldgr-labs/garage`             | S3 object storage            | Compiled from source (Rust)       |
| `ghcr.io/eudaldgr-labs/garage-webui`       | Garage web interface         | Compiled from source (Go + pnpm)  |
| `ghcr.io/eudaldgr-labs/ghost`              | Ghost publishing platform    | Official npm package + yarn        |
| `ghcr.io/eudaldgr-labs/go`                 | Go programming language      | Wolfi package (apko-only)          |
| `ghcr.io/eudaldgr-labs/i2pd`               | I2P daemon                   | Compiled from source (make)        |
| `ghcr.io/eudaldgr-labs/libtorrent`         | libtorrent-rasterbar library | Compiled from source (CMake)       |
| `ghcr.io/eudaldgr-labs/libtorrent-v1`      | libtorrent-rasterbar 1.x     | Compiled from source (CMake)       |
| `ghcr.io/eudaldgr-labs/lidarr`             | Lidarr music manager         | Compiled from source (.NET + yarn) |
| `ghcr.io/eudaldgr-labs/lnd`                | Lightning Network Daemon     | Compiled from source (Go)          |
| `ghcr.io/eudaldgr-labs/miniupnpc`          | MiniUPnP CLI/Library         | Compiled from source (make)        |
| `ghcr.io/eudaldgr-labs/openssl`            | OpenSSL CLI                  | Wolfi package (apko-only)          |
| `ghcr.io/eudaldgr-labs/openssl-static`     | OpenSSL static library       | Repacked from Wolfi openssl-dev    |
| `ghcr.io/eudaldgr-labs/plex`               | Plex Media Server            | Official Debian package            |
| `ghcr.io/eudaldgr-labs/postgres`           | PostgreSQL database          | Wolfi package (apko-only)          |
| `ghcr.io/eudaldgr-labs/prometheus-minimal` | Prometheus monitoring        | Compiled from source (Go)          |
| `ghcr.io/eudaldgr-labs/prowlarr`           | Prowlarr indexer manager     | Compiled from source (.NET + yarn) |
| `ghcr.io/eudaldgr-labs/python`             | Python 3.11–3.14 runtimes    | Wolfi packages (apko-only)         |
| `ghcr.io/eudaldgr-labs/qbittorrent`        | qBittorrent nox client       | Source-built + VueTorrent          |
| `ghcr.io/eudaldgr-labs/qbittorrent-libtorrentv1` | qBittorrent with libtorrent 1.x | Source-built + VueTorrent     |
| `ghcr.io/eudaldgr-labs/qt-minimal`         | Minimal Qt 6                 | Compiled from source (CMake)       |
| `ghcr.io/eudaldgr-labs/radarr`             | Radarr movie manager         | Compiled from source (.NET + yarn) |
| `ghcr.io/eudaldgr-labs/rocksdb`            | RocksDB static library       | Compiled from source (make)        |
| `ghcr.io/eudaldgr-labs/seerr`              | Seerr request manager        | Compiled from source (Node + pnpm) |
| `ghcr.io/eudaldgr-labs/sonarr`             | Sonarr TV manager            | Compiled from source (.NET + yarn) |
| `ghcr.io/eudaldgr-labs/sqlite`             | SQLite CLI                   | Wolfi package (apko-only)          |
| `ghcr.io/eudaldgr-labs/tautulli`           | Tautulli analytics for Plex  | Compiled from source (Python)      |
| `ghcr.io/eudaldgr-labs/tor`                | Tor anonymity network        | Compiled from source (autoconf)    |
| `ghcr.io/eudaldgr-labs/valkey`             | In-memory data store         | Compiled from source (make)       |
| `ghcr.io/eudaldgr-labs/vaultwarden`        | Vaultwarden password manager | Compiled from source (Rust)        |

### Verify Image Signatures

All images are signed with [cosign](https://github.com/sigstore/cosign) keyless signing via Sigstore. Verify any image with:

```bash
cosign verify \
  --certificate-identity-regexp="https://github.com/vegops/containers" \
  --certificate-oidc-issuer="https://token.actions.githubusercontent.com" \
  ghcr.io/vegops/tor:latest
```

### Build Locally

```bash
# Example: build tor image
apko build tor/apko.yaml ghcr.io/vegops/tor:test output.tar --arch x86_64
```

### Acknowledgements

Inspired by projects like [linuxserver](https://github.com/linuxserver), [rtvkiz/minimal](https://github.com/rtvkiz/minimal), [home-operations](https://github.com/home-operations), and [11notes](https://github.com/11notes).  
Their work in containerization, homelabs, and simplicity has strongly influenced this repository, which follows a similar philosophy focused on hardened, reproducible OCI images.

---

<p align="center">
  Released under the <a href="LICENSE">MIT License</a>.
</p>
