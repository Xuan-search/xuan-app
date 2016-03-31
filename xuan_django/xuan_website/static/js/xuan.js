(function ($){
	//testing changes

	Xuan = {
		baseUrl:"",
		init: function(){
			this.baseUrl = (window.location&&window.location.origin?window.location.origin:"http://99xuan.com");
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
			
		}


		
	};

})(jQuery);


Xuan.ttsReader = {
	url : '/api/audio?src={0}&voice={1}&speed={2}',
	template: '<audio class="xs-tts-reader" controls autoplay type="audio/mpeg"></audio>',
	renderTo:function(el){
		if(!el.find(".xs-tts-reader").get(0)){
			//tts shouldn't exist on this page
			return;
		}
		this.audioEl = el.find(".xs-tts-reader");
		this.readerEl = el.find(".xs-tts-reader-voice");
		this.speedEl = el.find(".xs-tts-reader-speed");
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
		text = text.replace(/—/g, ",").replace(/;/g, ".");
    		return text;
	},

	getRequestUrl: function(){
		return Xuan.baseUrl+this.url.format(
			this.getSelectionText(),
			this.readerEl.val(),
			this.speedEl.val())
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
	}
};

$(document).ready(function(){
	Xuan.init();
	var hit = $(".xs-search-hit").first();
	if(hit.length){
		$("html, body").animate({
			scrollTop:hit.offset().top - $(".xs-navbar").height()
		});
	}
	var searchView = Xuan.View.SearchView.renderTo($("#search-form"));
	var ttsReader = Xuan.ttsReader.renderTo($(".xs-reader"));
	if(ttsReader){
		$(".xs-reader").find(".xs-tts-play").click(
			function(){
				ttsReader.loadData();
			});
	}
});
