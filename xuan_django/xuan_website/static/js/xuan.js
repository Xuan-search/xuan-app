(function ($){
	//testing changes

	Xuan = {
				


		
	};

})(jQuery);


var currentSearch = "";
var searching = false;
var baseUrl = (window.location&&window.location.origin?window.location.origin:"http://99xuan.com");

Xuan.ttsReader = {
	locale: 'en-us',
	url : '/api/audio?src={0}&hl={1}',
	template: '<audio class="xs-tts-reader" controls autoplay type="audio/mpeg"></audio>',
	renderTo:function(el){
		if(!el.find(".xs-tts-reader").get(0)){
			//tts shouldn't exist on this page
			return;
		}
		this.audioEl = el.find(".xs-tts-reader");
		this.audioKitEnabled = true;
		if(typeof AudioContext !=='undefined'){
			this.audioContext = new AudioContext();		
                	var audioSrc = this.audioContext.createMediaElementSource(this.audioEl.get(0));
                
			this.audioAnalyser = this.audioContext.createAnalyser();
			audioSrc.connect(this.audioAnalyser);
                
			audioSrc.connect(this.audioContext.destination);

                //audioSrc.connect(this.audioAnalyser);
			this.avatarImg = el.find(".xs-tts-avatar");
		}else{
			this.audioKitEnabled = false;
			el.find(".xs-tts-avatar").hide();
		}
		//this.$el = $(this.template).appendTo(el);
		return this;
	},
	getSelectionText: function() {
    		var text = "";
		if (window.getSelection) {
        		text = window.getSelection().toString();
    		} else if (document.selection && document.selection.type != "Control") {
        		text = document.selection.createRange().text;
    		}
		//remove server-breaking text
		text = text.replace("—", ",");
    		return text;
	},

	getRequestUrl: function(){
		return baseUrl+this.url.format(
			this.getSelectionText(),
			this.locale)
	},
	loadData: function(){
		this.audioEl.attr('src', this.getRequestUrl());
		if(!this.audioKitEnabled) return;
		var $this = this;
		this.audioEl.on('canplay',function(){
			$this.audioEl.off('canplay');
			var audio = $this.audioEl.get(0);
			audio.play();
			
			$this.frequencyData = new Uint8Array($this.audioAnalyser.frequencyBinCount);			
			$this.peakVolume = 0;
			var animateAvatar = function(){
				requestAnimationFrame(animateAvatar);
				if(audio.paused){		
					$this.avatarImg.attr('src', '/media/img/anim1.png');
					return;		
				}
                		$this.audioAnalyser.getByteFrequencyData($this.frequencyData);
				var animKey = 1;
				var medThreshold = $this.peakVolume/2;
				var highThreshold = $this.peakVolume/4*3;
				var volume = 0;
				var start = -1;
				var end = -1;
				var bandfreq = $this.frequencyData.length/4;
				for(var i=0; i < bandfreq;i++){
					if(start<0&&$this.frequencyData[i]>0){
						start=i;
					}
					volume += $this.frequencyData[i];
				}
				volume = volume/bandfreq;
				if($this.peakVolume<volume){
					$this.peakVolume = volume;
				}else if (highThreshold < volume){
					animKey = 3;
				}else if (medThreshold < volume){
					animKey = 2;
				}		
				$this.avatarImg.attr('src', '/media/img/anim'+animKey+'.png');
			};
			animateAvatar();
		});
	
			
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



function renderSearchResult(hit){
	var template = "<li class='xs-book-info'>"+
				"<a href='/book/{0}?q={3}' class='xs-book-title'>{1}</a></br>"+
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
	var hit = $(".xs-search-hit").first();
	if(hit.length){
		$("html, body").animate({
			scrollTop:hit.offset().top - $(".xs-navbar").height()
		});
	}
	$("#search-form").submit(submitSearch);	
	
	var ttsReader = Xuan.ttsReader.renderTo($(".xs-reader"));
	if(ttsReader){
		$(".xs-reader").find(".xs-tts-play").click(
			function(){
				ttsReader.loadData();
			});

	}
});
