-- Extra SQL to execute after syncdb creates this app's tables.

create index post_search_index on post_post using gin(
	   to_tsvector('english', text)
);
