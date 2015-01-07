create table content
(
    id integer primary key,             -- content ID

    md5 varchar,                        -- md5 of the URL
    url varchar,                        -- original URL
    title varchar,                      -- page title
    archive varcher,                    -- name of archive to which content belongs
    images integer default 0,           -- number of images

    is_sponsored boolean,               -- whether content is sponsored
    is_partner boolean,                 -- whether content is from partener
    partner varchar,                    -- name of sponsor/partner

    created timestamp,                  -- creation timestamp
    updated timestamp                   -- update timestamp
);
