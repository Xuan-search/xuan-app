(function ($){
	//testing changes

	Xuan = {
				


		
	};

})(jQuery);
Xuan.ttsReader = {
	apiKey: '5aa6f086f1634e8f912342118ab4de9f',
	locale: 'en-us',
	url : 'http://api.voicerss.org/?key={0}&src={1}&hl={2}',
	template: '<audio class="xs-tts-reader" controls type="audio/mpeg" autoplay></audio>',
	renderTo:function(el){
		this.$el = $(this.template).appendTo(el);
		try{
			window.AudioContext = window.AudioContext || window.webkitAudioContext;
			this.audioContext = new AudioContext();
		}
		catch(e){
    			alert('Web Audio API is not supported in this browser');
		}
		return this;
	},
	getSelectionText: function() {
    		var text = "";
		if (window.getSelection) {
        	text = window.getSelection().toString();
    		} else if (document.selection && document.selection.type != "Control") {
        		text = document.selection.createRange().text;
    		}
    		return text;
	},

	getRequestUrl: function(){
		return this.url.format(this.apiKey,
			this.getSelectionText(),
			this.locale)
	},
		
	loadData: function(){
		
		this.$el.attr('src', this.getRequestUrl());
		/*
		// get some kind of XMLHttpRequest
		var xhrObj = new XMLHttpRequest();
		// open and send a synchronous request
		xhrObj.open('GET', this.getRequestUrl(), true);
		//xhrObj.responseType = 'arraybuffer';
		var $context = this.audioContext;
		var element = this.$el;
		xhrObj.onload = function(e){
			$context.decodeAudioData(
				xhrObj.response,
				function(buffer){
					console.log("playing");
					//var source = $context.createMediaElementSource(element.get(0));
					var source = $context.createBufferSource();
					source.buffer = buffer;
					console.log(buffer);
					source.connect($context.destination);
					console.log(source);
					
					source.onended = function(){
						console.log("y u no play");
					}	
					source.start();
				
				},
				function(error){
					alert("load audio failed:"+error);
				})
			
			console.log("play attempt");
			var data = xhrObj.response;
			//var encodedData = btoa(data);
			//console.log(encodedData);
			console.log(data);
			element.attr('src','"data:audio/mp3;base64,'+data);
			
		},
		xhrObj.send();
		
		// add the returned content to a newly created script tag
		//var se = document.createElement('script');
		// se.type = "text/javascript";
		
		
		//this.$el.attr("src",xhrObj.responseText);
		// document.getElementsByTagName('head')[0].appendChild(se);
		*/
	}
	

};



var currentSearch = "";
var searching = false;
var baseUrl = (window.location&&window.location.origin?window.location.origin:"http://99xuan.com");
function renderSearchResult(hit){
	var template = "<li class='xs-book-info'>"+
				"<a href='/book/{0}?q={3}#xs-search-hit' class='xs-book-title'>{1}</a></br>"+
				//"<span class='xs-book-score'>Score:{2}</span>"+
				"<div class='xs-book-exerpts'>{2}</div>"
			"</li>";
	var selectedExerpt = hit.highlight.html_body[0];
	for(var i in hit.highlight.html_body){
		var testString = hit.highlight.html_body[i];
		var openTagStart = testString.match(/<[^/^e]/g);
		var closeTagStart = testString.match(/<[/][^e]/g);
		var tagEnd = testString.match(/[^m]>/g);
		if(!openTagStart && !closeTagStart && !tagEnd){
			selectedExerpt = hit.highlight.html_body[i];
			break;
		}
	}


	return template.format(hit._id, hit.fields.book_title[0]/*,hit._score*/,selectedExerpt,currentSearch);
}
function showSearchResults(data){
	$('.xs-body-container').toggleClass('loaded');
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
	$('.xs-body-container').toggleClass('loaded');
	searching = false;
	alert("search failed: "+e);

}
function submitSearch(e){
	e.preventDefault();
	if(searching)return;
	searching = true;
	currentSearch = $("#searchterms").val();
	$('.xs-body-container').toggleClass('loaded');
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
	
	var ttsReader = Xuan.ttsReader.renderTo($(".xs-reader"));
	if(ttsReader.$el){
		console.log("element found");
		$(".xs-reader").find(".xs-tts-play").click(
			function(){
				console.log("clicked");
				ttsReader.loadData();
			});

	}
});
