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
