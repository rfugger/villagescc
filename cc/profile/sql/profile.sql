-- Extra SQL to execute after syncdb creates this app's tables.

create index search_index on profile_profile using gin(
	   setweight(to_tsvector('english', name), 'A') ||
	   setweight(to_tsvector('english', description), 'B')
);
