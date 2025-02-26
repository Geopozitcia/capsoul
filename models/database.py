import aiosqlite

DB_NAME = "CAPSOUL.db"

async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                phone TEXT,
                user_name TEXT UNIQUE NOT NULL,
                aim_of_project TEXT,
                past_experience TEXT,
                team_exist TEXT,
                date_of_project TEXT,
                design_preferences TEXT,
                meeting_date TEXT,
                planning_file TEXT
            )
        ''')
        await db.commit()

if __name__ == "__main__":
    import asyncio
    asyncio.run(init_db())