# Systemd unit files (canonical copies)

Version-controlled canonical copies of the systemd units installed on
organism infrastructure. The authoritative runtime copy lives at
`/etc/systemd/system/<unit>` on the target host; this directory is the
source of truth for disaster recovery and format auditing.

## Units

### `temporal-worker.service`
Host: **ganglion**
Purpose: mtor Temporal worker (translocase). Consumes tasks from the
`translation-queue` on Temporal, spawns ribosome subprocesses.

**Install / update:**
```bash
scp ~/germline/loci/systemd/temporal-worker.service \
    ganglion:/tmp/temporal-worker.service
ssh ganglion 'sudo mv /tmp/temporal-worker.service \
                       /etc/systemd/system/temporal-worker.service && \
              sudo systemctl daemon-reload && \
              sudo systemctl restart temporal-worker'
```

**Critical detail — do NOT use `EnvironmentFile=`** pointing at
`~/.env.bootstrap`. That file uses shell `export VAR=X` syntax, which
systemd's env file parser silently rejects, leaving `op run` without an
`OP_SERVICE_ACCOUNT_TOKEN` and crash-looping the worker. The unit wraps
its ExecStart in `bash -c 'source .env.bootstrap && exec op run ...'`
so the token actually reaches `op`. See
`~/epigenome/marks/finding_systemd_environmentfile_no_export.md`.
