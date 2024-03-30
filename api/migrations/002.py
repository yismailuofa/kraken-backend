# This migration changes all the Status Todo into To Do in the database.

from api.database import getDb

if __name__ == "__main__":
    db = getDb()

    # if the status is Todo, change it to To Do
    db.tasks.update_many(
        {"status": "Todo"},
        {"$set": {"status": "To Do"}},
    )

    db.tasks.update_many(
        {"qaTask.status": "Todo"},
        {"$set": {"qaTask.status": "To Do"}},
    )

    db.milestones.update_many(
        {"status": "Todo"},
        {"$set": {"status": "To Do"}},
    )

    print("Migration completed")
