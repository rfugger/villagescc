/* Common JS to be run on every page load. */

$(document).ready(function() {
	// Remove 'Search' text in search box when clicked.
	$('#global_search_input').focus(function() {
		$(this).val('');
	}).blur(function() {
		if ($(this).val() == '') $(this).val('Search')
	});

	// Clicking feed item container div goes to item page.
	$('.feed_item').click(function() {
		window.location = $(this).attr('href');
	}).hover(function() {
		$(this).addClass('hover')
	}, function() {
		$(this).removeClass('hover')
	});
});
