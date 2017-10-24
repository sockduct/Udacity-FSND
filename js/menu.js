/*
    Knockout Code - Map Menu/Points of Interest List
 */

'use strict';

// Model
var pointsOfInterest = [
    {title: 'Wixom Fire Department', location: {lat: 42.540713, lng: -83.537809}},
    {title: 'Wixom Habitat Vista', location: {lat: 42.538552, lng: -83.541523}},
    {title: 'Wixom City Hall Fountain', location: {lat: 42.524013, lng: -83.532183}},
    {title: "Alex's Pizzeria", location: {lat: 42.524625, lng: -83.532651}},
    {title: 'Puckmasters', location: {lat: 42.520194, lng: -83.552822}},
    {title: 'Detroit Public Television', location: {lat: 42.500581, lng: -83.553301}}
];


// ViewModel
var pointOfInterest = function(poiData) {
    this.title = ko.observable(poiData.title);
    this.location = ko.observable(poiData.location);
};

var viewModel = function() {
    var self = this;  // Store a reference to the viewModel.currentLocation object
    this.poiList = ko.observableArray([]);

    pointsOfInterest.forEach(function(poi) {
        self.poiList.push(new pointOfInterest(poi));
    });
    // this.currentPoi = null;  // Start out with no POI set
    this.currentPoi = ko.observable(this.poiList()[0]);

    this.updateCurrentPoi = function(clickedPoi) {
        self.currentPoi(clickedPoi);
    };
};

ko.applyBindings(new viewModel());
