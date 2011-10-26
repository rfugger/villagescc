-- Extra SQL to execute after syncdb creates this app's tables.

-- Create text search column and index.
alter table feed_feeditem add column tsearch tsvector;
create index ts_index on feed_feeditem using gin(tsearch);