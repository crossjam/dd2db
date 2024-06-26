--- artists
CREATE TABLE IF NOT EXISTS artist (
    id              integer NOT NULL,
    name            text NOT NULL,
    realname        text,
    profile         text,

    data_quality    text
);

CREATE TABLE IF NOT EXISTS artist_url (
    id              SERIAL,
    artist_id       integer NOT NULL,
    url             text NOT NULL
);

CREATE TABLE IF NOT EXISTS artist_namevariation (
    id              SERIAL,
    artist_id       integer NOT NULL,
    name            text NOT NULL
);

CREATE TABLE IF NOT EXISTS artist_alias (
    artist_id       integer NOT NULL,
    alias_name      text NOT NULL,
    alias_artist_id integer
);

CREATE TABLE IF NOT EXISTS artist_image (
    artist_id       integer NOT NULL,
    type            text,
    width           integer,
    height          integer
);

CREATE TABLE IF NOT EXISTS group_member (
    group_artist_id     integer NOT NULL,
    member_artist_id    integer NOT NULL,
    member_name         text NOT NULL
);

--- labels
CREATE TABLE IF NOT EXISTS label (
    id              integer NOT NULL,
    name            text NOT NULL,
    contact_info    text,
    profile         text,

    parent_id       integer,
    parent_name     text,

    data_quality    text
);

CREATE TABLE IF NOT EXISTS label_url (
    id              SERIAL,
    label_id        integer NOT NULL,
    url             text NOT NULL
);

CREATE TABLE IF NOT EXISTS label_image (
    label_id        integer NOT NULL,
    type            text,
    width           integer,
    height          integer
);

--- masters
CREATE TABLE IF NOT EXISTS master (
    id              integer NOT NULL,
    title           text NOT NULL,
    year            integer,
    main_release    integer NOT NULL,
    data_quality    text
);

CREATE TABLE IF NOT EXISTS master_artist (
    id              SERIAL,
    master_id       integer NOT NULL,
    artist_id       integer NOT NULL,
    artist_name     text,
    anv             text,
    position        integer,
    join_string     text,
    role            text
);

CREATE TABLE IF NOT EXISTS master_video (
    id              SERIAL,
    master_id       integer NOT NULL,
    duration        integer,
    title           text,
    description     text,
    uri             text
);

CREATE TABLE IF NOT EXISTS master_genre (
    id              SERIAL,
    master_id       integer NOT NULL,
    genre           text
);

CREATE TABLE IF NOT EXISTS master_style (
    id              SERIAL,
    master_id       integer NOT NULL,
    style           text
);

CREATE TABLE IF NOT EXISTS master_image (
    master_id       integer NOT NULL,
    type            text,
    width           integer,
    height          integer
);

--- releases
CREATE TABLE IF NOT EXISTS release (
    id              integer NOT NULL,
    title           text NOT NULL,
    released        text,
    country         text,
    notes           text,
    data_quality    text,
    main            integer,
    master_id       integer,
    status          text
);

CREATE TABLE IF NOT EXISTS release_artist (
    id              SERIAL,
    release_id      integer NOT NULL,
    artist_id       integer NOT NULL,
    artist_name     text,
    extra           integer NOT NULL,
    anv             text,
    position        integer,
    join_string     text,
    role            text,
    tracks          text
);

CREATE TABLE IF NOT EXISTS release_label (
    id              SERIAL,
    release_id      integer NOT NULL,
    label_id        integer,
    label_name      text NOT NULL,
    catno           text
);

CREATE TABLE IF NOT EXISTS release_genre (
    id              SERIAL,
    release_id      integer NOT NULL,
    genre           text
);

CREATE TABLE IF NOT EXISTS release_style (
    release_id      integer NOT NULL,
    style           text
);

CREATE TABLE IF NOT EXISTS release_format (
    id              SERIAL,
    release_id      integer NOT NULL,
    name            text,
    qty             NUMERIC, -- There's 1 example e.g. 8262262,File,1000000000000000000000000000000000000000000000000000000000000001,32 kbps,MP3; Album; Mono
    text_string     text,
    descriptions    text
);

CREATE TABLE IF NOT EXISTS release_track (
    id              SERIAL,
    release_id      integer NOT NULL,
    sequence        integer NOT NULL,
    position        text,
    parent          integer,
    title           text,
    duration        text,
    track_id        integer
);

CREATE TABLE IF NOT EXISTS release_track_artist (
    id              SERIAL,
    track_id        integer,
    release_id      integer NOT NULL,
    track_sequence  integer NOT NULL,
    artist_id       integer NOT NULL,
    artist_name     text,
    extra           boolean NOT NULL,
    anv             text,
    position        integer,
    join_string     text,
    role            text,
    tracks          text
);

CREATE TABLE IF NOT EXISTS release_identifier (
    id              SERIAL,
    release_id      integer NOT NULL,
    description     text,
    type            text,
    value           text
);

CREATE TABLE IF NOT EXISTS release_video (
    id              SERIAL,
    release_id      integer NOT NULL,
    duration        integer,
    title           text,
    description     text,
    uri             text
);

CREATE TABLE IF NOT EXISTS release_company (
    id                  SERIAL,
    release_id          integer NOT NULL,
    company_id          integer NOT NULL,
    company_name        text NOT NULL,
    entity_type         text,
    entity_type_name    text,
    uri                 text
); 

CREATE TABLE IF NOT EXISTS release_image (
    release_id      integer NOT NULL,
    type            text,
    width           integer,
    height          integer
);

