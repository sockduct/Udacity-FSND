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
    // var selectedIcon = makeMarkerIcon('3db73c');

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
            id: pointsOfInterest[i].place
        });

        // Push the marker to our array of markers.
        markers.push(marker);
        // Create an onclick event to open an infowindow at each marker.
        marker.addListener('click', function() {
            // Clicked marker = this
            resetMarkerIcons();
            this.setAnimation(google.maps.Animation.DROP);
            this.setIcon(highlightedIcon);
            getPlacesDetails(this, largeInfoWindow);
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

function resetMarkerIcons() {
    markers.forEach(function (marker) {
        var defaultIcon = makeMarkerIcon('0091ff');
        marker.setIcon(defaultIcon);
    });
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

            // Use jQuery to create new div/DOM element
            var iwcontent = $('<div></div>');
            iwcontent.attr('id', 'outer-iwcontent');
            iwcontent.append('<strong>' + marker.title + '</strong>');
            // For each potential information element from places details, need to check
            // if it's present - it may or may not be
            /* Use marker.title instead
            if (place.name) {
                iwcontent.append('<strong>' + place.name + '</strong>');
            }
            */
            if (place.formatted_address) {
                iwcontent.append('<br>' + place.formatted_address);
            }
            if (place.formatted_phone_number) {
                iwcontent.append('<br>' + place.formatted_phone_number);
            }
            if (place.opening_hours) {
                iwcontent.append('<br><br><strong>Hours:</strong><br>' +
                    place.opening_hours.weekday_text[0] + '<br>' +
                    place.opening_hours.weekday_text[1] + '<br>' +
                    place.opening_hours.weekday_text[2] + '<br>' +
                    place.opening_hours.weekday_text[3] + '<br>' +
                    place.opening_hours.weekday_text[4] + '<br>' +
                    place.opening_hours.weekday_text[5] + '<br>' +
                    place.opening_hours.weekday_text[6]);
            }
            /* Use Flickr photos instead...
            if (place.photos) {
                iwcontent.append('<br><br><img src="' + place.photos[0].getUrl({maxHeight: 100, maxWidth: 200}) + '">');
            }
            */
            // Add a photo place holder
            iwcontent.append('<br><br><img src="" id="flickr-photo" alt="Checking for Flickr Photos..."></img>');
            infowindow.setContent(iwcontent[0]);
            infowindow.open(map, marker);
            // Make sure the marker property is cleared if the infowindow is closed.
            infowindow.addListener('closeclick', function() {
                infowindow.marker = null;
            });

            // First call:
            getPhotos(marker.title, iwcontent, infowindow);

            /* Update photo div appropriately
            switch (data.photos.total) {
                case '-1':
                    iwcontent.find('#flickr-photo').attr('alt', 'Error retrieving Flickr Photo.')
                case '0':
                    iwcontent.find('#flickr-photo').attr('alt', 'No Flickr Photos found - Trying again with more general search...');
            }
            */
        }
    });
}

// Query Flickr for place photos
function getPhotos(title, iwcontent, infowindow) {
    // Photo Search API Endpoint:
    // https://api.flickr.com/services/rest/?method=flickr.photos.search&api_key=<key>&text=<title>&format=json&nojsoncallback=1
    var photoQueryURL = 'https://api.flickr.com/services/rest/?' + $.param({
        'method': 'flickr.photos.search',
        'api_key': flickrAPIKey,
        'text': title,
        // 'tags': title,
        'format': 'json',
        'nojsoncallback': '1'
    });

    // AJAX Query:
    // Consider setting timeout - not sure what default timeout is
    $.ajax(photoQueryURL)
        .done(function(data) {
            console.log('Sucessful query.');
            console.log(data);

            // Check status code - both good and bad
            // Check for results - handle 0, 1, and multiple
            // If get 0 results, try requerying without last word
            // e.g., Wixom Habitat instead of Wixom Habitat Vista
            /*
            if (Number(data.photos.total) === 0 && marker.title.split(' ').length > 2) {
                console.log('In if check of getPhotos...');
                var newTitle = marker.title.slice(0, title.lastIndexOf(' '));
                getPhotos(newTitle, marker, infowindow, iwcontent);
            }
            */

            if (data.stat !== "ok") {
                data.photos.total = "-1";
            }
        })
        .fail(function(errReq, errStat) {
            console.log('Query with status of ' + errStat);
            console.log(errReq);
            // Update photo div appropriately (Flickr unavailable...)
        })
        .always(function(data) {
            // Error handling - if data missing this, then add it:
            // var data = {'photos': {'total': "-1"}};

            installPhotos(data, iwcontent, infowindow);

            if (data.photos.total === '0' && title.split(' ').length > 2) {
                var newTitle = title.slice(0, title.lastIndexOf(' '));
                // Retry with more general title search
                getPhotos(newTitle, iwcontent, infowindow);
            }
        });
}

function installPhotos(data, iwcontent, infowindow) {
    // Update photo div appropriately
    var photoIndex = 0;

    switch (data.photos.total) {
        case '-1':
            console.log('Case -1...');
            iwcontent.find('#flickr-photo').attr('alt', 'Error retrieving Flickr Photo.')
            break;
        case '0':
            console.log('Case 0...');
            iwcontent.find('#flickr-photo').attr('alt', 'No Flickr Photos found - Trying again with more general search...');
            break;
        // Later on for case 1, just want photo and no buttons
        case '1':
            console.log('Case 1...');
        // Later on for case 2+, want photo and forward/back buttons
        default:
            console.log('Made it to default case - ' + data.photos.total + ' Flickr photos available.');

            // Photo Retrieval:
            // m = 240px max, n = 320px max
            // https://farm{farm-id}.staticflickr.com/{server-id}/{id}_{secret}_m.jpg'
            // Could use template literals, but no IE support...
            var photoArray = data.photos.photo;
            iwcontent.find('#flickr-photo').attr({
                'alt': 'Flickr Photo',
                'src': 'https://farm' + photoArray[photoIndex].farm + '.staticflickr.com/' + photoArray[photoIndex].server + '/' + photoArray[photoIndex].id + '_' + photoArray[photoIndex].secret + '_m.jpg'
            });
            iwcontent.append('<br>Source:  Flickr Photo API');
            iwcontent.append('<br><br><button id="prev-photo" type="button" disabled>Previous</button> Flickr Photo <span id="photo-num">' + (photoIndex + 1) + '</span> of ' + data.photos.total + ' <button id="next-photo" type="button">Next</button>');
    }
    $('#prev-photo').on('click', function() {
        if (photoIndex > 0) {
            photoIndex--;

            iwcontent.find('#flickr-photo').attr('src', 'https://farm' + photoArray[photoIndex].farm + '.staticflickr.com/' + photoArray[photoIndex].server + '/' + photoArray[photoIndex].id + '_' + photoArray[photoIndex].secret + '_m.jpg');
            iwcontent.find('#photo-num').text(photoIndex + 1);
            if (photoIndex + 1 === Number(data.photos.total) - 1) {
                console.log('Enabling next button...');
                iwcontent.find('#next-photo').removeAttr('disabled');
            }
            if (photoIndex === 0) {
                console.log('Disabling previous button...');
                iwcontent.find('#prev-photo').attr('disabled', true);
            }
        }
    });
    $('#next-photo').on('click', function() {
        if (photoIndex < Number(data.photos.total) - 1) {
            photoIndex++;

            iwcontent.find('#flickr-photo').attr('src', 'https://farm' + photoArray[photoIndex].farm + '.staticflickr.com/' + photoArray[photoIndex].server + '/' + photoArray[photoIndex].id + '_' + photoArray[photoIndex].secret + '_m.jpg');
            iwcontent.find('#photo-num').text(photoIndex + 1);
            if (photoIndex === 1) {
                console.log('Enabling previous button...');
                iwcontent.find('#prev-photo').removeAttr('disabled');
            }
            if (photoIndex + 1 === Number(data.photos.total)) {
                console.log('Disabling next button...');
                iwcontent.find('#next-photo').attr('disabled', true);
            }
        }
    });
    console.log('iwcontent now:');
    console.log(iwcontent[0]);
    infowindow.setContent(iwcontent[0]);
    // infowindow.open(map, marker);

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
