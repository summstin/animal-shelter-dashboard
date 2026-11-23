# Animal Shelter Dashboard (CS-499 Capstone Artifact)

Python dashboard (PyMongo, Dash, MongoDB) for browsing and filtering Austin Animal Center shelter outcomes for Grazioso Salvare, originally built in CS-340 in Winter 2026. This branch contains the Databases enhancement, built on top of the original CS-340 code.

## What this branch adds

- **No hardcoded credentials.** The connection (host, port, user, password, auth database, database, collection) is read from environment variables. The data layer pings the server on startup and fails fast if MongoDB is down.
- **Compound index** `rescue_filter_idx` on `breed`, `sex_upon_outcome`, `age_upon_outcome_in_weeks`, created on startup. It covers the equality, `$in` and range fields that every rescue filter uses.
- **Rescue queries moved into the data layer.** The Water, Mountain/Wilderness and Disaster/Tracking profiles now live in `RESCUE_PROFILES` and `rescue_query()` instead of being built inside the dashboard callback.
- **Input validation.** Create and update only accept an allowlist of known fields, with numeric type checks. Update accepts plain fields or `$set` only (no operators), and refuses an empty query. Delete refuses an empty query so it cannot wipe the collection.
- **Better error handling.** Bare `except` and `print` replaced with specific `PyMongoError` handling and logging.
- **Richer `read()`.** Supports projection, limit and sort, and leaves `_id` out by default, so the dashboard no longer has to drop it from every DataFrame.
- **Server-side aggregation.** `breed_counts()` uses a MongoDB `$match` / `$group` / `$sort` pipeline to build the breed pie chart. The dashboard falls back to counting the table's rows only when the user has typed column filters.
- **Update fix.** The original `update()` passed values straight to MongoDB, so they needed a manual `$set`. The enhanced version wraps them correctly.

## Branches

- `main`: original CS-340 code
- `databases`: this branch (Enhancement Three)

## Files

- `CRUD_Python_Module.py`: `AnimalShelter` data layer (CRUD, rescue queries, aggregation, index)
- `ProjectTwoDashboard.ipynb`: the Dash dashboard
- `aac_shelter_outcomes.csv`: source dataset
- `Grazioso Salvare Logo.png`: dashboard logo

## Run it

1. Install and start MongoDB, then import `aac_shelter_outcomes.csv` into the `animals` collection of the `aac` database (for example with MongoDB Compass).
2. Create a virtual environment and install `pymongo`, `dash`, `jupyter-dash`, `dash-leaflet`, `plotly`, `pandas`, `numpy`, `matplotlib` and `jupyter`.
3. If your MongoDB requires authentication, set `MONGO_USER` and `MONGO_PASS`. Optional settings: `MONGO_HOST` (default `localhost`), `MONGO_PORT` (`27017`), `MONGO_AUTH_DB` (`admin`), `MONGO_DB` (`aac`), `MONGO_COL` (`animals`). With no user and password set, it connects without credentials.
4. Open `ProjectTwoDashboard.ipynb` in Jupyter and run all cells.
