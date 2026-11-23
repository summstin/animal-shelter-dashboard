"""CRUD and query operations for the AAC animals collection in MongoDB."""
import logging
import os

from pymongo import MongoClient
from pymongo.errors import PyMongoError

log = logging.getLogger(__name__)

INDEX_NAME = "rescue_filter_idx"

ALLOWED_FIELDS = {
    "rec_num", "age_upon_outcome", "animal_id", "animal_type", "breed",
    "color", "date_of_birth", "datetime", "monthyear", "name",
    "outcome_subtype", "outcome_type", "sex_upon_outcome",
    "location_lat", "location_long", "age_upon_outcome_in_weeks",
}
NUMERIC_FIELDS = ("location_lat", "location_long", "age_upon_outcome_in_weeks")

# profile: (breeds, sex, min age in weeks, max age in weeks)
RESCUE_PROFILES = {
    "water": (["Labrador Retriever Mix", "Chesapeake Bay Retriever", "Newfoundland"],
              "Intact Female", 26, 156),
    "mountain": (["German Shepherd", "Alaskan Malamute", "Old English Sheepdog",
                  "Siberian Husky", "Rottweiler"], "Intact Male", 26, 156),
    "disaster": (["Doberman Pinscher", "German Shepherd", "Golden Retriever",
                  "Bloodhound", "Rottweiler"], "Intact Male", 20, 300),
}


class AnimalShelter:
    """Data layer for the Grazioso Salvare dashboard."""

    def __init__(self):
        # Settings come from the environment. With no MONGO_USER/MONGO_PASS
        # it connects without credentials, as your local setup does today.
        opts = {"serverSelectionTimeoutMS": 5000}
        user, pw = os.getenv("MONGO_USER"), os.getenv("MONGO_PASS")
        if user and pw:
            opts.update(username=user, password=pw,
                        authSource=os.getenv("MONGO_AUTH_DB", "admin"))
        self.client = MongoClient(os.getenv("MONGO_HOST", "localhost"),
                                  int(os.getenv("MONGO_PORT", "27017")), **opts)
        self.client.admin.command("ping")  # fail fast if the server is down
        self.database = self.client[os.getenv("MONGO_DB", "aac")]
        self.collection = self.database[os.getenv("MONGO_COL", "animals")]
        # Covers the equality, $in and range fields every rescue filter uses.
        self.collection.create_index(
            [("breed", 1), ("sex_upon_outcome", 1), ("age_upon_outcome_in_weeks", 1)],
            name=INDEX_NAME)

    @staticmethod
    def _check(doc):
        """Raise ValueError if doc is not a safe animal document."""
        if not isinstance(doc, dict) or not doc:
            raise ValueError("Document must be a non-empty dict.")
        bad = set(doc) - ALLOWED_FIELDS
        if bad:
            raise ValueError("Unknown field(s): " + ", ".join(sorted(bad)))
        for f in NUMERIC_FIELDS:
            if f in doc and not isinstance(doc[f], (int, float)):
                raise ValueError(f + " must be a number.")

    @staticmethod
    def rescue_query(profile):
        """Return the MongoDB query for a rescue profile; {} means all animals."""
        if profile not in RESCUE_PROFILES:
            return {}
        breeds, sex, lo, hi = RESCUE_PROFILES[profile]
        return {"breed": {"$in": breeds}, "sex_upon_outcome": sex,
                "age_upon_outcome_in_weeks": {"$gte": lo, "$lte": hi}}

    # Create
    def create(self, data):
        try:
            self._check(data)
            self.collection.insert_one(dict(data))
            return True
        except (ValueError, PyMongoError) as e:
            log.error("Create failed: %s", e)
            return False

    # Read
    def read(self, query, projection=None, limit=0, sort=None):
        """Return a list of documents. _id is left out unless a projection asks for it."""
        if not isinstance(query, dict):
            return []
        try:
            cur = self.collection.find(
                query, projection if projection is not None else {"_id": 0}, limit=limit)
            if sort:
                cur = cur.sort(sort)
            return list(cur)
        except PyMongoError as e:
            log.error("Read failed: %s", e)
            return []

    # Update
    def update(self, query, new_values, multiple=False):
        """Set fields on matching documents. Returns the modified count."""
        if not isinstance(query, dict) or not query or not isinstance(new_values, dict) or not new_values:
            log.error("Update needs a non-empty query and non-empty new values.")
            return 0
        try:
            body = new_values.get("$set", new_values)
            if any(k.startswith("$") for k in body):
                raise ValueError("Only plain fields or {'$set': {...}} are allowed.")
            self._check(body)
            run = self.collection.update_many if multiple else self.collection.update_one
            return run(query, {"$set": body}).modified_count
        except (ValueError, PyMongoError) as e:
            log.error("Update failed: %s", e)
            return 0

    # Delete
    def delete(self, query, multiple=False):
        """Delete matching documents. An empty query is refused."""
        if not isinstance(query, dict) or not query:
            log.error("Delete refused: query is empty.")
            return 0
        try:
            run = self.collection.delete_many if multiple else self.collection.delete_one
            return run(query).deleted_count
        except PyMongoError as e:
            log.error("Delete failed: %s", e)
            return 0

    # Aggregation
    def breed_counts(self, query=None, top=10):
        """Count animals per breed in MongoDB. Breeds past the top N become 'Other'."""
        pipeline = [{"$match": query or {}},
                    {"$group": {"_id": "$breed", "count": {"$sum": 1}}},
                    {"$sort": {"count": -1}}]
        try:
            rows = list(self.collection.aggregate(pipeline))
        except PyMongoError as e:
            log.error("Aggregation failed: %s", e)
            return []
        out = [{"breed": r["_id"], "count": r["count"]} for r in rows[:top]]
        rest = sum(r["count"] for r in rows[top:])
        if rest:
            out.append({"breed": "Other", "count": rest})
        return out

    def close(self):
        self.client.close()