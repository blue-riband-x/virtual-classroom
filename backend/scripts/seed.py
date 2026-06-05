"""种子数据脚本"""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import text

async def seed():
    url = 'mysql+aiomysql://root:root@localhost:3306/virtual_classroom?charset=utf8mb4'
    engine = create_async_engine(url, echo=False)
    maker = async_sessionmaker(engine)

    async with maker() as session:
        # 测试用户
        await session.execute(text("""
            INSERT INTO users (username, email, password_hash, nickname, xp, level, streak, total_learning_hours, xp_to_next_level)
            VALUES ('dev', 'dev@test.com', '123456', '学习小达人', 2850, 15, 7, 42.5, 3000)
        """))
        print("✅ 用户数据插入成功")

        # 学习记录
        records = [
            (1, 'Python基础语法', '2026-05-10', 45, 92, 68),
            (1, '数据结构-二叉树', '2026-05-09', 60, 85, 72),
            (1, '算法复杂度分析', '2026-05-08', 40, 78, 48),
        ]
        for uid, topic, date, dur, score, xp in records:
            await session.execute(text(
                "INSERT INTO learning_records (user_id, topic, date, duration, score, xp_earned) VALUES (:uid, :topic, :date, :dur, :score, :xp)"
            ), {"uid": uid, "topic": topic, "date": date, "dur": dur, "score": score, "xp": xp})
        print("✅ 学习记录插入成功")

        # 成就
        for name, desc, icon in [
            ('首课完成', '完成第一节课', '🎯'),
            ('百课达成', '完成100节课', '💯'),
            ('提问达人', '累计提问50次', '❓'),
        ]:
            await session.execute(text(
                "INSERT INTO achievements (name, description, icon, xp_reward, `condition`) VALUES (:name, :desc, :icon, :xp, :cond)"
            ), {"name": name, "desc": desc, "icon": icon, "xp": 50, "cond": '{"type":"count","value":1}'})
        print("✅ 成就数据插入成功")

        await session.commit()

    # 验证
    async with maker() as session:
        r = await session.execute(text("SELECT COUNT(*) FROM users"))
        print(f"📊 users: {r.scalar()} rows")
        r = await session.execute(text("SELECT COUNT(*) FROM learning_records"))
        print(f"📊 learning_records: {r.scalar()} rows")
        r = await session.execute(text("SELECT COUNT(*) FROM achievements"))
        print(f"📊 achievements: {r.scalar()} rows")

    await engine.dispose()
    print("✅ 种子数据全部完成")

asyncio.run(seed())
