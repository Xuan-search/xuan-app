(function ($){
	

	Xuan = {

	};

})(jQuery);

function renderSearchResult(hit){
	var template = "<li class='xs-book-info'>"+
				"<a class='xs-book-title'>{0}</a>"+
				"<span class='xs-book-score'>Score:{1}</span>"+
			"</li>";
	return template.format(hit.fields.book_title[0],hit._score);
}
function showSearchResults(data){
	var list = $(".xs-search-results");
	console.log("Searchresult");
	list.html("");
	var hits = data.hits.hits;
	for(ind in hits){
		console.log(hits[ind]);
		list.append(renderSearchResult(hits[ind]));
	}
	//console.log(data);
	//var jsObj = JSON.parse(data);
	//console.log(jsObj);
}	
function submitSearch(e){
	e.preventDefault();
	$.ajax({
  		url: "http://52.10.91.42:8000/api/books?q="+
		$("#searchterms").val()}).success(showSearchResults);
	
}
$(document).ready(function(){
	if (!String.prototype.format) {
 		 String.prototype.format = function() {
    		var args = arguments;
    		return this.replace(/{(\d+)}/g, function(match, number) { 
      			return typeof args[number] != 'undefined'
        		? args[number]
        		: match;
   		 });
  		};
	}	
	$("#search-form").submit(submitSearch);	
	

});
