/*
    Google Maps Code
*/

'use strict';

// Hold representation of Google Map and InfoWindow
var map, largeInfoWindow;

// Array to hold marker locations:
var markers = [];

function initMap() {
    // Constructor creates a new map - only center and zoom are required
    // Need to specify where to load map (using #map here)
    // Need to also specify coordinates - center & zoom values (0-22)
    var mapDiv = $('#map');  // jQuery returns collection of 0 or 1
    var wixom = {lat: 42.524970, lng: -83.536211};  // Use zoom of 13
    largeInfoWindow = new google.maps.InfoWindow();
    // Allow adjusting map boundaries as necessary if things outside initial map area
    // This captures SW and NE corners of viewport
    var bounds = new google.maps.LatLngBounds();

    // Custom icons
    // Style the marker icons
    var defaultIcon = makeMarkerIcon('0091ff');
    // This will be a "highlighted location" marker color for when user mouses
    // over the marker
    var highlightedIcon = makeMarkerIcon('ffff24');

    map = new google.maps.Map(mapDiv[0], {
        center: wixom,
        zoom: 13
    });

    for (var i = 0; i < pointsOfInterest.length; i++) {
        // Get the position from the location array.
        var position = pointsOfInterest[i].location;
        var title = pointsOfInterest[i].title;
        // Create a marker per location, and put into markers array.
        var marker = new google.maps.Marker({
            map: map,
            position: position,
            title: title,
            animation: google.maps.Animation.DROP,
            icon: defaultIcon,
            // id: i
            id: pointsOfInterest[i].place
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
            var innerHTML = '<div><strong>' + marker.title + '</strong>';
            // For each potential information element from places details, need to check
            // if it's present - it may or may not be
            /* Use marker.title instead
            if (place.name) {
                innerHTML += '<strong>' + place.name + '</strong>';
            }
            */
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
            // Add a photo place holder
            innerHTML += '<br><br><img src="" alt="Checking for Flickr Photos..." id="flickr-photo">';
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

// Query Flickr for place phots
function getPhotos(title) {
    // Photo Search API Endpoint:
    // https://api.flickr.com/services/rest/?method=flickr.photos.search&api_key=<key>&text=<title>&format=json&nojsoncallback=1
    // var encodedTitle = encodeURI(title);
    var photoQueryURL = 'https://api.flickr.com/services/rest/?' + $.param({
        'method': 'flickr.photos.search',
        'api_key': flickrAPIKey,
        'text': title,
        // 'tags': title,
        'format': 'json',
        'nojsoncallback': '1'
    });
    // Photo Retrieval:
    // m = 240px max, n = 320px max
    // https://farm{farm-id}.staticflickr.com/{server-id}/{id}_{secret}_m.jpg'
    // Could use template literals, but no IE support...

    // AJAX Query:
    $.ajax(photoQueryURL)
        .done(function(data) {
            var flickrPhoto = $('#flickr-photo');
            console.log('Sucessful query.');
            console.log(data);
            // Check status code - both good and bad
            // Check for results - handle 0, 1, and multiple
            // If get 0 results, try requerying without last word
            // e.g., Wixom Habitat instead of Wixom Habitat Vista
            if (Number(data.photos.total) === 0 && title.split(' ').length > 2) {
                console.log('In if check of getPhotos...');
                var newTitle = title.slice(0, title.lastIndexOf(' '));
                getPhotos(newTitle);
            }
            // Update photo div appropriately
            switch (Number(data.photos.total)) {
                case 0:
                    flickrPhoto.attr('alt', 'No Flickr Photos found.  :-(');
                    break;
                case 1:
                    var photoArray = data.photos.photo;
                    flickrPhoto.attr({
                        alt: 'Flickr Photo',
                        src: 'https://farm' + photoArray[0].farm + '.staticflickr.com/' + photoArray[0].server + '/' + photoArray[0].id + '_' + photoArray[0].secret + '_m.jpg'
                    });
                    // Fall through to add next/prev buttons
                    // break;
                // 2 or more
                default:
                    console.log('Made it to default case - ' + data.photos.total + ' Flickr photos available.');
            }
        })
        .fail(function(err) {
            console.log('Failed query.');
            console.log(err);
            // Update photo div appropriately (Flickr unavailable...)
        });

    // Update photo div src to load first photo
    // If more than 1 add prev/next buttons
    /* Notes:
    Example JSON Response:
    { "photos": { "page": 1, "pages": 1, "perpage": 100, "total": 50,
        "photo": [
          { "id": "11876531065", "owner": "88636811@N06", "secret": "b23b77d7a1", "server": "7390", "farm": 8, "title": "cold", "ispublic": 1, "isfriend": 0, "isfamily": 0 },
          (...),
          { "id": "92265376", "owner": "39832458@N00", "secret": "3e07aa0323", "server": 13, "farm": 1, "title": "habitat5", "ispublic": 1, "isfriend": 0, "isfamily": 0 }
        ] },
     "stat": "ok" }
    */
}
