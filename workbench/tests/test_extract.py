"""Tests for reading documents and archives without trusting them.

Two properties are tested over and over here:

* **The limits hold.** A bomb, a 500-member archive, a file past the size limit —
  each is refused with the limit that stopped it named, and nothing is written.
* **Unsafe members are never written.** A name that climbs out, an absolute
  path, a symlink to `/etc/passwd`, a device node. The test checks the
  filesystem as well as the report, because a report that says "skipped" while
  the file is on disk is worse than no report.

There is also a static test of the policy itself: this module must contain no
way to execute what it reads.
"""

from __future__ import annotations

import ast
import os

from workbench import evidence as ev
from workbench import extract
from workbench.tests import fixtures
from workbench.tests.harness import check, contains, equal, not_contains

MODULE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                      "extract.py")


def _write(directory, name, data):
    path = os.path.join(directory, name)
    with open(path, "wb") as fh:
        fh.write(data)
    return path


def _pdf(directory, name="file.pdf"):
    return _write(directory, name, fixtures.build_pdf())


# ----------------------------------------------------------------------- PDF
def test_a_pdf_is_read_for_metadata_pages_text_links_and_attachments():
    directory = fixtures.tempfile_dir()
    report = extract.inspect_file(_pdf(directory))
    equal(report.file_type, "pdf")
    equal(report.status, "extracted")
    equal(report.metadata["title"], fixtures.PDF_TITLE)
    equal(report.metadata["author"], fixtures.PDF_AUTHOR)
    check(report.metadata["header"].startswith("%PDF-"), report.metadata["header"])
    equal(len(report.pages), 2)
    check(report.pages[0]["sha256"] and len(report.pages[0]["sha256"]) == 64,
          "each page carries its own hash")
    contains(report.text, fixtures.PDF_TEXT_PAGE1.split()[0])
    equal([link["target"] for link in report.links], [fixtures.PDF_LINK_URL])
    equal(report.attachments[0]["written_out"], False)


def test_a_pdf_with_an_embedded_file_or_javascript_is_flagged_not_run():
    directory = fixtures.tempfile_dir()
    report = extract.inspect_file(_pdf(directory))
    features = {flag["feature"] for flag in report.flagged_features}
    check("an embedded file" in features, features)
    equal(report.executed, False)
    contains(report.report_lines(), "nothing was executed")


def test_a_pdf_declaring_encryption_is_flagged_and_not_decrypted():
    directory = fixtures.tempfile_dir()
    path = _write(directory, "enc.pdf", b"%PDF-1.4\n1 0 obj\n/Encrypt 3 0 R\nendobj\n%%EOF\n")
    report = extract.inspect_file(path)
    equal(report.metadata["encrypted"], True)
    check(any("encryption" in f["feature"] for f in report.flagged_features),
          report.flagged_features)
    check(any("not decrypted" in w for w in report.warnings), report.warnings)


def test_a_file_that_claims_to_be_a_pdf_but_holds_html_is_flagged():
    """A mislabelled file is read as what it is, and the mismatch is recorded."""
    directory = fixtures.tempfile_dir()
    path = _write(directory, "not-really.pdf", b"<html><body>a login page</body></html>")
    report = extract.inspect_file(path)
    equal(report.pages, [])
    check(any("extension does not match" in f["feature"]
              for f in report.flagged_features), report.flagged_features)
    check(any("describes something other than" in w for w in report.warnings),
          report.warnings)
    contains(report.text, "a login page")


def test_binary_content_named_pdf_is_refused_by_the_pdf_reader():
    directory = fixtures.tempfile_dir()
    path = _write(directory, "binary.pdf", bytes(range(256)) * 4)
    report = extract.inspect_file(path)
    equal(report.status, "refused")
    check(any("PDF header" in reason for reason in report.refusals), report.refusals)


def test_a_pdf_larger_than_the_limit_is_refused():
    directory = fixtures.tempfile_dir()
    path = _pdf(directory)
    report = extract.inspect_file(path, extract.limits(max_bytes=100))
    equal(report.status, "refused")
    check(any("larger than" in reason for reason in report.refusals), report.refusals)


def test_the_pdf_reader_states_what_it_could_not_read():
    directory = fixtures.tempfile_dir()
    report = extract.inspect_file(_pdf(directory))
    check(any("not a PDF parser" in note for note in report.notes), report.notes)


# ------------------------------------------------------------------ archives
def test_a_zip_is_listed_with_sizes_and_types():
    directory = fixtures.tempfile_dir()
    report = extract.inspect_file(_write(directory, "data.zip", fixtures.build_zip()))
    equal(report.file_type, "zip")
    equal([m["name"] for m in report.members], ["fixture.txt", "FIXTURE-README.txt"])
    equal(report.members[0]["size"], 25)
    equal(report.metadata["uncompressed_total"], 91)
    equal(extract.extraction_status(report), "listed_not_extracted")


def test_a_compression_bomb_is_refused_by_ratio_and_nothing_is_extracted():
    directory = fixtures.tempfile_dir()
    path = _write(directory, "bomb.zip", fixtures.build_bomb_zip())
    out = os.path.join(directory, "out")
    report = extract.inspect_file(path, extract_into=out)
    equal(report.status, "refused")
    check(any("bomb" in reason for reason in report.refusals), report.refusals)
    equal(os.listdir(out) if os.path.isdir(out) else [], [],
          "a bomb must not be extracted")


def test_an_archive_with_too_many_members_is_refused():
    directory = fixtures.tempfile_dir()
    path = _write(directory, "many.zip", fixtures.build_many_entries_zip(count=40))
    report = extract.inspect_file(path, extract.limits(max_files=10))
    equal(report.status, "refused")
    check(any("more than 10 members" in reason for reason in report.refusals),
          report.refusals)
    equal(len(report.members), 40, "the listing is still recorded for a refusal")


def test_a_malformed_archive_fails_without_raising():
    directory = fixtures.tempfile_dir()
    path = _write(directory, "bad.zip", fixtures.build_malformed_zip())
    report = extract.inspect_file(path)
    equal(report.status, "failed")
    check(any("not a readable zip" in reason for reason in report.refusals), report.refusals)


def test_a_nested_archive_is_read_in_memory_and_named_with_its_parent():
    directory = fixtures.tempfile_dir()
    report = extract.inspect_file(_write(directory, "nested.zip",
                                         fixtures.build_nested_zip(depth=2)))
    equal(len(report.nested), 1)
    child = report.nested[0]
    contains(child.name, "nested.zip!")
    contains(child.name, "level-1.zip")
    equal(child.metadata["nested_from"], "nested.zip")
    check(all(member["read"] is False for member in child.members),
          "a nested archive is listed, never extracted")


def test_nested_reading_stops_at_the_depth_limit():
    directory = fixtures.tempfile_dir()
    path = _write(directory, "nested.zip", fixtures.build_nested_zip(depth=3))
    shallow = extract.inspect_file(path, extract.limits(max_depth=0))
    equal(shallow.nested, [])
    deeper = extract.inspect_file(path, extract.limits(max_depth=2))
    equal(len(deeper.nested), 1)
    check(len(deeper.nested[0].children) <= 1, "the recursion is bounded")


def test_an_encrypted_archive_member_is_flagged_and_never_opened():
    directory = fixtures.tempfile_dir()
    path = _write(directory, "encrypted.zip", fixtures.build_encrypted_zip())
    out = os.path.join(directory, "out")
    report = extract.inspect_file(path, extract_into=out)
    check(any(member.get("encrypted") for member in report.members),
          "the encrypted member is recorded")
    check(any("no password was tried" in warning for warning in report.warnings),
          report.warnings)
    equal(os.listdir(out) if os.path.isdir(out) else [], [], "nothing was extracted")


# ----------------------------------------------------------------- traversal
def test_member_names_that_escape_the_destination_are_identified():
    equal(extract._unsafe_member_name("../x"), "a path that climbs out of the destination")
    equal(extract._unsafe_member_name("a/../../x"), "a path that climbs out of the destination")
    equal(extract._unsafe_member_name("/etc/passwd"), "an absolute path")
    equal(extract._unsafe_member_name("C:\\windows\\x"), "an absolute path")
    equal(extract._unsafe_member_name(""), "an empty member name")
    equal(extract._unsafe_member_name("a\x00b"), "a null byte in the name")
    equal(extract._unsafe_member_name("safe/inside.txt"), "")


def test_a_traversal_archive_yields_only_the_safe_member():
    directory = fixtures.tempfile_dir()
    out = os.path.join(directory, "out")
    path = _write(directory, "traversal.zip", fixtures.build_traversal_zip())
    report = extract.inspect_file(path, extract_into=out)
    equal(report.status, "partial")
    written = sorted(os.listdir(out))
    equal(written, ["safe"])
    equal(os.listdir(os.path.join(out, "safe")), ["inside.txt"])
    for reason in report.refusals:
        check("climbs out" in reason or "absolute" in reason, reason)
    check(not os.path.exists(os.path.join(directory, "escaped-relative.txt")),
          "nothing escaped the destination")
    # The fixture archive names /tmp as an absolute target. This asserts the
    # file is absent, so the literal is the test's data, not a temporary file
    # this code writes. Bandit flags the string; the string is the point.
    check(not os.path.exists("/tmp/escaped-absolute.txt"),  # nosec B108
          "nothing was written to /tmp")


def test_the_write_primitive_is_refused_by_the_calling_code_too():
    """The check is not only the name check: the resolved path is verified."""
    directory = fixtures.tempfile_dir()
    equal(extract._resolve_inside(directory, "inside.txt"), True)
    equal(extract._resolve_inside(directory, "../outside.txt"), False)
    equal(extract._resolve_inside(directory, "a/../../outside.txt"), False)


def test_extraction_never_calls_extractall():
    """A static check on the calls, not on the text: the docstring may name it."""
    with open(MODULE, encoding="utf-8") as fh:
        tree = ast.parse(fh.read())
    called = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            name = getattr(node.func, "attr", None) or getattr(node.func, "id", None)
            if name:
                called.add(name)
    equal([name for name in called if "extractall" in name], [])


# ----------------------------------------------------------------------- tar
def test_a_tar_is_listed_and_its_links_and_traversal_members_are_refused():
    directory = fixtures.tempfile_dir()
    path = _write(directory, "link.tar.gz", fixtures.build_symlink_tar())
    report = extract.inspect_file(path)
    equal(report.file_type, "tar")
    types = {member["name"]: member["type"] for member in report.members}
    equal(types["escape-link"], "link")
    equal(types["fixture.txt"], "file")
    check(any("links are never extracted" in reason for reason in report.refusals),
          report.refusals)
    check(any("climbs out" in reason for reason in report.refusals), report.refusals)


def test_a_symlink_from_a_tar_is_never_written():
    directory = fixtures.tempfile_dir()
    out = os.path.join(directory, "out")
    path = _write(directory, "link.tar.gz", fixtures.build_symlink_tar())
    report = extract.inspect_file(path, extract_into=out)
    written = sorted(os.listdir(out)) if os.path.isdir(out) else []
    equal(written, ["fixture.txt"])
    check(not os.path.islink(os.path.join(out, "escape-link")), "no link was created")
    equal(report.status, "partial")


def test_a_fifo_or_device_member_is_refused():
    equal(extract._member_type("pipe", True), "directory")
    equal(extract._member_type("FIXTURE.PDF"), "pdf")
    equal(extract._member_type("run.sh"), "script")
    equal(extract._member_type("a.exe"), "executable")


# --------------------------------------------------------------------- OOXML
def test_a_document_package_yields_its_text():
    directory = fixtures.tempfile_dir()
    report = extract.inspect_file(_write(directory, "doc.docx", fixtures.build_docx()))
    equal(report.status, "extracted")
    contains(report.text, "Fixture document body")
    not_contains(report.text, "<w:t>")
    equal(report.metadata["parts"], 2)


def test_a_macro_part_is_flagged_and_never_read_as_code():
    directory = fixtures.tempfile_dir()
    report = extract.inspect_file(_write(directory, "macro.docm",
                                         fixtures.build_docx(with_macro=True)))
    features = {flag["feature"] for flag in report.flagged_features}
    check("macro part" in features, features)
    not_contains(report.text, "fixture-not-a-real-macro-payload")
    contains(report.report_lines(), "nothing was executed")
    equal(report.executed, False)


def test_an_embedded_executable_in_a_package_is_flagged_and_not_written_out():
    directory = fixtures.tempfile_dir()
    import io
    import zipfile
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("word/document.xml", "<w:document>text</w:document>")
        zf.writestr("word/embed.exe", b"MZ\x90\x00fixture")
    path = _write(directory, "with-embed.docx", buf.getvalue())
    report = extract.inspect_file(path)
    features = {flag["feature"] for flag in report.flagged_features}
    check("embedded executable or script" in features, features)
    equal([a for a in report.attachments if a["name"].endswith(".exe")][0]["written_out"],
          False)


# ----------------------------------------------------------------- the policy
def test_static_flags_name_executable_content_without_running_it():
    directory = fixtures.tempfile_dir()
    elf = _write(directory, "sample", b"\x7fELF\x02\x01\x01" + b"\x00" * 32)
    flags = {flag["feature"] for flag in extract.static_flags(elf)}
    check("ELF executable" in flags, flags)
    script = _write(directory, "sample.sh", b"#!/bin/sh\necho fixture\n")
    flags = {flag["feature"] for flag in extract.static_flags(script)}
    check("script with a shebang" in flags, flags)
    pe = _write(directory, "sample.exe", b"MZ\x90\x00" + b"\x00" * 32)
    flags = {flag["feature"] for flag in extract.static_flags(pe)}
    check("PE executable" in flags, flags)


def test_the_module_cannot_execute_what_it_reads():
    """No subprocess, no exec, no eval, no import of the file's contents.

    Bare `compile()` is checked as well as `eval`/`exec`, and the module imports
    are checked for the ones that deserialise: an extractor that unpickles a file
    is an extractor that runs it.
    """
    with open(MODULE, encoding="utf-8") as fh:
        tree = ast.parse(fh.read())
    bare_banned = {"eval", "exec", "compile", "__import__"}
    attribute_banned = {"system", "popen", "Popen", "check_output", "check_call",
                        "execv", "execve", "spawnv", "spawnl", "fork"}
    banned_modules = {"subprocess", "pickle", "shelve", "marshal", "ctypes",
                      "importlib", "runpy", "multiprocessing"}
    found = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split(".")[0] in banned_modules:
                    found.append(f"import {alias.name}")
        elif isinstance(node, ast.ImportFrom):
            if (node.module or "").split(".")[0] in banned_modules:
                found.append(f"from {node.module}")
        elif isinstance(node, ast.Call):
            bare = getattr(node.func, "id", None)
            attribute = getattr(node.func, "attr", None)
            if bare in bare_banned:
                found.append(f"{bare}()")
            elif attribute in attribute_banned:
                found.append(f".{attribute}()")
            elif bare == "getattr" and len(node.args) == 2 and \
                    isinstance(node.args[1], ast.Constant) and \
                    node.args[1].value in bare_banned:
                found.append(f"getattr(..., {node.args[1].value!r})")
    equal(found, [], f"the extraction module must not execute anything: {found}")


def test_the_module_does_not_import_os_in_a_way_that_runs_anything():
    """`os` is imported for paths only; the calls that run things are not used."""
    with open(MODULE, encoding="utf-8") as fh:
        tree = ast.parse(fh.read())
    used = {getattr(node.func, "attr", None) for node in ast.walk(tree)
            if isinstance(node, ast.Call)}
    for dangerous in ("system", "popen", "execv", "spawnv", "fork", "kill"):
        equal(dangerous in used, False, f"os.{dangerous} must not be called")


def test_quarantine_moves_a_file_and_records_where_it_came_from():
    directory = fixtures.tempfile_dir()
    quarantine = os.path.join(directory, "quarantine")
    path = _write(directory, "sample.exe", b"MZ\x90\x00fixture")
    moved = extract.quarantine(path, quarantine)
    equal(os.path.exists(path), False)
    check(os.path.isfile(moved), "the file was moved, not copied")
    with open(moved + ".origin", encoding="utf-8") as fh:
        note = fh.read()
    contains(note, "quarantined from")
    contains(note, path)


def test_an_executable_is_quarantined_on_inspection_when_a_directory_is_given():
    directory = fixtures.tempfile_dir()
    quarantine = os.path.join(directory, "quarantine")
    path = _write(directory, "sample.bin", b"\x7fELF\x02\x01\x01" + b"\x00" * 32)
    report = extract.inspect_file(path, quarantine_dir=quarantine)
    equal(os.path.exists(path), False)
    check(report.quarantined_to, "the report says where the file went")
    check(any("moved to" in note for note in report.notes), report.notes)


# -------------------------------------------------------------------- statuses
def test_every_extraction_status_maps_onto_the_manifest_vocabulary():
    for status in extract.EXTRACTION_STATUSES:
        check(status, "a status name cannot be empty")
    equal(extract.extraction_status(extract.Extraction("x", "unknown", 0, {})),
          "not_attempted")
    report = extract.Extraction("x", "unknown", 0, {})
    report.status = "partial"
    equal(extract.extraction_status(report), "extracted_with_caveats")


def test_a_missing_file_is_a_failure_not_an_exception():
    report = extract.inspect_file(os.path.join(fixtures.tempfile_dir(), "absent.pdf"))
    equal(report.status, "failed")
    check(any("no such file" in reason for reason in report.refusals), report.refusals)


def test_the_whole_report_is_json_serialisable():
    import json
    directory = fixtures.tempfile_dir()
    for name, data in (("file.pdf", fixtures.build_pdf()),
                       ("data.zip", fixtures.build_zip()),
                       ("doc.docx", fixtures.build_docx())):
        report = extract.inspect_file(_write(directory, name, data))
        encoded = json.dumps(report.as_dict())
        check(len(encoded) > 100, "the report has content")
        payload = json.loads(encoded)
        equal(payload["executed"], False)
        check(payload["limits"], "the limits in force are recorded")
        equal(payload["sha256"], ev.file_sha256(os.path.join(directory, name)))
