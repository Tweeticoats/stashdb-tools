create table sites_stashdb
(
    id          varchar(255) not null
        primary key,
    stash_id varchar(255)
);
create table performer_stashdb
(
    id int unsigned primary key,
    stash_id varchar(255)
);

create table tags_stashdb
(
    id    int unsigned primary key,
    stash_id varchar(255)
);
