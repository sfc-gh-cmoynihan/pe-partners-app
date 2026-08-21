app.controller('CallAnalyticsCtrl', ['$scope', '$http', '$sce', function($scope, $http, $sce) {
    $scope.companies = [];
    $scope.calls = [];
    $scope.selectedCompany = null;
    $scope.selectedCall = null;
    $scope.callDetail = null;
    $scope.loadingCalls = false;
    $scope.loadingDetail = false;

    $http.get('/api/calls/companies').then(function(resp) {
        $scope.companies = resp.data || [];
        var openai = $scope.companies.filter(function(c) { return c.COMPANY_NAME === 'OpenAI'; })[0];
        if (openai) {
            $scope.selectedCompany = openai.COMPANY_NAME;
            $scope.onCompanyChange();
        }
    });

    $scope.onCompanyChange = function() {
        $scope.calls = [];
        $scope.selectedCall = null;
        $scope.callDetail = null;
        if (!$scope.selectedCompany) return;
        $scope.loadingCalls = true;
        $http.get('/api/calls/by-company', { params: { company: $scope.selectedCompany } }).then(function(resp) {
            $scope.calls = resp.data || [];
            $scope.loadingCalls = false;
            if ($scope.calls.length > 0) {
                $scope.selectedCall = $scope.calls[0].CALL_ID;
                $scope.onCallChange();
            }
        }, function() {
            $scope.loadingCalls = false;
        });
    };

    var positiveWords = ['growth', 'remarkable', 'thrilled', 'exceeded', 'extraordinary', 'record',
        'improved', 'outstanding', 'phenomenal', 'transformative', 'incredible', 'excellent',
        'strong', 'confident', 'profitability', 'advantage', 'efficiency', 'gains',
        'innovation', 'exciting', 'opportunity', 'success', 'achievement', 'progress',
        'optimistic', 'momentum', 'robust', 'accelerating', 'impressive', 'tremendous'];

    function highlightPositive(text) {
        if (!text) return '';
        var escaped = text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
        escaped = escaped.replace(/\n/g, '<br>');
        var pattern = new RegExp('\\b(' + positiveWords.join('|') + ')\\b', 'gi');
        return escaped.replace(pattern, '<span class="highlight-positive">$1</span>');
    }

    $scope.onCallChange = function() {
        $scope.callDetail = null;
        $scope.highlightedTranscript = '';
        if (!$scope.selectedCall) return;
        $scope.loadingDetail = true;
        $http.get('/api/calls/' + $scope.selectedCall).then(function(resp) {
            $scope.callDetail = resp.data;
            $scope.highlightedTranscript = $sce.trustAsHtml(highlightPositive(resp.data.TRANSCRIPT));
            $scope.youtubeVideoId = resp.data.YOUTUBE_VIDEO_ID || null;
            $scope.youtubeEmbedUrl = $scope.youtubeVideoId ? $sce.trustAsResourceUrl('https://www.youtube.com/embed/' + $scope.youtubeVideoId) : null;
            $scope.loadingDetail = false;
        }, function() {
            $scope.loadingDetail = false;
        });
    };

    $scope.sentimentClass = function(sentiment) {
        if (!sentiment) return '';
        var s = sentiment.toLowerCase();
        if (s.indexOf('negative') !== -1) return 'sentiment-negative';
        if (s.indexOf('positive') !== -1 && s.indexOf('cautiously') === -1) return 'sentiment-positive';
        return 'sentiment-neutral';
    };

    // SENTIMENT_SCORE is stored on a -1..1 scale; display as a 0-100 score.
    $scope.scoreValue = function(score) {
        if (score === null || score === undefined) return '-';
        return Math.round(((score + 1) / 2) * 100);
    };

    $scope.scoreClass = function(score) {
        if (score === null || score === undefined) return 'sentiment-neutral';
        if (score >= 0.4) return 'sentiment-positive';
        if (score <= -0.1) return 'sentiment-negative';
        return 'sentiment-neutral';
    };
}]);
