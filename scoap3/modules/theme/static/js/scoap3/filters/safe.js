define([], function(){
  function safeFilter($sce) {
    return function(text) {
      return $sce.trustAsHtml(text);
    };
  }
  return safeFilter;
});
