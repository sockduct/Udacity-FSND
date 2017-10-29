/*
    Knockout Code - Map Menu/Points of Interest List
 */

'use strict';

// Model
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


// ViewModel
var pointOfInterest = function(poiData) {
    this.title = ko.observable(poiData.title);
    this.location = ko.observable(poiData.location);
};

var filterRecall = '';

var viewModel = function() {
    var self = this;  // Store a reference to the viewModel object
    this.filterText = $('#filter-text');
    this.filterBtn = $('#filter-button');
    this.poiList = ko.observableArray([]);
    // this.currentPoi = null;  // Can't start out with null - must be observable
    this.currentPoi = ko.observable();  // Start out with no POI set
    // this.currentPoi = ko.observable(this.poiList()[0]);

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
        self.currentPoi(clickedPoi);
        console.log('You clicked on:  ' + clickedPoi.title());

        for (var i = 0; i < pointsOfInterest.length; i++) {
            if (pointsOfInterest[i].title === clickedPoi.title()) {
                // populateInfoWindow(markers[i], largeInfoWindow);
                // Try collecting photos first and then passing into getPlacesDetails
                getPlacesDetails(markers[i], largeInfoWindow);
                getPhotos(clickedPoi.title());
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
        // console.log('You submitted:  ' + filterTextVal);

        // Do last - remember applied filter:
        filterRecall = filterTextVal;
    });
};

ko.applyBindings(new viewModel());
