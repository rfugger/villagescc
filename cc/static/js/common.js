/* JS functions available on every page. */

function init_instruction_input() {
	/* Allow search boxes to give instructions that disappear when selected. */
	$('.instruction_input').each(function(index) {
		var orig_text = $(this).val()
		$(this).focus(function() {
			if ($(this).val() == orig_text) {
				$(this).val('');
			}
		}).blur(function() {
			if ($(this).val() == '') {
				$(this).val(orig_text);
			}
		});
	});
}

function init_feed_items() {
	/* Make feed item container divs clickable links. */
	$('.feed_item').click(function() {
		window.location = $(this).attr('href');
	}).hover(function() {
		$(this).addClass('hover')
	}, function() {
		$(this).removeClass('hover')
	});
}	