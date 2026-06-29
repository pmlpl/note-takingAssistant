"""查看当前数据库的表结构和样本数据"""
import asyncio
import sys

sys.path.insert(0, ".")
from sqlalchemy import text
from app.core.database import engine


async def inspect_db():
    print(f"[info] 连接数据库: {engine.url}")

    async with engine.connect() as conn:
        print("\n====== [1] 所有表 ======")
        rows = await conn.execute(text("SHOW TABLES"))
        tables = [r[0] for r in rows]
        print(f"共 {len(tables)} 张表: {tables}")

        for t in tables:
            print(f"\n{'=' * 60}")
            print(f"[表] {t}")
            print("=" * 60)

            # 字段
            cols = await conn.execute(text(f"DESCRIBE {t}"))
            print(
                f"{'字段名':<22}{'类型':<20}{'NULL':<6}{'KEY':<6}{'默认值':<14}Extra"
            )
            print("-" * 90)
            for c in cols:
                name = c[0]
                typ = str(c[1])
                nul = str(c[2])
                key = str(c[3]) if c[3] else ""
                default = str(c[4]) if c[4] is not None else "NULL"
                extra = str(c[5]) if c[5] else ""
                print(f"{name:<22}{typ:<20}{nul:<6}{key:<6}{default:<14}{extra}")

            # 行数
            cnt = await conn.scalar(text(f"SELECT COUNT(*) FROM {t}"))
            print(f"\n  行数: {cnt}")

            # 样本（前 3 行）
            try:
                sample = await conn.execute(text(f"SELECT * FROM {t} LIMIT 3"))
                col_names = list(sample.keys())
                print(f"  列: {col_names}")
                for i, row in enumerate(sample):
                    values = []
                    for v in row:
                        if v is None:
                            values.append("NULL")
                        else:
                            s = str(v)
                            if len(s) > 60:
                                s = s[:60] + "..."
                            values.append(s)
                    print(f"   #{i+1}: {values}")
            except Exception as e:
                print(f"   (读取样本失败: {e})")


if __name__ == "__main__":
    asyncio.run(inspect_db())
