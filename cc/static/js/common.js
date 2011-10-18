/* JS functions available on every page. */

function init_instruction_input() {
	/* Allow search boxes to give instructions that disappear when selected. */
	$('.instruction_input').each(function(index) {
		// Input instruction goes in 'help' attribute.
		var orig_text = $(this).attr('help');

		// Only apply help instruction if blank.
		if ($(this).val() == '')
			$(this).val(orig_text);

		$(this).focus(function() {  // Remove instruction on focus.
			if ($(this).val() == orig_text) {
				$(this).val('');
			}
		}).blur(function() {  // Restore on blur if nothing entered.
			if ($(this).val() == '') {
				$(this).val(orig_text);
			}
		});
		
		// Remove help on form submit.
		input = $(this);  // Inside form submit handler, $(this) = form.
		input.closest('form').submit(function() {
			if (input.val() == orig_text) {
				input.val('');
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

function init_feed_filter_form() {
	/* Make form submit on change. */
	$('.feed_filter_form #id_radius').change(function() {
		$(this).closest('form').submit();
	});
	$('.feed_filter_form #id_trusted').change(function() {
		$(this).closest('form').submit();
	});
	$('.feed_filter_form #id_clear').click(function() {
		$('.feed_filter_form #id_q').val('');
		$(this).closest('form').submit();
	});
}

