CREATE TABLE IF NOT EXISTS anime
(
    anime_id INTEGER PRIMARY KEY AUTOINCREMENT
);

CREATE TABLE IF NOT EXISTS anime_name
(
    anime_name_id INTEGER PRIMARY KEY AUTOINCREMENT,
    is_primary BOOLEAN NOT NULL,
    anime_id INTEGER REFERENCES anime (anime_id),
    anime_name TEXT NOT NULL,
    normalized_anime_name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS character_name
(
    character_name_id INTEGER PRIMARY KEY AUTOINCREMENT,
    anime_id INTEGER REFERENCES anime (anime_id),
    character_name TEXT NOT NULL,
    normalized_character_name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS unmatched_character
(
    unmatched_character_id INTEGER PRIMARY KEY AUTOINCREMENT,
    character_name TEXT NOT NULL,
    normalized_character_name TEXT NOT NULL,
    anime_name TEXT NOT NULL,
    normalized_anime_name TEXT NOT NULL,
    reference_id INTEGER NULL
);

CREATE TABLE IF NOT EXISTS match_result
(
    match_result_id INTEGER PRIMARY KEY AUTOINCREMENT,
    unmatched_character_id INTEGER REFERENCES unmatched_character (unmatched_character_id),
    matched_character_name_id REFERENCES character_name (character_name_id)
);

CREATE INDEX IF NOT EXISTS anime_name_ix_is_primary ON anime_name (is_primary);
CREATE INDEX IF NOT EXISTS anime_name_ix_anime_id ON anime_name (anime_id, anime_name, normalized_anime_name);
CREATE INDEX IF NOT EXISTS anime_name_ix_normalized_anime_name ON anime_name (normalized_anime_name, anime_name, anime_id);
CREATE INDEX IF NOT EXISTS character_name_ix_anime_id ON character_name (anime_id, character_name, normalized_character_name);
CREATE INDEX IF NOT EXISTS character_name_ix_normalized_character_name ON character_name (normalized_character_name, character_name, anime_id);
CREATE INDEX IF NOT EXISTS unmatched_character_ix_normalized_name ON unmatched_character (normalized_character_name, normalized_anime_name, character_name, anime_name);
CREATE INDEX IF NOT EXISTS unmatched_character_ix_normalized_name ON unmatched_character (normalized_anime_name, normalized_character_name, character_name, anime_name);

DELETE FROM anime_name;
DELETE FROM character_name;
DELETE FROM anime;
DELETE FROM unmatched_character;
DELETE FROM match_result;
