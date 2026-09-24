"""FR-T-2: build a stg_events-shaped table with known, planted properties.

The BigQuery sandbox is not reachable from a coding agent, so a SQL change would
otherwise be unverifiable. This generator writes a small, seeded event log with
the same columns and types as flood_it.stg_events, containing:

  * a one-day logging outage (players vanish, per-player behaviour does not),
  * passive-only days (os_update with no user_engagement),
  * exact duplicate rows,
  * placeholder countries.

Output: tests/_simulated/stg_events.parquet plus planted_facts.json.
Nothing here is part of the analysis path, and no number it produces may ever be
reported as a finding: the data is invented.
"""
import json                                                             # write the planted-facts file
import numpy as np                                                      # random numbers and array building
import pandas as pd                                                     # tables
from pathlib import Path                                                # paths that work on every operating system

RANDOM_STATE = 42                                                       # NFR-R-3: one seed, reproducible output
FIRST_DAY = pd.Timestamp("2018-06-12")                                  # same start as the real export
DAYS_OF_DATA = 114                                                      # same length as the real export
N_PLAYERS = 2000                                                        # enough for stable statistics, small enough to stay fast
OUTAGE_DAY_OFFSET = 70                                                  # the day whose events are partly lost
OUTAGE_LOST_SHARE = 0.75                                                # share of that day's active players whose events disappear
DUPLICATE_SHARE = 0.005                                                 # share of rows copied verbatim
PLACEHOLDER_COUNTRY_SHARE = 0.08                                        # share of players with an obfuscated country
PASSIVE_DAY_SHARE = 0.15                                                # share of players that get a passive-only day
COUNTRY_NAMES = ["United States", "India", "Brazil", "United Kingdom", "Germany", "France",
                 "Canada", "Mexico", "Japan", "Australia", "Spain", "Italy"]   # readable country list
COUNTRY_WEIGHTS = [0.30, 0.16, 0.10, 0.08, 0.07, 0.06, 0.05, 0.05, 0.05, 0.03, 0.03, 0.02]  # how common each one is
LANGUAGES = ["en-us", "en-gb", "pt-br", "de-de", "fr-fr", "es-es", "ja-jp", "hi-in"]   # device languages
APP_VERSIONS = ["1.4.0", "1.4.1", "1.5.0"]                              # game versions
EVENT_ORDER = ["user_engagement", "level_start_quickplay", "level_end_quickplay", "level_complete_quickplay",
               "level_reset_quickplay", "post_score", "spend_virtual_currency", "ad_reward",
               "challenge_a_friend", "completed_5_levels", "use_extra_steps", "screen_view"]   # events emitted on an active day
OUT_DIR = Path(__file__).resolve().parent / "_simulated"                # where the parquet lands

rng = np.random.default_rng(RANDOM_STATE)                               # the single random generator
OUT_DIR.mkdir(parents=True, exist_ok=True)                              # create the output folder if needed
last_day_offset = DAYS_OF_DATA - 1                                      # offset of the final day of data

join_offsets = np.concatenate([                                         # when each player first engages
    rng.integers(0, 7, size=300),                                       # 300 players inside week 1 -> is_new_player = FALSE
    rng.integers(7, last_day_offset - 6, size=N_PLAYERS - 400),         # the bulk, all with a full week of follow-up
    rng.integers(last_day_offset - 6, last_day_offset + 1, size=100),   # 100 late joiners -> right-censored out of player_features
])
rng.shuffle(join_offsets)                                               # mix them so player ids are not ordered by cohort
quality = rng.beta(2.0, 5.0, size=N_PLAYERS)                            # per-player engagement quality, right-skewed like real players
platforms = np.where(rng.random(N_PLAYERS) < 0.70, "ANDROID", "IOS")    # platform mix
real_countries = rng.choice(COUNTRY_NAMES, size=N_PLAYERS, p=COUNTRY_WEIGHTS)   # the country a player would report
countries = np.where(rng.random(N_PLAYERS) < PLACEHOLDER_COUNTRY_SHARE, "(unknown)", real_countries)   # obfuscation looks like this after sql/06
languages = rng.choice(LANGUAGES, size=N_PLAYERS)                       # device language
versions = rng.choice(APP_VERSIONS, size=N_PLAYERS)                     # app version
player_ids = np.array([f"sim{index:06d}" for index in range(N_PLAYERS)])   # stable, readable player ids

active_pairs = []                                                       # flat list of (player index, day offset) to generate events for
for index in range(N_PLAYERS):                                          # one loop, one player per iteration
    join_offset = int(join_offsets[index])                              # this player's joining day
    horizon = last_day_offset - join_offset                             # how many days of follow-up they have
    day_numbers = np.arange(1, horizon + 1)                             # candidate return days (day 0 is always active)
    return_base = 0.12 + 0.55 * quality[index]                          # keener players return more often
    decay = 2.5 + 11.0 * quality[index]                                 # keener players stay longer
    probabilities = return_base * np.exp(-day_numbers / decay)          # daily probability of being active
    returns = day_numbers[rng.random(horizon) < probabilities]          # the days they actually came back
    active_pairs.append((index, join_offset))                           # the joining day itself
    active_pairs.extend((index, join_offset + int(day)) for day in returns)   # every return day

rows_player = []                                                        # collected player id arrays, one per active player-day
rows_minute = []                                                        # collected minute-of-day arrays
rows_offset = []                                                        # collected day-offset arrays
rows_name = []                                                          # collected event-name arrays
for index, day_offset in active_pairs:                                  # one loop, one active player-day per iteration
    player_quality = quality[index]                                     # how engaged this player is
    engagements = 1 + rng.poisson(1.0 + 3.0 * player_quality)           # user_engagement events (always at least one)
    starts = rng.poisson(1.0 + 6.0 * player_quality)                    # levels started
    completes = rng.binomial(starts, 0.55) if starts > 0 else 0         # levels completed is a subset of levels started
    ends = starts                                                       # every started level also ends
    resets = rng.binomial(starts, 0.20) if starts > 0 else 0            # some levels are reset
    scores = rng.binomial(completes, 0.60) if completes > 0 else 0      # scores are posted after completing
    spends = rng.poisson(0.4 * player_quality)                          # virtual currency spends
    ads = rng.poisson(0.7 * player_quality)                             # rewarded ads
    friends = int(rng.random() < 0.20 * player_quality)                 # friend challenges are rare
    milestone = 1 if completes >= 5 else 0                              # completed_5_levels only fires after five completions
    extras = rng.poisson(0.3 * player_quality)                          # extra-step purchases
    screens = 1 + rng.poisson(1.5)                                      # screen views, a non-game event
    counts = [engagements, starts, ends, completes, resets, scores, spends, ads, friends, milestone, extras, screens]
    names = np.repeat(EVENT_ORDER, counts)                              # one array holding every event name for this day
    rng.shuffle(names)                                                  # order within the day carries no meaning
    n_events = names.size                                               # how many events this day holds
    n_sessions = int(min(3, 1 + rng.poisson(1.5 * player_quality)))     # one to three sessions, keener players have more
    session_of_event = np.sort(rng.integers(0, n_sessions, size=n_events))   # assign events to sessions, keeping them contiguous
    first_start = int(rng.integers(0, 1440 - n_sessions * 90))          # first session start, leaving room for the others
    session_starts = first_start + np.arange(n_sessions) * 90 + rng.integers(0, 20, size=n_sessions)   # 90-minute blocks keep gaps above 30 minutes
    within_gaps = rng.uniform(0.2, 3.0, size=n_events)                  # minutes between consecutive events inside a session
    is_session_start = np.concatenate(([True], session_of_event[1:] != session_of_event[:-1]))   # first event of each session
    within_gaps[is_session_start] = 0.0                                 # a session's first event sits exactly on its block start
    offsets_in_session = pd.Series(within_gaps).groupby(session_of_event).cumsum().to_numpy()   # running minutes inside each session
    offsets_in_session = np.minimum(offsets_in_session, 45.0)           # cap a session at 45 minutes so blocks never overlap
    minutes = session_starts[session_of_event] + offsets_in_session     # minute-of-day for every event
    rows_player.append(np.repeat(player_ids[index], n_events))          # same player for all of them
    rows_minute.append(minutes)                                         # times
    rows_offset.append(np.repeat(day_offset, n_events))                 # the day
    rows_name.append(names)                                             # the event names

events = pd.DataFrame({                                                 # assemble one row per event
    "player_index": np.repeat([index for index, _ in active_pairs], [array.size for array in rows_name]),   # index back into the player arrays
    "player_id": np.concatenate(rows_player),                           # player id
    "day_offset": np.concatenate(rows_offset),                          # day offset from the first day of data
    "minute_of_day": np.concatenate(rows_minute),                       # minute inside that day
    "event_name": np.concatenate(rows_name),                            # what happened
})
passive_players = rng.choice(N_PLAYERS, size=int(N_PLAYERS * PASSIVE_DAY_SHARE), replace=False)   # players that get a passive-only day
passive_offsets = np.clip(join_offsets[passive_players] + rng.integers(2, 20, size=passive_players.size), 0, last_day_offset)   # a day near their join
passive = pd.DataFrame({                                                # passive-only rows: no user_engagement that day
    "player_index": passive_players,                                    # index back into the player arrays
    "player_id": player_ids[passive_players],                           # player id
    "day_offset": passive_offsets,                                      # the passive day
    "minute_of_day": rng.uniform(0, 1439, size=passive_players.size),   # any time of day
    "event_name": "os_update",                                          # an automatic event nobody triggered
})
already_active = set(zip(events["player_index"], events["day_offset"]))    # player-days that already hold real engagement
keep_passive = [pair not in already_active for pair in zip(passive["player_index"], passive["day_offset"])]   # drop collisions with active days
passive = passive[keep_passive]                                         # keep only genuinely passive days
events = pd.concat([events, passive], ignore_index=True)                # add them to the log

outage_pool = events[events["day_offset"] == OUTAGE_DAY_OFFSET]         # everything recorded on the outage day
outage_players = outage_pool["player_index"].unique()                   # the players active that day
lost_players = rng.choice(outage_players, size=int(len(outage_players) * OUTAGE_LOST_SHARE), replace=False)   # whose events are lost
lost_mask = (events["day_offset"] == OUTAGE_DAY_OFFSET) & (events["player_index"].isin(lost_players))   # rows the pipeline dropped
events = events[~lost_mask].reset_index(drop=True)                      # drop them: DAU falls, per-player ratios do not

events["event_date"] = (FIRST_DAY + pd.to_timedelta(events["day_offset"], unit="D")).dt.date    # reporting-time-zone date
events["event_ts"] = (FIRST_DAY + pd.to_timedelta(events["day_offset"], unit="D")
                      + pd.to_timedelta(events["minute_of_day"] * 60.0, unit="s")).dt.floor("s")   # exact timestamp, whole seconds
events["platform"] = platforms[events["player_index"].to_numpy()]       # platform from the player table
events["operating_system"] = np.where(events["platform"] == "IOS", "IOS", "ANDROID")    # operating system mirrors platform here
events["device_language"] = languages[events["player_index"].to_numpy()]   # device language
events["country"] = countries[events["player_index"].to_numpy()]        # country, including '(unknown)' placeholders
events["app_version"] = versions[events["player_index"].to_numpy()]     # app version
engagement_time = rng.integers(1000, 600000, size=len(events))          # milliseconds of engagement
events["engagement_time_msec"] = np.where(events["event_name"] == "user_engagement", engagement_time, np.nan)   # only on user_engagement

duplicates = events.sample(frac=DUPLICATE_SHARE, random_state=RANDOM_STATE)   # exact copies of real rows
events = pd.concat([events, duplicates], ignore_index=True)             # duplicate rows exist in the real export too
events = events.sort_values(["player_id", "event_ts"]).reset_index(drop=True)   # stable order

stg = events[["player_id", "event_date", "event_ts", "event_name", "platform", "operating_system",
              "device_language", "country", "app_version", "engagement_time_msec"]].copy()   # exactly the stg_events columns
stg["engagement_time_msec"] = stg["engagement_time_msec"].astype("Int64")    # nullable integer, like BigQuery's INT64
stg.to_parquet(OUT_DIR / "stg_events.parquet", index=False)             # the table the DuckDB harness reads

facts = {                                                               # what was planted, for the harness to assert against
    "random_state": RANDOM_STATE,                                       # the seed
    "first_day": str(FIRST_DAY.date()),                                 # first day of data
    "days_of_data": DAYS_OF_DATA,                                       # length of the window
    "players": int(N_PLAYERS),                                          # how many players exist
    "events": int(len(stg)),                                            # how many rows were written
    "outage_date": str((FIRST_DAY + pd.to_timedelta(OUTAGE_DAY_OFFSET, unit="D")).date()),   # the planted outage
    "outage_players_lost": int(len(lost_players)),                      # how many players vanished that day
    "duplicate_rows": int(len(duplicates)),                             # exact duplicates added
    "passive_only_player_days": int(len(passive)),                      # passive-only days added
    "placeholder_country_share": round(float((stg["country"] == "(unknown)").mean()), 4),   # obfuscated share
}
(OUT_DIR / "planted_facts.json").write_text(json.dumps(facts, indent=2), encoding="utf-8")   # save the facts
print("wrote", OUT_DIR / "stg_events.parquet")                          # where the table went
print(json.dumps(facts, indent=2))                                      # show the planted facts
