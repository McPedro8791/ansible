# ansible

## group_vars (git submodule)

`group_vars/` is a git submodule of
[McPedro8791/ansible-submodule](https://github.com/McPedro8791/ansible-submodule)
(public: no secrets in it). Ansible finds it through the symlink
`inventory/group_vars -> ../group_vars`, next to `inventory/hosts.ini`.

Clone with submodules: `git clone --recurse-submodules <url>` (the ansible-gui
backend and its SSH targets do this on their own). To take a newer `group_vars`:

    git -C group_vars pull origin main
    git add group_vars && git commit -m "Update group_vars" && git push

A run uses exactly the submodule commit this repository points to.

## Demo playbooks for the ansible-gui features

All of them run against `localhost` of the target and change at most files under `/tmp`. They are samples for the features of
[headlamp-ansible-plugin](https://github.com/McPedro8791/headlamp-ansible-plugin) (manuals in its `docs/`):

| Playbook | Shows |
|---|---|
| `dry-run-demo.yml` | dry run (`--check --diff`): first as a dry run with the diff, then for real, then again |
| `approval-demo.yml` | `# approval: required`: a real run waits for a second person |
| `timeout-retry-demo.yml` | `# timeout:` and `# retries:` |
| `precheck-demo.yml` | `# precheck:`: checks on the target before the run |
| `chain-backup-demo.yml`, `chain-upgrade-demo.yml` | `# requires:`: the backup runs first, then the upgrade |
| `secret-demo.yml` | `type=secret`: a typed-in password, never stored |
| `full-header-demo.yml` | every header line at once |
| `parameter-demo.yml`, `const-demo.yml`, `k8s-version-demo.yml`, `repo-dirs-demo.yml`, `openbao-demo.yml` | parameters of all types, constants, the Kubernetes version, lists from the repository, values from OpenBao |
