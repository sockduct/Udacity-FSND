/*
    Web Application Code
    * Google Maps API functionality implement by the Google Maps JavaScript Library
    * Menu (Nav Sidebar) functionality implemented by Knockout
*/
/* jshint esversion: 6 */

// Application namespace:
var app = app || {};
// Application Object for Google Map:
app.map;
// Application InfoWindow namespace:
var appiw = appiw || {};
// Application Object for Google Map InfoWindow:
appiw.infowindow;
// Only once:
appiw.iwbound = false;

// Console object:
var console = console || {};

// Library definitions to quiet complaining linter:
var $ = $ || {};  // jQuery
var ko = ko || {};  // Knockout
var google = google || {};  // Google top level (google.maps.*)

// Don't use strict mode globally - this can cause problems in a typical production
// environment.  The build process will often concatenate all JavaScript files together
// resulting in strict mode being enabled everywhere.  Some legacy code/libraries
// doesn't work with strict mode.  Instead, create an application namespace and enable
// strict mode within there.
// 'use strict';


// IIFE for app:
(function() {
    'use strict';

    // Put Flickr API Key Here:
    // var flickrAPIKey = '<key>';

    // Object for knockout to store info about a point of interest from the map (marker)
    var pointOfInterest = function(poiData) {
        this.title = ko.observable(poiData.title);
        this.location = ko.observable(poiData.location);
    };

    // Keep track of menu list filter to allow toggling it on and off
    // var filterRecall = '';

    // Array to hold Google Map marker locations:
    var markers = [];

    // Array of Points of Interest for Google Map markers
    // Loaded via AJAX from outside the IIFE
    app.pointsOfInterest = [];

    // Gates for AJAX calls, used outside the IIFE
    app.mapGate = false;
    app.placesGate = false;

    // Callback to initialize Google Map
    app.initMap = function() {
        // Constructor creates a new map - only center and zoom are required
        // Need to specify where to load map (using #map here)
        // Need to also specify coordinates - center & zoom values (0-22)
        var mapDiv = $('#map');  // jQuery returns collection of 0 or 1
        var wixom = {lat: 42.524970, lng: -83.536211};  // Use zoom of 13
        // Match max width of Flickr Photo
        appiw.infowindow = new google.maps.InfoWindow({
            maxWidth: 250
        });

        app.map = new google.maps.Map(mapDiv[0], {
            center: wixom,
            zoom: 13
        });

        app.mapGate = true;
    };

    // Callback if we can't reach Google Maps API or experience some kind of failure
    app.initMapError = function() {
        var mapDiv = $('#map');
        mapDiv.append('<h2><em>Unable to load map from Google Maps API... </em> :-(</h2>');
    };

    app.initMarkers = function() {
        // Custom icons
        // Style the marker icons
        var defaultIcon = makeMarkerIcon('0091ff');
        // This will be a "highlighted location" marker color for when user mouses
        // over the marker
        var highlightedIcon = makeMarkerIcon('ffff24');
        // var selectedIcon = makeMarkerIcon('3db73c');

        // Change just to eliminate JSHint Warning
        // for (var i = 0; i < pointsOfInterest.length; i++) {
        app.pointsOfInterest.forEach(function (poi) {
            // Get the position from the location array.
            var position = poi.location;
            var title = poi.title;
            // Create a marker per location, and put into markers array.
            var marker = new google.maps.Marker({
                map: app.map,
                position: position,
                title: title,
                animation: google.maps.Animation.DROP,
                icon: defaultIcon,
                id: poi.place
            });

            // Push the marker to our array of markers.
            markers.push(marker);
            // Create an onclick event to open an infowindow at each marker.
            marker.addListener('click', function() {
                // Clicked marker = this
                resetMarkerIcons();
                this.setAnimation(google.maps.Animation.DROP);
                this.setIcon(highlightedIcon);
                appiw.ViewModel.getPlacesDetails(this, appiw.infowindow);
            });
            // Two event listeners - one for mouseover, one for mouseout,
            // to change the colors back and forth.
            marker.addListener('mouseover', function() {
                this.setIcon(highlightedIcon);
            });
            marker.addListener('mouseout', function() {
                this.setIcon(defaultIcon);
            });
        });
    };

    // Google Maps API Marker Customization function
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

    // Reset all Google Map markers to the default color
    function resetMarkerIcons() {
        markers.forEach(function (marker) {
            var defaultIcon = makeMarkerIcon('0091ff');
            marker.setIcon(defaultIcon);
        });
    }


    /*
        Knockout Code - Map Menu/Points of Interest List
     */

    // Knockout ViewModel functionality
    app.ViewModel = function() {
        var self = this;  // Store a reference to the app.ViewModel object
        this.filterText = ko.observable('');
        this.filterBtn = $('#filter-button');
        // Hide Side Navbar Elements unless screen width at least 768 pixels
        this.showNavElmts = ko.observable(false);
        this.poiList = ko.observableArray([]);
        this.currentPoi = ko.observable();  // Start out with no POI set

        this.populatePoiList = function(filterString) {
            var re1 = new RegExp(filterString, 'i');

            if ($(window).width() >= 768) {
                self.showNavElmts(true);
            }

            // Purge any existing elements
            if (self.poiList().length) {
                self.poiList.splice(0, self.poiList().length);
            }
            // Hide all map markers
            for (let i = 0; i < markers.length; i++) {
                markers[i].setMap(null);
            }

            // app.pointsOfInterest.forEach(function(poi) {  // use for loop so have index
            // Change i to j, solely to eliminate JSHint Warning
            for (let i = 0; i < app.pointsOfInterest.length; i++) {
                // If no filter or matching filter, add element
                if (!filterString || (filterString && app.pointsOfInterest[i].title.match(re1))) {
                    self.poiList.push(new pointOfInterest(app.pointsOfInterest[i]));
                    // Display relevant marker on map if initialized
                    if (markers[i]) {
                        markers[i].setMap(app.map);
                    }
                }
            }
        };
        this.populatePoiList();

        this.updateCurrentPoi = function(clickedPoi) {
            var highlightedIcon = makeMarkerIcon('ffff24');
            self.currentPoi(clickedPoi);
            // console.log('You clicked on:  ' + clickedPoi.title());

            for (let i = 0; i < app.pointsOfInterest.length; i++) {
                if (app.pointsOfInterest[i].title === clickedPoi.title()) {
                    // For small screens, toggle the list menu closed so infowindow
                    // isn't too narrow
                    if ($(window).width() < 768 && $('.sidebar').hasClass('active')) {
                        $('#sidebarCollapse').trigger('click');
                    }
                    resetMarkerIcons();
                    // Center map to selected marker:
                    app.map.panTo(markers[i].getPosition());
                    markers[i].setAnimation(google.maps.Animation.DROP);
                    markers[i].setIcon(highlightedIcon);
                    appiw.ViewModel.getPlacesDetails(markers[i], appiw.infowindow);
                    break;
                }
            }
        };

        this.toggleNavBar = function() {
            $('.sidebar').toggleClass('active');
            $('#map').toggleClass('active');
            // Querying CSS shows what the sidebar was
            // Note - can't do simple toggle because the meaning of "active" changes
            // depending on the viewport width
            if ($('.sidebar').css('margin-left') === '-150px') {
                // Sidebar was hidden (negative value)
                // It just got opened, show Nav Elements
                self.showNavElmts(true);
            } else {
                // Just got closed, hide Nav Elements
                self.showNavElmts(false);
            }
        };
    };
})();


// IIFE for appiw:
(function() {
    'use strict';

    // ViewModel for InfoWindow
    appiw.ViewModel = {
        init: function() {
            var self = this;  // Store a reference to the appiw.ViewModel object

            // InfoWindow Data
            this.iwdata = {};

            this.iwdataInit = function() {
                this.title = '';
                // Google Maps, Places Info Container
                this.place = {};
                // Flick Photo Array
                this.photoArray = [];
                // Current Flickr Photo Index
                this.photoIndex = ko.observable(0);
                // Total number of Flickr Photos for current point of interest
                this.photoTotal = ko.observable('0');
                // Current Flickr retrieval URL
                this.photoSrc = ko.observable('');
                // Current Flickr photo "alt tag" text/status
                this.photoAlt = ko.observable('Checking for Flickr Photos...');

                // Hide (default) or Show Flickr Attribution and Photo Controls
                this.showCredit = ko.observable(false);
                this.showPhotoCtl = ko.observable(false);
            };

            this.flickrPrevPhoto = function() {
                if (self.iwdata.photoIndex() > 0) {
                    self.iwdata.photoIndex(self.iwdata.photoIndex() - 1);

                    self.iwdata.photoSrc('https://farm' + self.iwdata.photoArray[self.iwdata.photoIndex()].farm + '.staticflickr.com/' + self.iwdata.photoArray[self.iwdata.photoIndex()].server + '/' + self.iwdata.photoArray[self.iwdata.photoIndex()].id + '_' + self.iwdata.photoArray[self.iwdata.photoIndex()].secret + '_m.jpg');
                }
            };
            this.flickrNextPhoto = function() {
                if (self.iwdata.photoIndex() < Number(self.iwdata.photoTotal()) - 1) {
                    self.iwdata.photoIndex(self.iwdata.photoIndex() + 1);

                    self.iwdata.photoSrc('https://farm' + self.iwdata.photoArray[self.iwdata.photoIndex()].farm + '.staticflickr.com/' + self.iwdata.photoArray[self.iwdata.photoIndex()].server + '/' + self.iwdata.photoArray[self.iwdata.photoIndex()].id + '_' + self.iwdata.photoArray[self.iwdata.photoIndex()].secret + '_m.jpg');
                }
            };
        },

        // Google Maps API Place function leveraging the places library
        // This is the PLACE DETAILS search - it's the most detailed so it's only
        // executed when a marker is selected, indicating the user wants more
        // details about that place.
        // Note: It uses placeid to get place details and display in an infowindow above
        // user cliked place marker
        getPlacesDetails: function(marker, infowindow) {
            var service = new google.maps.places.PlacesService(app.map);
            service.getDetails({
                placeId: marker.id
            }, function(place, status) {
                // Set the marker property on this infowindow so it isn't created again.
                infowindow.marker = marker;
                // Reset iwdata:
                appiw.ViewModel.iwdataInit.call(appiw.ViewModel.iwdata);

                // Use jQuery to create new div/DOM element
                var iwcontent = '<div id="info-window" data-bind="template: {name: \'info-window-template\', data: appiw.ViewModel.iwdata}"></div>';
                appiw.ViewModel.iwdata.title = marker.title;
                if (status === google.maps.places.PlacesServiceStatus.OK) {
                    // console.log('Successful query to Google Maps, Places API:');
                    // console.log(place);
                    // For each potential information element from places details, need to check
                    // if it's present - it may or may not be
                    /* Use marker.title instead
                    if (place.name) {
                        appiw.ViewModel.iwdata.place.name = place.name;
                    }
                    */
                    if (place.formatted_address) {
                        appiw.ViewModel.iwdata.place.formatted_address = place.formatted_address;
                    }
                    if (place.formatted_phone_number) {
                        appiw.ViewModel.iwdata.place.formatted_phone_number = place.formatted_phone_number;
                    }
                    if (place.opening_hours) {
                        appiw.ViewModel.iwdata.place.opening_hours = place.opening_hours;
                    }
                    /* Use Flickr photos instead...
                    if (place.photos) {
                        // Image Formatting: '<br><br><img src="' + place.photos[0].getUrl({maxHeight: 100, maxWidth: 200}) + '">'
                        appiw.ViewModel.iwdata.place.photos = place.photos[0];
                    }
                    */
                    if (place.website) {
                        appiw.ViewModel.iwdata.place.website = '<a href="' + place.website + '" target="_blank">' + place.website + '</a>';
                    }
                } else {
                    console.log('Failed query to Google Maps, Places API - status of ' + status + ':');
                    console.log(place);
                    appiw.ViewModel.iwdata.place.error = true;
                }

                infowindow.setContent(iwcontent);

                // Bind InfoWindow to KO Template
                // console.log('getPlacesDetails/iwbound:  ' + iwbound);
                // google.maps.event.addListener(app.ViewModel, 'domready', function() {
                google.maps.event.addListener(infowindow, 'domready', function() {
                    // Note - couldn't get this to work
                    //        if applied once as shown in example, then infowindow only works
                    //        once
                    //        if applied every time infowindow opens then get error from knockout
                    //        about rebinding to already bound viewmodel
                    // if (!appiw.iwbound) {
                        // ko.applyBindings(app.ViewModel, $('#info-window')[0]);
                    ko.cleanNode($('#info-window')[0]);
                    ko.applyBindings(appiw.ViewModel, $('#info-window')[0]);
                        // appiw.iwbound = true;
                    // }
                });

                infowindow.open(app.map, marker);
                // Make sure the marker property is cleared if the infowindow is closed.
                infowindow.addListener('closeclick', function() {
                    infowindow.marker = null;
                });

                appiw.ViewModel.getPhotos(marker.title);
            });
        },

        // Query Flickr for place photos and retrieve if available (using AJAX)
        getPhotos: function(title) {
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
                    // Update photo div appropriately (Flickr unavailable...)
                })
                .always(function(reqRespObj, reqStat) {
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

                    if (photoData.photos.total === '0' && title.split(' ').length > 2) {
                        var newTitle = title.slice(0, title.lastIndexOf(' '));
                        // Retry with more general title search
                        appiw.ViewModel.getPhotos(newTitle);
                    } else {
                        appiw.ViewModel.installPhotos(photoData);
                    }
                });
        },

        // Update iwdata with retrieved Flicrk photo(s)
        installPhotos: function(photoData) {
            // Update photo div appropriately
            if (photoData.error) {
                console.log('installPhotos:  passed photo data set encountered errors...');
                appiw.ViewModel.iwdata.photoAlt('Failed to retrieve Flickr Photo(s).');
            } else {
                switch (photoData.photos.total) {
                    case '0':
                        appiw.ViewModel.iwdata.photoAlt('No Flickr Photos found...');
                        break;
                    default:
                        // Photo Retrieval:
                        // m = 240px max, n = 320px max
                        // https://farm{farm-id}.staticflickr.com/{server-id}/{id}_{secret}_m.jpg'
                        // Could use template literals, but no IE support...
                        // var photoArray = photoData.photos.photo;
                        appiw.ViewModel.iwdata.photoArray = photoData.photos.photo;
                        // Replace photoData.photos.total with photoTotal:
                        appiw.ViewModel.iwdata.photoTotal(photoData.photos.total);
                        appiw.ViewModel.iwdata.photoAlt('Flickr Photo');
                        appiw.ViewModel.iwdata.photoSrc('https://farm' + appiw.ViewModel.iwdata.photoArray[appiw.ViewModel.iwdata.photoIndex()].farm + '.staticflickr.com/' + appiw.ViewModel.iwdata.photoArray[appiw.ViewModel.iwdata.photoIndex()].server + '/' + appiw.ViewModel.iwdata.photoArray[appiw.ViewModel.iwdata.photoIndex()].id + '_' + appiw.ViewModel.iwdata.photoArray[appiw.ViewModel.iwdata.photoIndex()].secret + '_m.jpg');
                        appiw.ViewModel.iwdata.showCredit(true);

                        // if (Number(photoData.photos.total) > 1) {
                        if (Number(appiw.ViewModel.iwdata.photoTotal()) > 1) {
                            appiw.ViewModel.iwdata.showPhotoCtl(true);
                        }
                        // Now Pan down so InfoWindow fits on screen:
                        /*  Height Adjustments:
                            Title - 15 (all have a title)
                            Address - 30 (most have, sometimes wrap so 30 vs 15)
                            Phone# - 15 (some have)
                            URL - 15 (some have)
                            Hours - 135 (a few have)
                            Picture - 255 (all have at least one picture)
                            Source - 15 (all have)
                            Buttons - 36 (most have)
                            Framing Divs - 19 (all have)
                            Buffer so not right at top of screen - 10
                            +35-40 if width < 768
                        */
                        var panAdjust = 0 + 15 + 255 + 15 + 19 + 10;
                        if (appiw.ViewModel.iwdata.place.formatted_address) {
                            panAdjust += 30;
                        }
                        if (appiw.ViewModel.iwdata.place.formatted_phone_number) {
                            panAdjust += 15;
                        }
                        if (appiw.ViewModel.iwdata.place.website) {
                            panAdjust += 15;
                        }
                        if (appiw.ViewModel.iwdata.place.opening_hours) {
                            panAdjust += 135;
                        }
                        if (Number(appiw.ViewModel.iwdata.photoTotal()) > 1) {
                            panAdjust += 36;
                        }
                        if ($(window).width() < 768) {
                            panAdjust += 50;
                        }
                        panAdjust -= Math.ceil($(window).height()/2);
                        if (panAdjust > 0) {
                            app.map.panBy(0, -panAdjust);
                        }
                }
            }
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
    };
})();


// Note:  If hosting locally, must serve via a web server or will receive the following error:
// Cross origin requests are only supported for protocol schemes: http, data, chrome, chrome-extension, https.
$.getJSON('places.json')
    .done(function(jsonData, reqStat, reqObj) {
        console.log('Loading places data finished with status "' + reqStat + '".');
        app.pointsOfInterest = jsonData;
    })
    .fail(function(reqObj, reqStat, errThrown) {
        console.log('Loading places data failed with status "' + reqStat + '".');
        if (errThrown) {
            console.log('Error thrown:  "' + errThrown + '".');
        }
    })
    .always(function(reqRespObj, reqStat) {
        if (reqStat !== 'success') {
            console.log('Failed to load places data - loading error marker.');
            app.pointsOfInterest[0] = {title: 'Failed to load Wixom Points of Interest',
                location: {lat: 42.5247555, lng: -83.5363268},
                place: 'ChIJ7xtMYSCmJIgRZBZBy5uZHl8'};
        }

        app.placesGate = true;

        // Initiate two way bindings between View and ViewModel
        // Must use new or get errors!
        app.RunTime = new app.ViewModel();
        app.RunTime.filterText.subscribe(app.RunTime.populatePoiList);
        // ko.applyBindings(new app.ViewModel());
        ko.applyBindings(app.RunTime);

        // Gate check:
        app.gateCount = 0;
        app.gate();
    });


app.gate = function () {
    app.gateCount++;

    if (app.mapGate && app.placesGate) {
        appiw.ViewModel.init();
        app.initMarkers();
    } else if (app.gateCount < 51) {
        if (app.gateCount % 4 === 0) {
            console.log('Waiting for Google Map and Places data to finish loading...');
        }
        setTimeout(app.gate, 200);
    } else {
        console.log('Giving up...');
    }
};
