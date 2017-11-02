/*
    Web Application Code
    * Google Maps API functionality implement by the Google Maps JavaScript Library
    * Menu (Nav Sidebar) functionality implemented by Knockout
*/

// Disabling to pass JSHint warnings
// 'use strict';

// Hold representation of Google Map and InfoWindow
var map, largeInfoWindow;

// Array to hold Google Map marker locations:
var markers = [];

// Object for knockout to store info about a point of interest from the map (marker)
var pointOfInterest = function(poiData) {
    this.title = ko.observable(poiData.title);
    this.location = ko.observable(poiData.location);
};

// Keep track of menu list filter to allow toggling it on and off
var filterRecall = '';

// Array of Points of Interest for Google Map markers
var pointsOfInterest = [
    {title: "Alex's Pizzeria", location: {lat: 42.524625, lng: -83.532651},
        place: 'Eis0OTAwMCBXIFBvbnRpYWMgVHJhaWwsIFdpeG9tLCBNSSA0ODM5MywgVVNB'},
    {title: 'Detroit Public Television', location: {lat: 42.500581, lng: -83.553301},
        place: 'ChIJz3mlFlmoJIgRiVZL_fZXx50'},
    {title: 'Puckmasters', location: {lat: 42.520194, lng: -83.552822},
        place: 'ChIJw3d8SXyoJIgRI2gTN-ShU40'},
    {title: 'Wixom City Hall Fountain', location: {lat: 42.524013, lng: -83.532183},
        place: 'ChIJD7BLEJ6oJIgRb-8oaW1ao3c'},
    {title: 'Wixom Fire Department', location: {lat: 42.540713, lng: -83.537809},
        place: 'ChIJ_as08TmmJIgRyNMPA08nWI8'},
    {title: 'Wixom Habitat Vista', location: {lat: 42.538552, lng: -83.541523},
        place: 'ChIJI3oMRDqmJIgRClQR9PGkk08'}
];

// Callback to initialize Google Map
function initMap() {
    'use strict';
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

// Callback if we can't reach Google Maps API or experience some kind of failure
function initMapError() {
    'use strict';
    var mapDiv = $('#map');
    mapDiv.append('<h2><em>Unable to load map from Google Maps API... </em> :-(</h2>');
}

// Google Maps API Marker Customization function
// This function takes in a COLOR, and then creates a new marker
// icon of that color. The icon will be 21 px wide by 34 high, have an origin
// of 0, 0 and be anchored at 10, 34).
function makeMarkerIcon(markerColor) {
    'use strict';
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

// Reset all Google Map markers to the default color
function resetMarkerIcons() {
    'use strict';
    markers.forEach(function (marker) {
        var defaultIcon = makeMarkerIcon('0091ff');
        marker.setIcon(defaultIcon);
    });
}

// Google Maps API Place function leveraging the places library
// This is the PLACE DETAILS search - it's the most detailed so it's only
// executed when a marker is selected, indicating the user wants more
// details about that place.
// Note: It uses placeid to get place details and display in an infowindow above
// user cliked place marker
function getPlacesDetails(marker, infowindow) {
    'use strict';
    var service = new google.maps.places.PlacesService(map);
    service.getDetails({
        placeId: marker.id
    }, function(place, status) {
        // Set the marker property on this infowindow so it isn't created again.
        infowindow.marker = marker;

        // Use jQuery to create new div/DOM element
        var iwcontent = $('<div></div>');
        iwcontent.attr('id', 'outer-iwcontent');
        iwcontent.append('<strong>' + marker.title + '</strong>');
        if (status === google.maps.places.PlacesServiceStatus.OK) {
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
        } else {
            iwcontent.append('<br><br><em>Unable to load data from Google Maps, Places API</em>');
        }

        // Add a photo place holder
        iwcontent.append('<br><br><img src="" id="flickr-photo" alt="Checking for Flickr Photos..."></img>');
        infowindow.setContent(iwcontent[0]);
        infowindow.open(map, marker);
        // Make sure the marker property is cleared if the infowindow is closed.
        infowindow.addListener('closeclick', function() {
            infowindow.marker = null;
        });

        getPhotos(marker.title, iwcontent, infowindow);
    });
}

// Query Flickr for place photos and retrieve if available (using AJAX)
function getPhotos(title, iwcontent, infowindow) {
    'use strict';
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
        .done(function(respData, reqStat, reqObj) {
            /*
            console.log('Query finished with status "' + reqStat + '".');
            console.log('respData:');
            console.log(respData);
            */
            // Check Flickr API Call Status
            respData.stat === 'ok' ? respData.error = false : respData.error = true;
        })
        .fail(function(reqObj, reqStat, errThrown) {
            console.log('Query failed with status "' + reqStat + '".');
            if (errThrown) {
                console.log('Error thrown:  "' + errThrown + '".');
            }
            /*
            console.log('reqObj:');
            console.log(reqObj);
            */
            // Update photo div appropriately (Flickr unavailable...)
        })
        .always(function(reqRespObj, reqStat) {
            /*
            console.log('Query completed with status "' + reqStat + '".');
            console.log('reqRespObj:');
            console.log(reqRespObj);
            */
            var photoData;

            if (reqStat === 'success') {
                photoData = reqRespObj;
            } else {
                // Create empty data set:
                photoData = {
                    photos: {total: '0'},
                    error: true
                };
            }

            installPhotos(photoData, iwcontent, infowindow);

            if (photoData.photos.total === '0' && title.split(' ').length > 2) {
                var newTitle = title.slice(0, title.lastIndexOf(' '));
                // Retry with more general title search
                getPhotos(newTitle, iwcontent, infowindow);
            }
        });
}

// Update marker infowindow with retrieved Flicrk photo(s)
function installPhotos(photoData, iwcontent, infowindow) {
    'use strict';
    // Update photo div appropriately
    var photoIndex = 0;

    if (photoData.error) {
        console.log('installPhotos:  passed photo data set encountered errors...');
        iwcontent.find('#flickr-photo').attr('alt', 'Failed to retrieve Flickr Photos.');
    } else {
        switch (photoData.photos.total) {
            case '0':
                console.log('Case 0...');
                iwcontent.find('#flickr-photo').attr('alt', 'No Flickr Photos found...');
                break;
            default:
                // Photo Retrieval:
                // m = 240px max, n = 320px max
                // https://farm{farm-id}.staticflickr.com/{server-id}/{id}_{secret}_m.jpg'
                // Could use template literals, but no IE support...
                var photoArray = photoData.photos.photo;
                iwcontent.find('#flickr-photo').attr({
                    'alt': 'Flickr Photo',
                    'src': 'https://farm' + photoArray[photoIndex].farm + '.staticflickr.com/' + photoArray[photoIndex].server + '/' + photoArray[photoIndex].id + '_' + photoArray[photoIndex].secret + '_m.jpg'
                });
                iwcontent.append('<br>Source:  Flickr Photo API');

                if (Number(photoData.photos.total) > 1) {
                    iwcontent.append('<br><br><button id="prev-photo" type="button" disabled>Previous</button> Flickr Photo <span id="photo-num">' + (photoIndex + 1) + '</span> of ' + photoData.photos.total + ' <button id="next-photo" type="button">Next</button>');
                }
        }
    }

    if (Number(photoData.photos.total) > 1) {
        $('#prev-photo').on('click', function() {
            if (photoIndex > 0) {
                photoIndex--;

                iwcontent.find('#flickr-photo').attr('src', 'https://farm' + photoArray[photoIndex].farm + '.staticflickr.com/' + photoArray[photoIndex].server + '/' + photoArray[photoIndex].id + '_' + photoArray[photoIndex].secret + '_m.jpg');
                iwcontent.find('#photo-num').text(photoIndex + 1);
                if (photoIndex + 1 === Number(photoData.photos.total) - 1) {
                    iwcontent.find('#next-photo').removeAttr('disabled');
                }
                if (photoIndex === 0) {
                    iwcontent.find('#prev-photo').attr('disabled', true);
                }
            }
        });
        $('#next-photo').on('click', function() {
            if (photoIndex < Number(photoData.photos.total) - 1) {
                photoIndex++;

                iwcontent.find('#flickr-photo').attr('src', 'https://farm' + photoArray[photoIndex].farm + '.staticflickr.com/' + photoArray[photoIndex].server + '/' + photoArray[photoIndex].id + '_' + photoArray[photoIndex].secret + '_m.jpg');
                iwcontent.find('#photo-num').text(photoIndex + 1);
                if (photoIndex === 1) {
                    iwcontent.find('#prev-photo').removeAttr('disabled');
                }
                if (photoIndex + 1 === Number(photoData.photos.total)) {
                    iwcontent.find('#next-photo').attr('disabled', true);
                }
            }
        });
    }
    infowindow.setContent(iwcontent[0]);

    /* Notes:
    Example JSON Response:
    { "photos": { "page": 1, "pages": 1, "perpage": 100, "total": 50,
        "photo": [
          { "id": "11876531065", "owner": "88636811@N06", "secret": "b23b77d7a1", "server": "7390", "farm": 8, "title": "cold", "ispublic": 1, "isfriend": 0, "isfamily": 0 },
          (...),
        ] },
     "stat": "ok" }
    */
}

// Function to implement collapsable sidebar
$('#sidebarCollapse').on('click', function(event) {
    // Prevent following hyperlink
    event.preventDefault();
    $('.sidebar').toggleClass('active');
    $('#map').toggleClass('active');
    $('#filter-button').toggleClass('hidden');
});


/*
    Knockout Code - Map Menu/Points of Interest List
 */

// Knockout ViewModel functionality
var viewModel = function() {
    'use strict';
    var self = this;  // Store a reference to the viewModel object
    this.filterText = $('#filter-text');
    this.filterBtn = $('#filter-button');
    this.poiList = ko.observableArray([]);
    this.currentPoi = ko.observable();  // Start out with no POI set

    this.populatePoiList = function(filterString) {
        var re1 = new RegExp(filterString, 'i');

        // Purge any existing elements
        if (self.poiList().length) {
            self.poiList.splice(0, self.poiList().length);
        }
        // Hide all map markers
        for (var i = 0; i < markers.length; i++) {
            markers[i].setMap(null);
        }

        // pointsOfInterest.forEach(function(poi) {  // use for loop so have index
        for (var i = 0; i < pointsOfInterest.length; i++) {
            // If no filter or matching filter, add element
            if (!filterString || (filterString && pointsOfInterest[i].title.match(re1))) {
                self.poiList.push(new pointOfInterest(pointsOfInterest[i]));
                // Display relevant marker on map if initialized
                if (markers[i]) {
                    markers[i].setMap(map);
                }
            }
        }
    };
    this.populatePoiList();

    this.updateCurrentPoi = function(clickedPoi) {
        var highlightedIcon = makeMarkerIcon('ffff24');
        self.currentPoi(clickedPoi);
        console.log('You clicked on:  ' + clickedPoi.title());

        for (var i = 0; i < pointsOfInterest.length; i++) {
            if (pointsOfInterest[i].title === clickedPoi.title()) {
                resetMarkerIcons();
                markers[i].setAnimation(google.maps.Animation.DROP);
                markers[i].setIcon(highlightedIcon);
                getPlacesDetails(markers[i], largeInfoWindow);
                break;
            }
        }
    };

    this.filterBtn.on('click', function(event) {
        // Prevent page refresh
        event.preventDefault();
        var filterTextVal = self.filterText.val();

        // Filter applied - set button color to orange
        if (filterTextVal && filterTextVal !== filterRecall) {
            self.filterBtn.removeClass();
            self.filterBtn.addClass('btn btn-warning');
        // Filter cleared - set button color to green
        } else {
            // Click on filter button without chaning text --> clear filter
            if (filterTextVal === filterRecall) {
                // Clear filter
                filterTextVal = '';
            }
            self.filterBtn.removeClass();
            self.filterBtn.addClass('btn btn-success');
        }

        self.populatePoiList(filterTextVal);
        // Do last - remember applied filter:
        filterRecall = filterTextVal;
    });
};

ko.applyBindings(new viewModel());
