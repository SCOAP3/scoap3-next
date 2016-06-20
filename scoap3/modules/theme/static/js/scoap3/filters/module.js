define([
  'js/scoap3/filters/striptags',
  'js/scoap3/filters/safe',
  'js/scoap3/filters/titlecase'
], function(striptagsFilter, safeFilter, titlecaseFilter){
  var app = angular.module('scoap3.filters', ['ngSanitize'])
    .filter('striptags', striptagsFilter)
    .filter('titlecase', titlecaseFilter)
    .filter('safe', ['$sce', safeFilter]);
  return app;
});
