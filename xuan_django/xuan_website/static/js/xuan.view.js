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
	resultDetailTemplate: "<span class='xs-book-details-fq'>The word <b>{0}</b> appears <b>{1}</b> times.</span><span class='xs-book-details-fq'>and appears in <b>{2}%</b> of the books in the database.</span><br/>",

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
		
	}
	
});
Xuan.View.SearchView = {
	searching: false,
	currentSearch: "",
	resultTemplate: "<li class='xs-book-info'>"+
						"<a href='/book/{0}?q={3}' class='xs-book-title'>{1}</a></br>"+
						//"<span class='xs-book-score'>Score:{2}</span>"+
						"<div class='xs-book-exerpts'>{2}</div>" +
					"</li>",
	renderTo: function(el){
		this.$el = el;
		this._listEl = $(".xs-search-results");
		$("#search-form").submit(this.submitSearch.bind(this));	
		return this;
	},
	renderSearchResult:function(hit){
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
		var resultItem = $(this.resultTemplate.format(hit._id, hit.fields.book_title[0]/*,hit._score*/,selectedExerpt,this.currentSearch)).appendTo(this._listEl);
		var detailView = new Xuan.View.SearchDetailsView({searchTerm:this.currentSearch, document:hit});
		detailView.renderTo(resultItem);
		//return ;
		
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
		$.ajax({
			url: Xuan.baseUrl + "/api/books?q="+this.currentSearch+
			"&exact="+$(".xs-exact").is(':checked')+
			"&match="+($(".xs-phrase").is(':checked')?"phrase":"word")
		}).success(this.showSearchResults.bind(this)).fail(this.searchFailure.bind(this));	
	}
};