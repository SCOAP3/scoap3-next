require.config({
  baseUrl: "/static/",
  paths: {
    jquery: "node_modules/jquery/jquery",
    bootstrap: "node_modules/bootstrap-sass/assets/javascripts/bootstrap",
    angular: "node_modules/angular/angular",
    typeahead: 'node_modules/typeahead.js/dist/typeahead.jquery',
    bloodhound: 'node_modules/typeahead.js/dist/bloodhound',
  },
  shim: {
    angular: {
      exports: 'angular'
    },
    jquery: {
      exports: "$"
    },
    bootstrap: {
      deps: ["jquery"]
    }
  }
});
