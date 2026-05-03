"""命令行 seed 工具: 把 data/seed/*.yaml 灌入数据库.

用法:
    python -m app.db.seed_tcm
    python -m app.db.seed_tcm --file data/seed/anticoagulant_tcm.yaml
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from app.core.logging import get_logger
from app.db.init_db import init_db
from app.db.session import SessionLocal
from app.services.tcm_seed_loader import load_yaml

logger = get_logger(__name__)

DEFAULT_SEED_FILE = Path("data/seed/anticoagulant_tcm.yaml")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Seed TCM-Drug interactions from YAML")
    parser.add_argument(
        "--file",
        type=Path,
        default=DEFAULT_SEED_FILE,
        help=f"YAML 文件路径 (默认 {DEFAULT_SEED_FILE})",
    )
    parser.add_argument(
        "--no-init",
        action="store_true",
        help="跳过 init_db (假设表已建好)",
    )
    args = parser.parse_args(argv)

    yaml_path: Path = args.file
    if not yaml_path.exists():
        logger.error("seed file not found", path=str(yaml_path))
        print(f"❌ 找不到 seed 文件: {yaml_path}", file=sys.stderr)
        return 1

    if not args.no_init:
        init_db()
        print("✅ 表结构已就绪")

    with SessionLocal() as session:
        stats = load_yaml(session, yaml_path)

    print(
        f"✅ Seed 完成: {stats['interactions']} 条互作, "
        f"{stats['evidences']} 条证据 "
        f"(skipped {stats['skipped']}, failed {stats['failed']})"
    )
    return 0 if stats["failed"] == 0 else 2


if __name__ == "__main__":
    sys.exit(main())
