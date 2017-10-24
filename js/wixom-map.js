/*
    Google Maps Code
*/

'use strict';

// Hold representation of Google Map
var map;

// Array to hold listing markers:
var markers = [];

// Create placemarkers array to use in multiple functions to have control
// over the number of places that show.
var placeMarkers = [];

function initMap() {
    // Constructor creates a new map - only center and zoom are required
    // Need to specify where to load map (using #map here)
    // Need to also specify coordinates - center & zoom values (0-22)
    var mapDiv = $('#map');  // jQuery returns collection of 0 or 1
    var mapDivNative = document.getElementById('map');
    var wixom = {lat: 42.524970, lng: -83.536211};  // Try 13
    var largeInfoWindow = new google.maps.InfoWindow();
    // Allow adjusting map boundaries as necessary if things outside initial map area
    // This captures SW and NE corners of viewport
    var bounds = new google.maps.LatLngBounds();

    // Custom icons
    // Style the markers - this will be listing marker icon
    var defaultIcon = makeMarkerIcon('0091ff');
    // This will be a "highlighted location" marker color for when user mouses
    // over the marker
    var highlightedIcon = makeMarkerIcon('ffff24');

    map = new google.maps.Map(mapDiv[0], {
        center: wixom,
        zoom: 13
        /*
        // Choose styles or this:
        mapTypeControlOptions: {
            mapTypeIds: ['roadmap', 'satellite', 'hybrid', 'terrain', 'styled_map']
        }
        */
        // Prevent user from changing map type (only if choose styles)
        // mapTypeControl: false
    });

    // Associate the styled map with the MapTypeId and set it to display
    // (Only if choose mapTypeControlOptions)
    /*
    map.mapTypes.set('styled_map', styledMapType);
    map.setMapTypeId('styled_map');
    */

    /*
    // First example showing only a single point:
    var tribeca = {lat: 40.719526, lng: -74.0089934};

    // Create a marker on the map to show a point (Tribeca):
    var marker = new google.maps.Marker({
        // Which coordinates should marker appear at?
        position: tribeca,
        // Which map should marker appear on?
        map: map,
        // Title which appears if hover over marker:
        title: 'First Marker!'
        // Many more options - see API docs
    });
    // InfoWindow's don't open automatically like markers
    var infowindow = new google.maps.InfoWindow({
        content: 'Do you ever feel like an InfoWindow, floating through the wind, ' +
            'ready to start again?'
    });

    // Open InfoWindow when user clicks on marker
    marker.addListener('click', function() {
        infowindow.open(map, marker);
    });
    */

    for (var i = 0; i < pointsOfInterest.length; i++) {
        // Get the position from the location array.
        var position = pointsOfInterest[i].location;
        var title = pointsOfInterest[i].title;
        // Create a marker per location, and put into markers array.
        var marker = new google.maps.Marker({
            // Eliminated this when added showListings()
            // map: map,
            position: position,
            title: title,
            animation: google.maps.Animation.DROP,
            icon: defaultIcon,
            id: i
        });

        // Push the marker to our array of markers.
        markers.push(marker);
        // Create an onclick event to open an infowindow at each marker.
        marker.addListener('click', function() {
            // Clicked marker = this
            // populateInfoWindow is a function below
            populateInfoWindow(this, largeInfoWindow);
        });
        // Two event listeners - one for mouseover, one for mouseout,
        // to change the colors back and forth.
        marker.addListener('mouseover', function() {
            this.setIcon(highlightedIcon);
        });
        marker.addListener('mouseout', function() {
            this.setIcon(defaultIcon);
        });
        // Extend map boundary for each marker - moved to showListings()
        // bounds.extend(markers[i].position);
    }

    // Adjust map to fit all markers - moved to showListings()
    // map.fitBounds(bounds);

    document.getElementById('show-pois').addEventListener('click', showListings);
    // Replaced hideListings with hideMarkers
    // document.getElementById('hide-listings').addEventListener('click', hideListings);
    document.getElementById('hide-pois').addEventListener('click', function() {
        hideMarkers(markers);
    });
}

// This function populates the infowindow when the marker is clicked. We'll only allow
// one infowindow which will open at the marker that is clicked, and populate based
// on that markers position.
function populateInfoWindow(marker, infowindow) {
    // Check to make sure the infowindow is not already opened on this marker.
    if (infowindow.marker != marker) {
        // Clear the infowindow content to give the streetview time to load.
        infowindow.setContent('');
        infowindow.marker = marker;
        /* Removed when added street view functionality
        infowindow.setContent('<div>' + marker.title + '</div>');
        infowindow.open(map, marker);
        */
        // Make sure the marker property is cleared if the infowindow is closed.
        infowindow.addListener('closeclick', function() {
            infowindow.setMarker = null;
        });

        var streetViewService = new google.maps.StreetViewService();
        // Street view data might not have exact match for Lat+Lng, so search within a radius:
        var radius = 50;
        // In case the status is OK, which means the pano was found, compute the
        // position of the streetview image, then calculate the heading, then get a
        // panorama from that and set the options
        function getStreetView(data, status) {
            if (status == google.maps.StreetViewStatus.OK) {
                var nearStreetViewLocation = data.location.latLng;
                // Compute heading (from which direction are you looking at street view)
                // Use location of nearest street view and our marker for this
                var heading = google.maps.geometry.spherical.computeHeading(
                        nearStreetViewLocation, marker.position);
                // Create div with id of pano to reference below
                infowindow.setContent('<div>' + marker.title + '</div><div id="pano"></div>');
                var panoramaOptions = {
                    position: nearStreetViewLocation,
                    pov: {
                        // As computed from above
                        heading: heading,
                        // Looking slightly up at building
                        pitch: 30
                    }
                };
                // Put street view panorama in div with pano id
                var panorama = new google.maps.StreetViewPanorama(
                        document.getElementById('pano'), panoramaOptions);
            } else {
                // If there's no street view data available:
                infowindow.setContent('<div>' + marker.title + '</div>' +
                    '<div>No Street View Found</div>');
            }
        }
        // Use streetview service to get the closest streetview image within
        // 50 meters of the markers position
        streetViewService.getPanoramaByLocation(marker.position, radius, getStreetView);
        // Open the infowindow on the correct marker.
        infowindow.open(map, marker);
    }
}

// This function will loop through the markers array and display them all.
function showListings() {
    var bounds = new google.maps.LatLngBounds();

    // Extend the boundaries of the map for each marker and display the marker
    for (var i = 0; i < markers.length; i++) {
        markers[i].setMap(map);
        bounds.extend(markers[i].position);
    }

    map.fitBounds(bounds);
}

// This function will loop through the listings and hide them all.
// function hideListings() { - renamed to hideMarkers to make more generic
function hideMarkers(markers) {
    for (var i = 0; i < markers.length; i++) {
        markers[i].setMap(null);
    }
}

// This function takes in a COLOR, and then creates a new marker
// icon of that color. The icon will be 21 px wide by 34 high, have an origin
// of 0, 0 and be anchored at 10, 34).
function makeMarkerIcon(markerColor) {
    var markerImage = new google.maps.MarkerImage(
        'http://chart.googleapis.com/chart?chst=d_map_spin&chld=1.15|0|'+ markerColor +
            '|40|_|%E2%80%A2',
        new google.maps.Size(21, 34),
        new google.maps.Point(0, 0),
        new google.maps.Point(10, 34),
        new google.maps.Size(21, 34)
    );

    return markerImage;
}

// This is the PLACE DETAILS search - it's the most detailed so it's only
// executed when a marker is selected, indicating the user wants more
// details about that place.
// Note: It uses placeid to get place details and display in an infowindow above
// user cliked place marker
function getPlacesDetails(marker, infowindow) {
    var service = new google.maps.places.PlacesService(map);
    service.getDetails({
        placeId: marker.id
    }, function(place, status) {
        if (status === google.maps.places.PlacesServiceStatus.OK) {
            // Set the marker property on this infowindow so it isn't created again.
            infowindow.marker = marker;
            var innerHTML = '<div>';
            // For each potential information element from places details, need to check
            // if it's present - it may or may not be
            if (place.name) {
                innerHTML += '<strong>' + place.name + '</strong>';
            }
            if (place.formatted_address) {
                innerHTML += '<br>' + place.formatted_address;
            }
            if (place.formatted_phone_number) {
                innerHTML += '<br>' + place.formatted_phone_number;
            }
            if (place.opening_hours) {
                innerHTML += '<br><br><strong>Hours:</strong><br>' +
                    place.opening_hours.weekday_text[0] + '<br>' +
                    place.opening_hours.weekday_text[1] + '<br>' +
                    place.opening_hours.weekday_text[2] + '<br>' +
                    place.opening_hours.weekday_text[3] + '<br>' +
                    place.opening_hours.weekday_text[4] + '<br>' +
                    place.opening_hours.weekday_text[5] + '<br>' +
                    place.opening_hours.weekday_text[6];
            }
            if (place.photos) {
                innerHTML += '<br><br><img src="' + place.photos[0].getUrl(
                    {maxHeight: 100, maxWidth: 200}) + '">';
            }
            innerHTML += '</div>';
            infowindow.setContent(innerHTML);
            infowindow.open(map, marker);
            // Make sure the marker property is cleared if the infowindow is closed.
            infowindow.addListener('closeclick', function() {
                infowindow.marker = null;
            });
        }
    });
}
