(function ($,$$){
	Xuan.View = {};

	
})(jQuery);
Xuan.View.SearchDetailsView = function(options){
	this.searchTerm = options.searchTerm.toLowerCase();
	this.document = options.document;
	return this;
}
$.extend(Xuan.View.SearchDetailsView.prototype,
{
	resultTemplate: "<div class='xs-book-details'>"+
						"<a class='xs-book-details-link'>Show Details</a>"+
						"<div class='xs-book-details-content'></div>"+
					"</div>",
	resultDetailTemplate: "<span class='xs-book-details-fq'>The word <b>{0}</b> "+
							"appears <b>{1}</b> times.</span><span class='xs-book-details-fq'>"+
							"and appears in <b>{2}%</b> of the books in the database.</span><br/>",
	resultDifficultyTemplate: "<span class='xs-book-details-fq'>This book level is <b>{0}</b> "+
						"in difficulty (when calculated by Method 3) and contains <b>{1}</b> tokens.</span><br/>",

	renderTo: function(el){
		this.$el = $(this.resultTemplate).appendTo(el);
		this.contentToggleEl = this.$el.find('.xs-book-details-link').first();
		this.contentEl = this.$el.find('.xs-book-details-content').first();
		this.contentToggleEl.click(this.loadContent.bind(this));
		return this;
	},
	loadContent:function(){
		if(this.detailData){
			this.showContent(this.detailData);
		}
		$.ajax({
			url: Xuan.baseUrl + "/api/book_info?id="+this.document._id
		}).success(this.showContent.bind(this));	
		
	},
	showContent:function(data){
		this.detailData = data;

		ga('send', 'event', 'Search', this.document._id, 'Show Details');
		var words = this.searchTerm.split(' '); 
		var wordObjects = [];
		this.contentEl.html("");
		for(var wordpair in data.frequency_counts){
			for (var i in words){
				if(data.frequency_counts[wordpair].word.toLowerCase()==words[i]){
					wordObjects.push(data.frequency_counts[wordpair]);
				}
			}
		}
		for(var i = 0; i < words.length;i++){
			var word;
			for(var q = 0; q < wordObjects.length;q++){
				if(wordObjects[q].word==words[i]){
					word = wordObjects[q];
					break;
				}
			}
			if(word){
				this.contentEl.append(this.resultDetailTemplate.format(word.word, word.count, Math.round((word.percentile?word.percentile:0)*100)));
			}else{
				this.contentEl.append(this.resultDetailTemplate.format(words[i], 0, 0));
			}
		}
		this.contentEl.append(
			this.resultDifficultyTemplate.format(
			(data.difficulty_by_percentile?data.difficulty_by_percentile:"not calculated"),
			(data.tokens_count?data.tokens_count:"uncounted"))
		);
		
	}
	
});
Xuan.View.SearchView = {
	searching: false,
	currentSearch: "",
	resultTemplate: "<li class='xs-book-info'>"+
						"<a href='/book/{0}?q={3}' class='xs-book-title'>{1}</a></br>"+
						//"<span class='xs-book-score'>Score:{2}</span>"+
						"<section class='xs-book-exerpts'>{2}</section>" +
					"</li>",
	renderTo: function(el){
		this.$el = el;
		this._listEl = $(".xs-search-results");
		$("#search-form").submit(this.submitSearch.bind(this));	
		$(".xs-search-difficulty-select").change(this.toggleFields);
		return this;
	},
	renderSearchResult:function(hit){
		var selectedExerpt;
		
		if(hit.highlight.html_body)
			selectedExerpt = hit.highlight.html_body[0];
		else{
			selectedExerpt = hit.highlight['html_body.tokens'][0];
		}
		for(var i in hit.highlight.html_body){
			var testString = hit.highlight.html_body[i];
			var openTagStart = testString.match(/<[^/^e]/g);
			var closeTagStart = testString.match(/<[/][^e]/g);
			var tagEnd = testString.match(/[^m]>/g);
			if(!openTagStart && !closeTagStart && !tagEnd){
				if(hit.highlight.html_body)
					selectedExerpt = hit.highlight.html_body[i];
				else{
					selectedExerpt = hit.highlight['html_body.tokens'][i];
				}
				break;
			}
		}
		var resultItem = $(this.resultTemplate.format(hit._id, hit.fields.book_title[0]/*,hit._score*/,selectedExerpt,this.currentSearch)).appendTo(this._listEl);
		var detailView = new Xuan.View.SearchDetailsView({searchTerm:this.currentSearch, document:hit});
		detailView.renderTo(resultItem);
		//return ;
		
	},
	toggleFields:function(e){

		ga('send', 'event', 'Search', $(this).val(), 'Difficulty Changed');
		$(".xs-search-difficulty-fields").attr("disabled", $(this).val()===""||!$(this).val());
	},
	showSearchResults:function (data){
		$('.xs-body-container').toggleClass('loaded');
		this._listEl.html("");
		var hits = data.hits.hits;
		for(ind in hits){
			this.renderSearchResult(hits[ind]);
		
		}
		this.searching = false;
	},	
	searchFailure:function (e){
		$('.xs-body-container').toggleClass('loaded');
		this.searching = false;
		alert("search failed: "+e);
	},
	submitSearch:function (e){
		e.preventDefault();
		if(this.searching)return;
		this.searching = true;
		this.currentSearch = $("#searchterms").val();
		$('.xs-body-container').toggleClass('loaded');
		ga('send', 'event', 'Search', this.currentSearch, 'Search Made');
		$.ajax({
			url: Xuan.baseUrl + "/api/books?q="+this.currentSearch+
			"&exact="+$(".xs-exact").is(':checked')+
			"&match="+($(".xs-phrase").is(':checked')?"phrase":"word")+
			"&difficulty="+($(".xs-search-difficulty-select").val())+
			"&from_difficulty="+($(".from-difficulty").val())/*+
			"&to_difficulty="+($(".to-difficulty").val())*/
		}).success(this.showSearchResults.bind(this)).fail(this.searchFailure.bind(this));	
	}
};