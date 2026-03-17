#!/usr/bin/env python3
"""
Import specific files WITH git history from a locally-available ref.

Requirements:
    git-filter-repo==2.47.0

Usage:
    python ./Tools/_Greenshift/portContentFiles.py <remote>/<branch> file1.txt file2.txt ...
    python ./Tools/_Greenshift/portContentFiles.py <remote>/<branch> --paths-from-file ./Tools/_Greenshift/ported_file_lists/<file.txt>
"""

import argparse
import subprocess
import sys
import tempfile
import shutil
from pathlib import Path


def run(cmd, cwd=None, check=True, capture=False):
    """Run and print a shell command"""
    print(f"  $ {' '.join(cmd)}" + (f"  (in {cwd})" if cwd else ""))
    result = subprocess.run(
        cmd,
        cwd=cwd,
        check=check,
        text=True,
        capture_output=capture,
    )
    return result

def get_repo_root():
    """Get the root of the current git repo"""
    result = run(["git", "rev-parse", "--show-toplevel"], capture=True)
    return result.stdout.strip()

def ref_exists(ref):
    """Check if a git ref exists locally"""
    result = run(["git", "rev-parse", "--verify", ref], check=False, capture=True)
    return result.returncode == 0

def main():
    parser = argparse.ArgumentParser(
        description="Import git history for specific files from a local ref"
    )
    parser.add_argument(
        "ref",
        help='Any locally-available ref (e.g. "wizden/master", a local branch, a tag, a SHA)',
    )
    parser.add_argument(
        "files",
        nargs="*",
        help="Files to import history for",
    )
    parser.add_argument(
        "--paths-from-file",
        help="Read file paths from a text file (one per line)",
    )
    parser.add_argument(
        "--branch",
        default=None,
        help="Local branch name to store the imported history on before merging "
             "If not set, merges directly into the current branch",
    )
    parser.add_argument(
        "--no-merge",
        action="store_true",
        help="Create a local branch with the filtered history but don't merge it",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be done without executing",
    )

    args = parser.parse_args()

    ref = args.ref

    # Collect file list
    files = []
    if args.paths_from_file:
        p = Path(args.paths_from_file)
        if not p.exists():
            print(f"Error: paths file '{p}' not found.", file=sys.stderr)
            sys.exit(1)
        with open(p) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    files.append(line)
    elif args.files:
        files = args.files

    if not files:
        parser.error("No files specified. Pass them as arguments or use --paths-from-file")
    
    for file in files:
        if "_" not in file:
            print("Error: This script is not meant to port changes made by forks to wizden upstream files, that must be done manually. All ported files must exist in a _ForkName sub directory.")
            sys.exit(1)
    # Verify ref exists locally
    if not ref_exists(ref):
        print(f"Error: ref '{ref}' not found locally. Run 'git fetch <remote> <branch>' first", file=sys.stderr)
        sys.exit(1)

    repo_root = get_repo_root()

    print(f"\nRef:     {ref}")
    print(f"Repo:    {repo_root}")
    print(f"Files:   {len(files)}")
    for fp in files:
        print(f"  - {fp}")

    if args.dry_run:
        print("\n[dry-run] Would clone locally, filter, fetch, and merge. Exiting.")
        sys.exit(0)

    # Clone locally
    tmpdir = tempfile.mkdtemp(prefix="git-filter-import-")
    clone_path = Path(tmpdir) / "filtered-clone"
    print(f"\n[1/4] Local clone into temp dir...")
    print(f"       {clone_path}")

    # Resolve the ref to a commit so we can check it out in the clone
    resolved = run(
        ["git", "rev-parse", ref], capture=True
    ).stdout.strip()

    run(["git", "clone", "--no-checkout", repo_root, str(clone_path)])
    run(["git", "checkout", resolved, "-b", "_import_work"], cwd=str(clone_path))

    # Filter
    print(f"\n[2/4] Filtering clone down to {len(files)} file(s)...")
    filter_cmd = ["git", "filter-repo", "--force"]
    for fp in files:
        filter_cmd.extend(["--path", fp])
    run(filter_cmd, cwd=str(clone_path))

    # Sanity check: see how many commits survived
    result = run(
        ["git", "rev-list", "--count", "HEAD"],
        cwd=str(clone_path),
        capture=True,
    )
    commit_count = result.stdout.strip()
    print(f"       {commit_count} commits remain after filtering.")

    if int(commit_count) == 0:
        print("\nWarning: No commits survived filtering. The specified files may not "
              "exist on that ref.", file=sys.stderr)
        shutil.rmtree(tmpdir)
        sys.exit(1)

    # Add filtered clone as a temporary remote and fetch
    tmp_remote = "_filtered_import_tmp"
    print(f"\n[3/4] Fetching filtered history into current repo...")
    run(["git", "remote", "remove", tmp_remote], check=False)
    run(["git", "remote", "add", tmp_remote, str(clone_path)])
    run(["git", "fetch", tmp_remote, "_import_work"])

    # Merge or create branch
    fetched_ref = f"{tmp_remote}/_import_work"

    if args.no_merge:
        local_branch = args.branch or f"imported/{ref}"
        print(f"\n[4/4] Creating local branch '{local_branch}' (no merge)...")
        run(["git", "branch", local_branch, fetched_ref])
        print(f"\n  Done. Inspect with:  git log {local_branch}")
    elif args.branch:
        print(f"\n[4/4] Creating branch '{args.branch}' and merging filtered history...")
        run(["git", "checkout", "-b", args.branch])
        run(["git", "merge", fetched_ref, "--allow-unrelated-histories",
             "-m", f"Import file history from {ref}"])
        print(f"\n  Done. You're now on branch '{args.branch}'.")
    else:
        print(f"\n[4/4] Merging filtered history into current branch...")
        run(["git", "merge", fetched_ref, "--allow-unrelated-histories",
             "-m", f"Import file history from {ref}"])
        print("\n  Done. Filtered history merged into current branch.")

    # Cleanup
    run(["git", "remote", "remove", tmp_remote])
    shutil.rmtree(tmpdir)
    print(f"  Cleaned up temp dir and remote.\n")

if __name__ == "__main__":
    main()