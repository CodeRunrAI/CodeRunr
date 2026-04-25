import asyncio

from sqlalchemy import select

from db.session import AsyncSessionLocal, SyncSessionLocal
from db.models.language import Language


LANGUAGES = [
    {
        "id": 1,
        "name": "C",
        "version": "GCC 13.3.0",
        "source_file": "main.c",
        "compile_cmd": "gcc -o main main.c -lm",
        "run_cmd": "./main",
    },
    {
        "id": 2,
        "name": "C++",
        "version": "GCC 13.3.0",
        "source_file": "main.cpp",
        "compile_cmd": "g++ -o main main.cpp -std=c++17",
        "run_cmd": "./main",
    },
    {
        "id": 3,
        "name": "Python",
        "version": "3.12.3",
        "source_file": "main.py",
        "compile_cmd": "python3 -m py_compile main.py",
        "run_cmd": "python3 main.py",
    },
    {
        "id": 4,
        "name": "JavaScript",
        "version": "Node.js 18.19.1",
        "source_file": "main.js",
        "compile_cmd": None,
        "run_cmd": "node main.js",
    },
    {
        "id": 5,
        "name": "TypeScript",
        "version": "5.7.3",
        "source_file": "main.ts",
        "compile_cmd": "tsc main.ts --typeRoots $NODE_PATH/@types --types node",
        "run_cmd": "node main.js",
    },
    {
        "id": 6,
        "name": "Go",
        "version": "1.22.2",
        "source_file": "main.go",
        "compile_cmd": "go build -o main main.go",
        "run_cmd": "./main",
    },
    {
        "id": 7,
        "name": "Rust",
        "version": "1.75.0",
        "source_file": "main.rs",
        "compile_cmd": "rustc -o main main.rs",
        "run_cmd": "./main",
    },
    {
        "id": 8,
        "name": "Java",
        "version": "OpenJDK 21.0.5",
        "source_file": "Main.java",
        "compile_cmd": "javac Main.java",
        "run_cmd": "java Main",
    },
]


async def seed_languages_async():
    async with AsyncSessionLocal() as db:
        existing = await db.execute(select(Language.name))
        existing_names = set(existing.scalars().all())

        added = 0
        for lang in LANGUAGES:
            if lang["name"] in existing_names:
                print(f"  ⏭  {lang['name']} (already exists)")
                continue

            db.add(Language(**lang))
            added += 1
            print(f"  ✓  {lang['name']}")

        await db.commit()
        print(f"\nSeeded {added} language(s), skipped {len(LANGUAGES) - added}.")


def seed_languages_sync() -> None:
    """Synchronous variant — safe to call from Lambda regardless of event-loop state."""
    with SyncSessionLocal() as db:
        existing = db.execute(select(Language.name))
        existing_names = set(existing.scalars().all())

        added = 0
        for lang in LANGUAGES:
            if lang["name"] in existing_names:
                print(f"  ⏭  {lang['name']} (already exists)")
                continue

            db.add(Language(**lang))
            added += 1
            print(f"  ✓  {lang['name']}")

        db.commit()
        print(f"\nSeeded {added} language(s), skipped {len(LANGUAGES) - added}.")


if __name__ == "__main__":
    print("Seeding languages...\n")
    asyncio.run(seed_languages_async())
