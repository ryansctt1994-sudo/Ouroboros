# Lima Setup Guide — Running Eden ECS on macOS via a Linux VM

[Lima](https://lima-vm.io/) ("Linux on Mac") is a lightweight CLI tool that
runs Linux VMs on macOS using Apple's Virtualization framework (macOS 13+) or
QEMU (macOS 12 and earlier).  It gives you a full Ubuntu / Fedora / Arch
environment with transparent file-sharing and port-forwarding — ideal for
developing and testing `eden_ecs` when your primary machine is a Mac.

---

## Table of contents

1. [Prerequisites](#1-prerequisites)
2. [Install Lima](#2-install-lima)
3. [Create a VM](#3-create-a-vm)
4. [Enter the VM shell](#4-enter-the-vm-shell)
5. [Install Rust inside the VM](#5-install-rust-inside-the-vm)
6. [Mount the repository](#6-mount-the-repository)
7. [Build and test eden_ecs](#7-build-and-test-eden_ecs)
8. [Run examples](#8-run-examples)
9. [Port-forwarding for telemetry](#9-port-forwarding-for-telemetry)
10. [Useful Lima commands](#10-useful-lima-commands)
11. [Troubleshooting](#11-troubleshooting)

---

## 1. Prerequisites

| Requirement | Minimum version |
|-------------|----------------|
| macOS | 12 Monterey (QEMU) or 13 Ventura (Apple Virtualization) |
| Homebrew | any recent version |
| Disk space | ≥ 15 GB free (VM image + build artefacts) |
| RAM | ≥ 8 GB recommended |

---

## 2. Install Lima

```sh
brew install lima
```

Verify:

```sh
limactl --version
# e.g. limactl version 0.21.0
```

---

## 3. Create a VM

Lima ships with several built-in templates.  The `default` template runs
Ubuntu LTS and is a good starting point.

### Option A — default Ubuntu template (simplest)

```sh
limactl create --name eden-dev template://ubuntu
limactl start eden-dev
```

### Option B — customised template with more RAM/CPUs

Create a file `lima-eden.yaml` (you can place it anywhere outside the repo):

```yaml
# lima-eden.yaml
vmType: vz          # Apple Virtualization (macOS 13+); use "qemu" on macOS 12
os: Linux
arch: x86_64        # or "aarch64" on Apple Silicon
images:
  - location: "https://cloud-images.ubuntu.com/releases/24.04/release/ubuntu-24.04-server-cloudimg-amd64.img"
    arch: x86_64
cpus: 4
memory: "8GiB"
disk: "40GiB"

mounts:
  # Give the VM read-write access to your local checkout.
  # Adjust the path to match where you cloned the repository.
  - location: "~/Developer/Ouroboros"
    writable: true
    mountPoint: "/home/user.linux/Ouroboros"

# Forward the Tracy profiler port from VM → host.
portForwards:
  - guestPort: 8086
    hostPort: 8086

provision:
  - mode: system
    script: |
      #!/bin/bash
      set -e
      apt-get update -qq
      apt-get install -y build-essential pkg-config libssl-dev curl git
```

```sh
limactl create --name eden-dev lima-eden.yaml
limactl start eden-dev
```

> **Apple Silicon note:** Change `arch: x86_64` to `arch: aarch64` and
> replace the image URL with the ARM64 variant
> (`ubuntu-24.04-server-cloudimg-arm64.img`).

---

## 4. Enter the VM shell

```sh
limactl shell eden-dev
```

You are now in a Bash session inside the Ubuntu VM.  Your macOS username maps
to a Linux user of the same name (or `user.linux` depending on the Lima
version).

To run a single command without entering an interactive shell:

```sh
limactl shell eden-dev -- cargo test -p eden_ecs
```

---

## 5. Install Rust inside the VM

Inside the VM shell:

```sh
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
# Accept all defaults
source "$HOME/.cargo/env"
rustc --version   # verify
```

---

## 6. Mount the repository

If you used the custom `lima-eden.yaml` from [Section 3](#3-create-a-vm), the
repository is already available at `/home/user.linux/Ouroboros` inside the VM.

If you used the default template you can clone fresh:

```sh
# Inside the VM
git clone https://github.com/AIOSPANDORA/Ouroboros.git ~/Ouroboros
```

Or use `limactl copy` to push files into the VM:

```sh
# From macOS host
limactl copy -r ~/Developer/Ouroboros eden-dev:/home/user.linux/Ouroboros
```

---

## 7. Build and test eden_ecs

Inside the VM shell:

```sh
cd ~/Ouroboros

# Debug build
cargo build -p eden_ecs

# Release build
cargo build --release -p eden_ecs

# Full test suite
cargo test -p eden_ecs

# Tests with output
cargo test -p eden_ecs -- --nocapture
```

The first build downloads crates from crates.io; subsequent builds are
incremental.  On a VM with 4 CPUs, a clean release build takes ~90 seconds.

---

## 8. Run examples

```sh
# A→B→A engram persistence (flagship experiment)
cargo run -p eden_ecs --example sakib_aba --release

# A/B routing comparison
cargo run -p eden_ecs --example sakib_ab --release

# Save results to a file
cargo run -p eden_ecs --example sakib_aba --release 2>diag.log | tee results.csv

# Competing-paths experiment
cargo run -p eden_ecs --example competing_paths --release

# Ablation harness
cargo run -p eden_ecs --example ablation --release
```

CSV output can be copied back to macOS for plotting:

```sh
# From macOS host
limactl copy eden-dev:/home/user.linux/Ouroboros/results.csv ~/Desktop/
```

---

## 9. Port-forwarding for telemetry

The Python telemetry bridge (`telemetry_ffi`) and the `cosmic_coder.py` agent
can expose metrics over HTTP (default port `8086`).

### Automatic forwarding (lima-eden.yaml)

If you added the `portForwards` block in [Section 3](#3-create-a-vm), Lima
handles this automatically.  Open `http://localhost:8086` on macOS.

### Manual SSH forwarding

```sh
# Find the VM's SSH address
limactl list

# Forward port 8086 from VM to localhost
ssh -L 8086:localhost:8086 \
    -i ~/.lima/eden-dev/lima.pub \
    -p $(limactl list -f '{{.SSH.LocalPort}}' eden-dev) \
    user@127.0.0.1 -N
```

### Tracy GUI (macOS) ↔ Tracy agent (VM)

1. Build the Tracy profiler GUI on macOS (see
   [MACOS.md §11](MACOS.md#11-tracy-profiling-on-macos) for macOS-specific
   build instructions).
2. Add `portForwards: [{guestPort: 8765, hostPort: 8765}]` to your Lima config
   (the default Tracy port).
3. Run Eden ECS in the VM with `--features eden_ecs/tracy`.
4. Connect the Tracy GUI on macOS to `localhost:8765`.

---

## 10. Useful Lima commands

| Command | Description |
|---------|-------------|
| `limactl list` | List all VMs and their status |
| `limactl start eden-dev` | Start a stopped VM |
| `limactl stop eden-dev` | Gracefully stop the VM |
| `limactl shell eden-dev` | Open an interactive shell |
| `limactl shell eden-dev -- <cmd>` | Run a single command |
| `limactl copy <src> eden-dev:<dst>` | Copy file from host to VM |
| `limactl copy eden-dev:<src> <dst>` | Copy file from VM to host |
| `limactl delete eden-dev` | Delete the VM (frees disk) |
| `limactl factory-reset eden-dev` | Reset VM to initial state |
| `limactl info eden-dev` | Show VM configuration |

---

## 11. Troubleshooting

### `limactl: command not found`

```sh
brew install lima
```

### VM fails to start: `virtualization framework not available`

Your macOS version is below 13.  Change `vmType: vz` to `vmType: qemu` in
your Lima config:

```yaml
vmType: qemu
```

Or install QEMU directly:

```sh
brew install qemu
```

### `cargo: command not found` inside the VM

Rustup adds `~/.cargo/bin` to `PATH` only in interactive shells.  Add to
`~/.bashrc` (or `~/.zshrc`):

```sh
export PATH="$HOME/.cargo/bin:$PATH"
```

Then reload:

```sh
source ~/.bashrc
```

### Mount is read-only

Make sure `writable: true` is set in the Lima config for the mount:

```yaml
mounts:
  - location: "~/Developer/Ouroboros"
    writable: true
```

Then restart the VM:

```sh
limactl stop eden-dev && limactl start eden-dev
```

### DNS resolution fails inside the VM

```sh
# Inside VM
sudo systemd-resolve --flush-caches
sudo resolvectl dns eth0 8.8.8.8
```

Or add to your Lima config:

```yaml
dns:
  - 8.8.8.8
  - 1.1.1.1
```

### Build is slow on Apple Silicon with `vmType: qemu`

QEMU emulates `x86_64` in software on `aarch64` which is slow.  Switch to a
native `aarch64` image:

```yaml
arch: aarch64
vmType: vz
images:
  - location: "https://cloud-images.ubuntu.com/releases/24.04/release/ubuntu-24.04-server-cloudimg-arm64.img"
    arch: aarch64
```

Native ARM builds of `eden_ecs` are fully supported.
