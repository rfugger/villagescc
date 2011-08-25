var geocoder;
var map;
var marker;

// Maps google geocode results to display names.
var address_type_map = {  
	country: 'country',
	administrative_area_level_1: 'state',
	locality: 'city',
	neighborhood: 'neighborhood',
	sublocality: 'neighborhood',
	route: 'neighborhood',
	intersection: 'neighborhood'
};

// Prefer reverse-geocoded addresses that have components listed
// earlier here.
var address_type_preference_order = {
	neighborhood: 1,
	sublocality: 2,
	intersection: 3,
	street_address: 4,
	route: 5,
	locality: 6,
	administrative_area_level_1: 7,
	country: 8
};

function initialize_geo(initial_lat, initial_lng) {
	var initial_pos = true;
	geocoder = new google.maps.Geocoder();
	if (initial_lat == '' || initial_lng == '') {
		// Default to Vancouver.
		initial_lat = 49.248523;
		initial_lng = -123.108;
		initial_pos = false;
	}
	var initial_center = new google.maps.LatLng(initial_lat, initial_lng);
	var map_options = {
		zoom: 11,
		center: initial_center,
		mapTypeControl: false,
		mapTypeId: google.maps.MapTypeId.ROADMAP
	};
	map = new google.maps.Map($('#map_canvas')[0], map_options);
	marker = new google.maps.Marker({
			map: map, 
			position: initial_center,
			draggable: true,
			title: "Drag me",
			visible: initial_pos
		});
	center_map(initial_center);
	if (initial_pos) {
		geocode_position(initial_center);
	}

	google.maps.event.addListener(marker, 'dragend', function() {
			geocode_position(marker.getPosition());
		});
   	google.maps.event.addListener(map, 'click', function(event) {
			marker.setPosition(event.latLng);
			geocode_position(event.latLng);
		});
}

function get_browser_location() {
	// Access browser html5 geolocation API.
	if (navigator.geolocation) {
		navigator.geolocation.getCurrentPosition(function(position) {
				var latlng = new google.maps.LatLng(position.coords.latitude, 
													position.coords.longitude);
				center_map(latlng);
				marker.setPosition(latlng);
				geocode_position(latlng);
			}, 
			function(msg) {},  // Error function (do nothing).
			{timeout: 3000});
	}
}

function geocode_callback(f) {
	/* Wrap f in some geocode error handling. */
	return function(results, status) {
		if (status == google.maps.GeocoderStatus.OK) {
			f(results);
			marker.setVisible(true);
		} else { 
			marker.setVisible(false);
		}
	};
}

function loc_search(query) {
	geocoder.geocode({address: query}, geocode_callback(function(results) {
				center_map(results[0].geometry.location);
				update_form(results[0].address_components, 
							results[0].geometry.location);
			}));
}


function center_map(location) {
	map.setCenter(location);
	marker.setPosition(location);
}

function update_form(address, location) {
	// Clear form fields.
	for (var key in address_type_map) {
		$('#id_' + address_type_map[key]).val('');
	}
	$('#id_point').val('');

	// Set form fields with new values.
	for (var i = 0; i < address.length; i++) {
		component = address[i];
		if (component.types) {
			var address_type = component.types[0];
			var target_type = address_type_map[address_type];
			if (!target_type) {
				continue;
			}
			// Abbreviate state.
			var component_name;
			if (target_type == 'state' && component.short_name ) {
				component_name = component.short_name;
			} else {
				component_name = component.long_name;
			}
			$('#id_' + target_type).val(component_name);
		}
	}
	// Point gets set in Well Known Text (WKT) for GeoDjango.
	$('#id_point').val(latlng_to_wkt(location.lat(), location.lng()));
}

function geocode_position(position) {
	geocoder.geocode({latLng: position}, geocode_callback(function(results) {
				var address = best_address(results);
				update_form(address.address_components, 
							results[0].geometry.location);
			}));
}

function best_address(results) {
	/* Prefer general over specific for neighbourhood. */
	var best = results[0];
	for (var i = 1; i < results.length; i++) {
		if (is_better_address(results[i], best)) {
			best = results[i];
		}
	}
	return best;
}

function is_better_address(addr1, addr2) {
	/* Is addr1 better than addr2 according to type preference order? */
	if (!(addr1.types[0] in address_type_preference_order)) {
		return false;
	}
	if (!(addr2.types[0] in address_type_preference_order)) {
		return true;
	}	
	return address_type_preference_order[addr1.types[0]] <
		address_type_preference_order[addr2.types[0]];
}

function latlng_to_wkt(lat, lng) {
	/* Creates Well-Known Text for GeoDjango.
	 * eg, 'POINT(-142.51152, 49.209830)'
	 */
	return 'POINT(' + lng + ' ' + lat + ')';
}
	
function wkt_to_latlng(text) {
	/* Takes Well-Known Text point and returns an array with lat, lng. */
	re = /POINT\s*\((-?\d+\.\d+)\s+(-?\d+\.\d+)\)/;
	match = re.exec(text);
	if (match) {
		return [match[2], match[1]];
	}
	return null;
}