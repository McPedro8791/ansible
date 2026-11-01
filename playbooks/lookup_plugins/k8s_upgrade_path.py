# -*- coding: utf-8 -*-
# Lookup plugin: the Kubernetes upgrade path from the version files of this
# checkout. Lives next to the playbook (playbooks/lookup_plugins/), which is
# where Ansible finds it without any configuration.
from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
name: k8s_upgrade_path
short_description: Upgrade steps between the installed and a target Kubernetes minor version
description:
  - Reads the version files C(versions/<version>.yml) of the checked-out repository (for example
    C(1.36.2.yml), C(1.37.5.yml) or just C(1.37.yml)) and returns the steps to go from the
    installed version to the target, one step per minor version.
  - From every minor version the newest file is used (several may exist for one minor; a file without
    patch number, C(1.37.yml), counts as the oldest of its minor).
  - The installed minor version is only a step when a newer patch release of it exists than the one
    installed. Every minor between the installed and the target one is a step and must have a file
    (minor versions are never skipped); a missing one is an error.
options:
  current:
    description: The installed version, C(1.36.1) (a minor-only C(1.36) is taken as up to date).
    type: str
    required: true
  target:
    description: The target minor version, C(1.38) (a full version is shortened to its minor).
      Empty means the newest minor version found in the versions directory.
    type: str
    default: ''
  dir:
    description: The directory with the version files. By default C(<playbook_dir>/../versions),
      C(<playbook_dir>/versions) and C(./versions) are tried in this order.
    type: str
    default: ''
return:
  _list:
    description: One dict per step in install order, with C(minor) (C(1.37)), C(version) (C(1.37.5), the
      file name without C(.yml)), C(file) (absolute path) and C(name) (file name).
    type: list
    elements: dict
"""

import os
import re

from ansible.errors import AnsibleError
from ansible.plugins.lookup import LookupBase

FILE_RE = re.compile(r"^(\d+)\.(\d+)(?:\.(\d+))?\.ya?ml$")
VERSION_RE = re.compile(r"^v?(\d+)\.(\d+)(?:\.(\d+))?")


def _find_dir(explicit, variables):
    if explicit:
        candidates = [explicit]
    else:
        playbook_dir = (variables or {}).get("playbook_dir") or os.getcwd()
        candidates = [
            os.path.join(playbook_dir, "..", "versions"),
            os.path.join(playbook_dir, "versions"),
            os.path.join(os.getcwd(), "versions"),
        ]
    for c in candidates:
        if os.path.isdir(c):
            return os.path.abspath(c)
    raise AnsibleError("k8s_upgrade_path: no versions directory found (looked in: %s)" % ", ".join(os.path.abspath(c) for c in candidates))


def _newest_per_minor(directory):
    """{(major, minor): (patch, file name)}; a file without patch number has patch -1."""
    best = {}
    for name in os.listdir(directory):
        m = FILE_RE.match(name)
        if not m:
            continue
        key = (int(m.group(1)), int(m.group(2)))
        patch = int(m.group(3)) if m.group(3) is not None else -1
        if key not in best or patch > best[key][0]:
            best[key] = (patch, name)
    return best


def build_path(directory, current, target):
    best = _newest_per_minor(directory)
    if not best:
        raise AnsibleError("k8s_upgrade_path: no version files (<version>.yml) in %s" % directory)

    cm = VERSION_RE.match(str(current or "").strip())
    if not cm:
        raise AnsibleError("k8s_upgrade_path: the installed version %r is not a Kubernetes version (like 1.36.1)" % (current,))
    cur_key = (int(cm.group(1)), int(cm.group(2)))
    cur_patch = int(cm.group(3)) if cm.group(3) is not None else None

    if str(target or "").strip():
        tm = VERSION_RE.match(str(target).strip())
        if not tm:
            raise AnsibleError("k8s_upgrade_path: the target %r is not a Kubernetes minor version (like 1.38)" % (target,))
        tgt_key = (int(tm.group(1)), int(tm.group(2)))
        if tgt_key not in best:
            have = ", ".join("%d.%d" % k for k in sorted(best))
            raise AnsibleError("k8s_upgrade_path: no version file for the target %d.%d in %s (available minor versions: %s)" % (tgt_key + (directory, have)))
    else:
        tgt_key = max(best)

    if tgt_key[0] != cur_key[0]:
        raise AnsibleError("k8s_upgrade_path: going from major version %d to %d is not supported" % (cur_key[0], tgt_key[0]))
    if tgt_key < cur_key:
        raise AnsibleError("k8s_upgrade_path: the target %d.%d is older than the installed %d.%d - downgrades are not supported" % (tgt_key + cur_key))

    keys = []
    # the installed minor: only when a newer patch release exists
    if cur_key in best and cur_patch is not None and best[cur_key][0] > cur_patch:
        keys.append(cur_key)
    # every minor in between and the target: none may be missing
    missing = [k for k in ((cur_key[0], m) for m in range(cur_key[1] + 1, tgt_key[1] + 1)) if k not in best]
    if missing:
        raise AnsibleError("k8s_upgrade_path: no version file for %s - minor versions cannot be skipped on the way from %d.%d to %d.%d" % (
            ", ".join("%d.%d" % k for k in missing), cur_key[0], cur_key[1], tgt_key[0], tgt_key[1]))
    keys.extend((cur_key[0], m) for m in range(cur_key[1] + 1, tgt_key[1] + 1))

    steps = []
    for key in keys:
        name = best[key][1]
        steps.append({
            "minor": "%d.%d" % key,
            "version": re.sub(r"\.ya?ml$", "", name),
            "file": os.path.join(directory, name),
            "name": name,
        })
    return steps


class LookupModule(LookupBase):
    def run(self, terms, variables=None, **kwargs):
        self.set_options(var_options=variables, direct=kwargs)
        directory = _find_dir(self.get_option("dir"), variables)
        return build_path(directory, self.get_option("current"), self.get_option("target"))
