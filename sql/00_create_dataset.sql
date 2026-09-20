-- 00_create_dataset.sql
-- Purpose: create your own dataset (a folder for views) in the SAME location as the public data (US).
CREATE SCHEMA IF NOT EXISTS flood_it              -- "schema" and "dataset" mean the same thing in BigQuery
OPTIONS (location = 'US');                        -- must be US, because the public Flood-It data lives in US
