-- Extra SQL to execute after syncdb creates this app's tables.

-- Extra parens required around compound index expression
-- See http://archives.postgresql.org/pgsql-general/2011-08/msg00616.php
create index profile_text_search_index on profile_profile using gin((
	   setweight(to_tsvector('english', name), 'A') ||
	   setweight(to_tsvector('english', description), 'B')
));
