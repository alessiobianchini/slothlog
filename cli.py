import argparse
import csv
from datetime import datetime
from pathlib import Path
import sys

import cluster
import db
import git_inspector
import parser


def format_table(headers: list[str], rows: list[list[str]]) -> str:
    if not rows:
        return "No entries found."
    widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(str(cell)))

    header_line = " | ".join(h.ljust(widths[i]) for i, h in enumerate(headers))
    separator = "-+-".join("-" * widths[i] for i in range(len(headers)))
    data_lines = [
        " | ".join(str(cell).ljust(widths[i]) for i, cell in enumerate(row))
        for row in rows
    ]
    return "\n".join([header_line, separator] + data_lines)


def handle_repos(args):
    if args.repo_action == "add":
        repo = db.add_repo(args.path, name=args.name)
        print(f"Added repo: {repo['name']} ({repo['path']}) [ID: {repo['id']}]")
    elif args.repo_action == "list":
        repos = db.list_repos()
        if not repos:
            print("No active repositories configured. Add one with 'cli.py repos add <path>'.")
            return
        rows = [[r["id"], r["name"], r["path"]] for r in repos]
        print(format_table(["ID", "Name", "Path"], rows))
    elif args.repo_action == "remove":
        ok = db.remove_repo(args.id)
        if ok:
            print(f"Removed repository {args.id}")
        else:
            print(f"Repository {args.id} not found.")


def handle_scan(args):
    target_date = args.date or datetime.now().strftime("%Y-%m-%d")
    repos = db.list_repos()
    if not repos:
        print("No active repositories configured. Run 'cli.py repos add <path>' first.")
        return

    all_slots = []
    print(f"Scanning {len(repos)} repositories for date: {target_date}...")

    for repo in repos:
        repo_path = repo["path"]
        repo_name = repo["name"]
        author = args.author or git_inspector.get_default_author(repo_path)
        commits = git_inspector.inspect_repo(repo_path, target_date=target_date, author=author)
        if not commits:
            continue

        clusters = cluster.cluster_commits(commits)
        for c in clusters:
            messages = [commit["message"] for commit in c["commits"]]
            summary = parser.synthesize_summary(c["ticket_id"], messages)

            slot_data = {
                "date": target_date,
                "repo_path": repo_path,
                "repo_name": repo_name,
                "ticket_id": c["ticket_id"],
                "hours": c["hours"],
                "summary": summary,
                "raw_commits": messages,
            }

            if args.save:
                saved = db.save_timeslot(slot_data)
                all_slots.append(saved)
            else:
                all_slots.append(slot_data)

    if not all_slots:
        print(f"No commits found for {target_date}.")
        return

    rows = [
        [s["date"], s["repo_name"], s["ticket_id"], f"{s['hours']:.2f}h", s["summary"]]
        for s in all_slots
    ]
    print("\nGenerated Timesheet:")
    print(format_table(["Date", "Repo", "Ticket", "Hours", "Summary"], rows))
    print(f"\nTotal Hours: {sum(s['hours'] for s in all_slots):.2f}h")


def handle_export(args):
    target_date = args.date or datetime.now().strftime("%Y-%m-%d")
    slots = db.get_timeslots(target_date)
    out_path = Path(args.output or f"timesheet_{target_date}.csv")

    with open(out_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Date", "Repo", "Ticket", "Hours", "Summary"])
        for s in slots:
            writer.writerow([
                s["date"],
                s.get("repo_name", ""),
                s["ticket_id"],
                f"{s['hours']:.2f}",
                s.get("summary", ""),
            ])

    print(f"Exported {len(slots)} timeslots for {target_date} to {out_path}")


def main():
    db.init_db()

    top_parser = argparse.ArgumentParser(
        prog="slothlog",
        description="SlothLog: AI-powered developer timesheet and commit clustering tool"
    )
    subparsers = top_parser.add_subparsers(dest="command", required=True)

    # Subcommand: repos
    repos_parser = subparsers.add_parser("repos", help="Manage tracked git repositories")
    repos_sub = repos_parser.add_subparsers(dest="repo_action", required=True)

    add_parser = repos_sub.add_parser("add", help="Add a git repository to track")
    add_parser.add_argument("path", help="Local filesystem path to git repository")
    add_parser.add_argument("--name", help="Optional friendly repository name")
    add_parser.set_defaults(func=handle_repos)

    list_parser = repos_sub.add_parser("list", help="List all tracked git repositories")
    list_parser.set_defaults(func=handle_repos)

    remove_parser = repos_sub.add_parser("remove", help="Remove a tracked repository by ID")
    remove_parser.add_argument("id", help="Repository ID")
    remove_parser.set_defaults(func=handle_repos)

    # Subcommand: scan
    scan_parser = subparsers.add_parser("scan", help="Scan tracked repos, cluster commits, and generate timeslots")
    scan_parser.add_argument("--date", help="Date in YYYY-MM-DD format (default: today)")
    scan_parser.add_argument("--author", help="Author name or email to filter commits (default: git config user)")
    scan_parser.add_argument("--save", action="store_true", default=True, help="Save generated timeslots to database")
    scan_parser.set_defaults(func=handle_scan)

    # Subcommand: export
    export_parser = subparsers.add_parser("export", help="Export timeslots to CSV")
    export_parser.add_argument("--date", help="Date in YYYY-MM-DD format (default: today)")
    export_parser.add_argument("-o", "--output", help="Output CSV filepath")
    export_parser.set_defaults(func=handle_export)

    args = top_parser.parse_args()
    if hasattr(args, "func"):
        args.func(args)
    else:
        top_parser.print_help()


if __name__ == "__main__":
    main()
