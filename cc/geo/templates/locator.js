var initial_lat = '{{ initial_lat }}';
var initial_lng = '{{ initial_lng }}';

$(document).ready(function() {
	// Search bar updates map.
	$('#loc_search_form').submit(function() {
		query = $('#loc_search').val();
		loc_search(query);
		return false;
	});	

	// Clear instruction when clicking search input.
	$('#loc_search').focus(function() {
		$(this).val('');
	});

	// Init map, etc.
	initialize_geo(initial_lat, initial_lng);
	get_browser_location();
});
