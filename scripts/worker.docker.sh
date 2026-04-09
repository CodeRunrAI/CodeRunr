#!/bin/bash
set -e

ensure_isolate_dirs() {
    install -d -m 0700 -o root -g root /var/local/lib/isolate
    install -d -m 0700 -o root -g root /run/isolate
    install -d -m 0700 -o root -g root /run/isolate/locks
}

setup_cgroup_v2() {
    local cg_root="/sys/fs/cgroup"
    local isolate_root="${cg_root}/isolate"

    if [[ ! -d "${cg_root}" ]]; then
        echo "Isolate warning: ${cg_root} is not mounted; cgroup mode may fail." >&2
        return
    fi

    if [[ -f "${cg_root}/cgroup.subtree_control" ]]; then
        echo "+cpu +memory +pids" > "${cg_root}/cgroup.subtree_control" 2>/dev/null || true
    fi

    mkdir -p "${isolate_root}" 2>/dev/null || true

    if [[ -f "${isolate_root}/cgroup.subtree_control" ]]; then
        echo "+cpu +memory +pids" > "${isolate_root}/cgroup.subtree_control" 2>/dev/null || true
    fi
}

ensure_isolate_dirs
setup_cgroup_v2

# Best-effort kernel tuning recommended by Isolate.
sysctl -w fs.protected_hardlinks=1 2>/dev/null || true

# Work around runtimes where / is not already a mount point.
mount --bind / / 2>/dev/null || true

# Swap weakens memory accounting, so disable it when the runtime permits.
swapoff -a 2>/dev/null || true

# Run celery worker
echo "Starting Celery worker..."
exec uv run celery --app=worker.celery worker --loglevel=INFO
