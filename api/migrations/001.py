# This migration backfills createdAt field to Milestones

from api.database import getDb
from api.schemas import now

if __name__ == "__main__":
    db = getDb()

    db.milestones.update_many(
        {},
        {"$set": {"createdAt": now()}},
    )

    print("Migration completed")
