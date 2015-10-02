(function ($){
	//testing changes

	Xuan = {

	};

})(jQuery);
var baseUrl = "http://52.26.252.216:8000";
var currentSearch = "";
var searching = false;
function renderSearchResult(hit){
	var template = "<li class='xs-book-info'>"+
				"<a href='/book/{0}?q={3}#xs-search-hit' class='xs-book-title'>{1}</a></br>"+
				//"<span class='xs-book-score'>Score:{2}</span>"+
				"<div class='xs-book-exerpts'>{2}</div>"
			"</li>";
	var selectedExerpt = hit.highlight.html_body[0];
	for(var i in hit.highlight.html_body){
		console.log("searching: "+hit.highlight.html_body[i]);
		var testString = hit.highlight.html_body[i];
		var openTagStart = testString.match(/<[^/^e]/g);
		var closeTagStart = testString.match(/<[/][^e]/g);
		var tagEnd = testString.match(/[^m]>/g);
		
		
		if(!openTagStart && !closeTagStart && !tagEnd){
			selectedExerpt = hit.highlight.html_body[i];
			console.log("found:"+openTagStart + "," + closeTagStart + "," +tagEnd);
			break;
		}
	}


	return template.format(hit._id, hit.fields.book_title[0]/*,hit._score*/,selectedExerpt,currentSearch);
}
function showSearchResults(data){
	var list = $(".xs-search-results");
	list.html("");
	var hits = data.hits.hits;
	for(ind in hits){
		console.log(hits[ind]);
		list.append(renderSearchResult(hits[ind]));
	}
	searching = false;
	//console.log(data);
	//var jsObj = JSON.parse(data);
	//console.log(jsObj);
}	
function searchFailure(e){
	searching = false;
	alert("search failed: "+e);

}
function submitSearch(e){
	e.preventDefault();
	if(searching)return;
	searching = true;
	currentSearch = $("#searchterms").val();
	$.ajax({
  		url: baseUrl + "/api/books?q="+currentSearch+
		"&exact="+$(".xs-search-checkbox").is(':checked')
	}).success(showSearchResults).fail(searchFailure);
	
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
