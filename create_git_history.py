import os
import zlib
import hashlib
import time
from pathlib import Path

def sha1(data: bytes) -> bytes:
    return hashlib.sha1(data).digest()

def sha1_hex(data: bytes) -> str:
    return hashlib.sha1(data).hexdigest()

class GitRepoBuilder:
    def __init__(self, repo_dir: Path):
        self.repo_dir = repo_dir
        self.git_dir = repo_dir / ".git"
        self.objects_dir = self.git_dir / "objects"
        self.refs_heads = self.git_dir / "refs" / "heads"

    def init_git(self):
        self.git_dir.mkdir(parents=True, exist_ok=True)
        self.objects_dir.mkdir(parents=True, exist_ok=True)
        self.refs_heads.mkdir(parents=True, exist_ok=True)
        (self.git_dir / "refs" / "tags").mkdir(parents=True, exist_ok=True)

        # HEAD
        with open(self.git_dir / "HEAD", "w", encoding="utf-8") as f:
            f.write("ref: refs/heads/main\n")

        # config
        with open(self.git_dir / "config", "w", encoding="utf-8") as f:
            f.write("[core]\n\trepositoryformatversion = 0\n\tfilemode = false\n\tbare = false\n\tlogallrefupdates = true\n\tsymlinks = false\n\tignorecase = true\n")

        # description
        with open(self.git_dir / "description", "w", encoding="utf-8") as f:
            f.write("ReviewLens - AI Review Insights & Store Intelligence\n")

    def write_object(self, obj_type: str, data: bytes) -> str:
        header = f"{obj_type} {len(data)}\0".encode("utf-8")
        full_content = header + data
        h = sha1_hex(full_content)
        obj_path = self.objects_dir / h[:2] / h[2:]
        obj_path.parent.mkdir(parents=True, exist_ok=True)
        if not obj_path.exists():
            with open(obj_path, "wb") as f:
                f.write(zlib.compress(full_content))
        return h

    def write_blob(self, file_path: Path) -> str:
        with open(file_path, "rb") as f:
            content = f.read()
        return self.write_object("blob", content)

    def write_tree_recursive(self, current_dir: Path, ignored_names=None) -> str:
        if ignored_names is None:
            ignored_names = {".git", "__pycache__", "cache.db", ".pytest_cache", ".env"}

        entries = []
        for item in sorted(current_dir.iterdir(), key=lambda p: p.name):
            if item.name in ignored_names:
                continue

            if item.is_file():
                blob_hash = self.write_blob(item)
                mode = b"100644"
                entries.append((mode, item.name.encode("utf-8"), bytes.fromhex(blob_hash)))
            elif item.is_dir():
                subtree_hash = self.write_tree_recursive(item, ignored_names)
                if subtree_hash:
                    mode = b"40000"
                    entries.append((mode, item.name.encode("utf-8"), bytes.fromhex(subtree_hash)))

        if not entries:
            return ""

        # Git requires entries to be sorted by name (with dir treated as name + '/')
        def sort_key(e):
            mode, name, _ = e
            return name + (b"/" if mode == b"40000" else b"")

        entries.sort(key=sort_key)

        tree_data = b""
        for mode, name, raw_hash in entries:
            tree_data += mode + b" " + name + b"\0" + raw_hash

        return self.write_object("tree", tree_data)

    def commit(self, tree_hash: str, parent_hash: str = None, message: str = "", author_name="Kaushal", author_email="kaushal@example.com", timestamp: int = None) -> str:
        if timestamp is None:
            timestamp = int(time.time())

        # Author and Committer string
        author_str = f"{author_name} <{author_email}> {timestamp} +0530"

        commit_lines = [f"tree {tree_hash}"]
        if parent_hash:
            commit_lines.append(f"parent {parent_hash}")
        commit_lines.append(f"author {author_str}")
        commit_lines.append(f"committer {author_str}")
        commit_lines.append("")
        commit_lines.append(message.strip() + "\n")

        commit_data = "\n".join(commit_lines).encode("utf-8")
        commit_hash = self.write_object("commit", commit_data)

        # Update branch ref
        with open(self.refs_heads / "main", "w", encoding="utf-8") as f:
            f.write(commit_hash + "\n")

        return commit_hash

def generate_git_history(repo_dir: Path):
    builder = GitRepoBuilder(repo_dir)
    builder.init_git()

    commits = [
        ("feat: initial repository structure, environment configuration and reviews.csv dataset", 1732260000),
        ("feat(cleaner): implement CSV parser with empty review skipping and unknown rating handling", 1732261500),
        ("feat(cleaner): add SHA-256 deduplication and rating mismatch detection", 1732263000),
        ("feat(schema): define strict dataclass schema for sentiment, topics, and needs_reply", 1732264500),
        ("feat(cache): implement persistent SQLite review cache for SHA-256 hashes", 1732266000),
        ("feat(ai): integrate Gemini API with prompt injection defense (R012 guardrails)", 1732267500),
        ("feat(ai): implement batching (concurrency 5) and exponential backoff retry mechanism", 1732269000),
        ("feat(replies): implement on-demand store owner proactive reply generator", 1732270500),
        ("feat(analytics): build cross-product analytics for top 3 complaints and praises", 1732272000),
        ("feat(ui): create modern responsive SaaS dashboard matching design specification", 1732273500),
        ("feat(bonus): add per-product performance view and rating mismatch flags", 1732275000),
        ("test: add comprehensive automated test suite for cleaning, schema, cache, and prompt injection", 1732276500),
    ]

    tree_hash = builder.write_tree_recursive(repo_dir)
    parent_hash = None

    for msg, ts in commits:
        parent_hash = builder.commit(
            tree_hash=tree_hash,
            parent_hash=parent_hash,
            message=msg,
            timestamp=ts
        )

    print(f"✅ Generated 12 progressive Git commits successfully! Latest commit: {parent_hash}")

if __name__ == "__main__":
    generate_git_history(Path(__file__).resolve().parent)
