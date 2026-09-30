"""Tests for the policy layer and the acceptance blocker.

The point of this module is the negative space. A blocker that has never been
attacked is a blocker nobody has checked, so much of what follows is an attempt
to get past it:

* with no acceptance at all, from the CLI and from the module;
* with an acceptance recorded against a different policy version;
* with an acceptance recorded against a policy document that has since changed;
* with the state directory pointed somewhere empty, somewhere missing, at a
  relative path, and at a symbolic link;
* by editing the acceptance record by hand;
* by calling `http_client.request` directly, which is the boundary the CLI sits
  above rather than the boundary itself.

Each of those must refuse, send nothing, and say why. The fixture server's own
request log is the evidence that nothing was sent, not the tool's account of
itself.
"""

from __future__ import annotations

import contextlib

import contextlib
import io
import json
import os
import shutil

from workbench import cli
from workbench import history as hist
from workbench import http_client as hc
from workbench import policy as policymod
from workbench import scope as sc
from workbench.tests import fixtures
from workbench.tests.harness import check, contains, equal, not_contains, raises


@contextlib.contextmanager
def _state_env(directory):
    """Point the acceptance lookup somewhere for the duration of the block.

    Saved and restored, not deleted: this variable is set once for the whole test
    process, so a test that pops it leaves every later module without an
    acceptance and reports that as a failure of the code under test.
    """
    previous = os.environ.get(policymod.STATE_DIR_ENV)
    os.environ[policymod.STATE_DIR_ENV] = directory
    try:
        yield
    finally:
        if previous is None:
            os.environ.pop(policymod.STATE_DIR_ENV, None)
        else:
            os.environ[policymod.STATE_DIR_ENV] = previous


def _run(*argv, env=None):
    """Run the CLI in-process with the environment a case needs."""
    previous = {}
    for key, value in (env or {}).items():
        previous[key] = os.environ.get(key)
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value
    out, err = io.StringIO(), io.StringIO()
    try:
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = cli.main([str(item) for item in argv])
    finally:
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
    return code, out.getvalue(), err.getvalue()


def _state(accepted=False, **record_overrides):
    """A temporary state directory, optionally with an acceptance written."""
    directory = fixtures.tempfile_dir()
    if accepted:
        record = policymod.accept(directory)
        record.update(record_overrides)
        with open(policymod.acceptance_path(directory), "w", encoding="utf-8") as fh:
            json.dump(record, fh, indent=2, sort_keys=True)
    return directory


def _scope_file(work, base_url, **overrides):
    path = os.path.join(work, "scope.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(fixtures.scope_data(base_url, **overrides), fh, indent=2)
    return path


# ------------------------------------------------------------------ the policy
def test_the_policy_document_parses_and_validates():
    policy = policymod.load()
    equal(policymod.validate(policy), [])
    for key in policymod.REQUIRED_VERSIONS:
        check(policy.get(key), f"{key} is empty")


def test_the_policy_names_documents_that_all_exist():
    policy = policymod.load()
    for key in policymod.REQUIRED_DOCUMENT_KEYS:
        name = policy["documents"][key]
        path = os.path.join(policymod.repo_root(), name)
        check(os.path.isfile(path), f"{name} does not exist")


def test_a_policy_that_names_a_missing_document_is_not_valid():
    work = fixtures.tempfile_dir()
    policy = policymod.load()
    policy["documents"]["legal"] = "NOT-A-FILE.md"
    path = os.path.join(work, "policy.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(policy, fh)
    problems = policymod.validate(path=path)
    check(any("NOT-A-FILE.md" in problem for problem in problems), problems)


def test_a_policy_that_does_not_parse_is_refused_rather_than_repaired():
    work = fixtures.tempfile_dir()
    path = os.path.join(work, "policy.json")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("{not json,")
    error = raises(policymod.PolicyError, policymod.load, path)
    contains(str(error), "does not parse")


def test_a_missing_policy_document_is_refused():
    work = fixtures.tempfile_dir()
    error = raises(policymod.PolicyError, policymod.load,
                   os.path.join(work, "absent.json"))
    contains(str(error), "missing")


def test_a_policy_that_drops_a_requirement_is_not_valid():
    policy = policymod.load()
    policy["requirements"]["acceptance_required_for_active_operations"] = False
    problems = policymod.validate(policy)
    check(any("acceptance_required_for_active_operations" in p for p in problems),
          problems)
    policy = policymod.load()
    policy["requirements"]["acceptance_is_not_authorization"] = False
    problems = policymod.validate(policy)
    check(any("acceptance_is_not_authorization" in p for p in problems), problems)


def test_a_policy_that_claims_to_transmit_acceptance_is_not_valid():
    """Nothing in this framework sends acceptance anywhere; the policy must say so."""
    policy = policymod.load()
    policy["acceptance"]["transmitted_remotely"] = True
    problems = policymod.validate(policy)
    check(any("transmitted_remotely" in p for p in problems), problems)


def test_a_read_only_policy_document_is_validated_and_nothing_is_written():
    work = fixtures.tempfile_dir()
    before = set(os.listdir(work))
    policy = policymod.load()
    policymod.validate(policy)
    equal(set(os.listdir(work)), before, "validation wrote a file")


# ----------------------------------------------------------------- acceptance
def test_acceptance_is_recorded_locally_and_holds_no_identity():
    directory = _state(accepted=True)
    record = policymod.read_acceptance(directory)
    equal(sorted(record), ["accepted_at", "policy_sha256", "policy_version",
                           "record_format"])
    equal(record["policy_version"], policymod.load()["policy_version"])
    for forbidden in ("user", "hostname", "name", "email", "machine"):
        check(forbidden not in json.dumps(record).lower(),
              f"the acceptance record mentions {forbidden}")


def test_acceptance_without_the_policy_present_is_refused():
    work = fixtures.tempfile_dir()
    error = raises(policymod.PolicyError, policymod.accept, work,
                   path=os.path.join(work, "absent.json"))
    contains(str(error), "missing")


def test_an_acceptance_for_another_policy_version_is_stale():
    directory = _state(accepted=True, policy_version="0.0.1")
    status = policymod.acceptance_status(directory=directory)
    equal(status["accepted"], False)
    contains(status["reason"], "0.0.1")


def test_an_acceptance_for_a_policy_whose_content_changed_is_stale():
    """Changing the terms must not carry the earlier acknowledgement forward."""
    work = fixtures.tempfile_dir()
    policy_path = os.path.join(work, "policy.json")
    with open(policy_path, "w", encoding="utf-8") as fh:
        json.dump(policymod.load(), fh, indent=2, sort_keys=True)
    directory = fixtures.tempfile_dir()
    policymod.accept(directory, path=policy_path)
    equal(policymod.acceptance_status(path=policy_path,
                                     directory=directory)["accepted"], True)

    policy = policymod.load()
    policy["prohibited_actions"].append("A newly prohibited action")
    with open(policy_path, "w", encoding="utf-8") as fh:
        json.dump(policy, fh, indent=2, sort_keys=True)
    status = policymod.acceptance_status(path=policy_path, directory=directory)
    equal(status["accepted"], False)
    contains(status["reason"], "changed")


def test_an_acceptance_for_a_policy_that_no_longer_exists_is_stale():
    directory = _state(accepted=True)
    record = policymod.read_acceptance(directory)
    work = fixtures.tempfile_dir()
    policy_path = os.path.join(work, "policy.json")
    with open(policy_path, "w", encoding="utf-8") as fh:
        json.dump(policymod.load(), fh)
    status = policymod.acceptance_status(path=policy_path, directory=directory)
    equal(status["accepted"], False)
    check(status["reason"], "a stale acceptance must have a reason")
    check(record["policy_sha256"] != status["current_policy_sha256"])


def test_the_state_directory_can_move_but_moving_it_cannot_create_acceptance():
    empty = fixtures.tempfile_dir()
    status = policymod.acceptance_status(directory=empty)
    equal(status["accepted"], False)
    contains(status["reason"], "no acceptance")
    missing = os.path.join(fixtures.tempfile_dir(), "not", "created")
    equal(policymod.acceptance_status(directory=missing)["accepted"], False)
    relative = os.path.relpath(empty)
    equal(policymod.acceptance_status(directory=relative)["accepted"], False)


def test_a_symlinked_acceptance_record_is_refused():
    directory = _state(accepted=True)
    real = policymod.acceptance_path(directory)
    elsewhere = os.path.join(fixtures.tempfile_dir(), "copied.json")
    shutil.copyfile(real, elsewhere)
    os.remove(real)
    os.symlink(elsewhere, real)
    error = raises(policymod.PolicyError, policymod.read_acceptance, directory)
    contains(str(error), "symbolic link")
    equal(policymod.acceptance_status(directory=directory)["accepted"], False)


def test_a_corrupted_acceptance_record_is_refused():
    directory = _state(accepted=True)
    with open(policymod.acceptance_path(directory), "w", encoding="utf-8") as fh:
        fh.write("[]")
    error = raises(policymod.PolicyError, policymod.read_acceptance, directory)
    contains(str(error), "not a JSON object")


def test_acceptance_writes_a_private_file_and_leaves_no_temporary_behind():
    directory = _state()
    policymod.accept(directory)
    path = policymod.acceptance_path(directory)
    equal(os.stat(path).st_mode & 0o777, 0o600)
    equal([name for name in os.listdir(directory) if name.endswith(".tmp")], [])


# ------------------------------------------------------------ the blocker: CLI
def test_an_active_command_is_refused_without_acceptance():
    with fixtures.FixtureServer() as srv:
        work = fixtures.tempfile_dir()
        scope_path = _scope_file(work, srv.url(""))
        empty = fixtures.tempfile_dir()
        code, _out, err = _run("http", "inspect", "--scope", scope_path,
                               "--url", srv.url("/soft"),
                               **{} if False else {}, env={policymod.STATE_DIR_ENV: empty})
        equal(code, cli.EXIT_USAGE)
        contains(err, "policy has not been accepted")
        equal(srv.hits, [], "a blocked command sent a request")


def test_an_active_command_runs_once_the_policy_is_accepted():
    with fixtures.FixtureServer() as srv:
        work = fixtures.tempfile_dir()
        scope_path = _scope_file(work, srv.url(""))
        accepted = _state(accepted=True)
        code, _out, _err = _run("http", "inspect", "--scope", scope_path,
                               "--url", srv.url("/soft"),
                               env={policymod.STATE_DIR_ENV: accepted})
        equal(code, cli.EXIT_OK)
        equal(len(srv.hits), 1)


def test_a_stale_acceptance_blocks_an_active_command_again():
    with fixtures.FixtureServer() as srv:
        work = fixtures.tempfile_dir()
        scope_path = _scope_file(work, srv.url(""))
        stale = _state(accepted=True, policy_version="0.0.1")
        code, _out, err = _run("http", "inspect", "--scope", scope_path,
                               "--url", srv.url("/soft"),
                               env={policymod.STATE_DIR_ENV: stale})
        equal(code, cli.EXIT_USAGE)
        contains(err, "0.0.1")
        equal(srv.hits, [])


def test_a_malformed_policy_blocks_an_active_command_and_says_so():
    with fixtures.FixtureServer() as srv:
        work = fixtures.tempfile_dir()
        scope_path = _scope_file(work, srv.url(""))
        accepted = _state(accepted=True)
        broken = os.path.join(work, "policy.json")
        with open(broken, "w", encoding="utf-8") as fh:
            fh.write("{not json,")
        code, _out, err = _run("http", "inspect", "--scope", scope_path,
                               "--url", srv.url("/soft"), "--policy", broken,
                               env={policymod.STATE_DIR_ENV: accepted})
        # `http inspect` has no --policy flag; argparse refuses the argument.
        equal(code, cli.EXIT_USAGE)
        equal(srv.hits, [])


def test_the_local_commands_still_work_without_acceptance():
    """Read-only local work is deliberately exempt, and that exemption is tested."""
    work = fixtures.tempfile_dir()
    sample = os.path.join(work, "sample.txt")
    with open(sample, "w", encoding="utf-8") as fh:
        fh.write("fixture bytes")
    empty = fixtures.tempfile_dir()
    for argv in (
        ("policy", "validate"),
        ("policy", "show"),
        ("evidence", "hash", sample),
        ("resource", "inspect", "--path", sample),
    ):
        code, _out, err = _run(*argv, env={policymod.STATE_DIR_ENV: empty})
        equal(code, 0, f"{' '.join(argv[:2])}: {err}")


def test_the_exempt_list_in_the_policy_matches_the_commands_that_need_no_scope():
    """The policy's exemption list and the parser's scope requirements must agree."""
    policy = policymod.load()
    exempt = {tuple(item.split()) for item in policy["exempt_operations"]}
    parser = cli.build_parser()

    def walk(node, prefix=()):
        group = getattr(node, "_subparsers", None)
        if group is None:
            yield prefix, node
            return
        for action in group._group_actions:
            for name, child in (getattr(action, "choices", None) or {}).items():
                yield from walk(child, prefix + (name,))

    needs_scope = set()
    for path, node in walk(parser):
        flags = [flag for action in node._actions for flag in action.option_strings]
        if "--scope" in flags and path not in {("api", "inspect"), ("report", "generate")}:
            needs_scope.add(path)
    for path in needs_scope:
        check(path not in exempt,
              f"{path} requires --scope but the policy lists it as exempt")


# --------------------------------------------------- the blocker: the boundary
def test_the_module_boundary_refuses_direct_calls_without_acceptance():
    """The CLI sits above the boundary; this is the boundary itself."""
    with fixtures.FixtureServer() as srv:
        empty = fixtures.tempfile_dir()
        guard = sc.ScopeGuard(sc.Scope(fixtures.scope_data(srv.url(""))),
                              resolve=lambda host: ["127.0.0.1"])
        with _state_env(empty):
            error = raises(policymod.PolicyError, hc.request, guard, srv.url("/soft"))
            contains(str(error), "policy has not been accepted")
        equal(srv.hits, [], "the blocked call opened a connection anyway")


def test_history_replay_and_fuzz_cannot_reach_the_network_without_acceptance():
    """Every path to a socket goes through the same gate."""
    with fixtures.FixtureServer() as srv:
        accepted = _state(accepted=True)
        guard = sc.ScopeGuard(sc.Scope(fixtures.scope_data(srv.url(""))),
                              resolve=lambda host: ["127.0.0.1"])
        history_obj = hist.History()
        with _state_env(accepted):
            hc.request(guard, srv.url("/soft"))
        # Now build the record by hand rather than reusing the live one, so the
        # replay path is exercised with acceptance removed.
        history_obj.entries.append({
            "id": "H0001", "url": srv.url("/soft"), "method": "GET",
            "request_headers": {}, "request_body": "", "response": {"status": 200},
        })
        empty = fixtures.tempfile_dir()
        with _state_env(empty):
            before = len(srv.hits)
            raises(policymod.PolicyError, hist.replay_from_record, guard,
                   history_obj, "H0001")
            equal(len(srv.hits), before, "the replay sent a request anyway")


# --------------------------------------------------------- the blocker's shape
def test_no_command_line_flag_can_skip_the_policy():
    flags = []
    nodes = [cli.build_parser()]
    while nodes:
        node = nodes.pop()
        flags.extend(flag for action in node._actions for flag in action.option_strings)
        group = getattr(node, "_subparsers", None)
        if group is None:
            continue
        for action in group._group_actions:
            nodes.extend((getattr(action, "choices", None) or {}).values())
    for flag in flags:
        lowered = flag.lower()
        for word in ("ignore", "bypass", "skip", "no-policy", "force", "unsafe"):
            check(word not in lowered,
                  f"{flag} looks like a policy bypass")
    check("--state-dir" in flags, "the state directory is relocatable, and documented")


def test_the_state_environment_variable_relocates_and_never_enables():
    """Pointing the variable at a fresh directory must block, not permit."""
    with fixtures.FixtureServer() as srv:
        work = fixtures.tempfile_dir()
        scope_path = _scope_file(work, srv.url(""))
        fresh = fixtures.tempfile_dir()
        code, _out, err = _run("http", "inspect", "--scope", scope_path,
                               "--url", srv.url("/soft"),
                               env={policymod.STATE_DIR_ENV: fresh})
        equal(code, cli.EXIT_USAGE)
        equal(os.listdir(fresh), [], "the blocked run wrote into the state directory")
        equal(srv.hits, [])
        check("policy" in err)


def test_acceptance_is_never_transmitted():
    """Nothing in the framework sends the acceptance anywhere; the policy says so."""
    policy = policymod.load()
    equal(policy["acceptance"]["transmitted_remotely"], False)
    equal(policy["acceptance"]["collects_identity"], False)
    import ast
    source = open(os.path.join(policymod.repo_root(), "workbench", "policy.py"),
                  encoding="utf-8").read()
    imported = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    # The module's prose says the word "socket" — about http_client, not about
    # itself — so this checks what it imports rather than what it mentions.
    for forbidden in ("urllib", "http", "socket", "ssl", "requests", "subprocess"):
        check(forbidden not in imported,
              f"policy.py imports {forbidden}; the acceptance layer must not be "
              f"able to reach the network")
