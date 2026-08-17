app.controller('SearchCtrl', ['$scope', '$http', '$sce', function($scope, $http, $sce) {
    $scope.query = 'Funding round';
    $scope.searchResults = [];
    $scope.searching = false;
    $scope.searched = false;

    $scope.companies = [];
    $scope.filings = [];
    $scope.selectedTicker = '';
    $scope.selectedFilingId = '';
    $scope.activeFiling = null;

    $scope.showTranscript = false;
    $scope.loadingAnalysis = false;
    $scope.summaryText = '';
    $scope.sentimentResult = null;
    $scope.transcriptText = '';
    $scope.transcriptHtml = null;
    $scope.transcriptTruncated = false;
    $scope.analysisError = null;

    // Compact finance-oriented positive/negative word list for inline highlighting.
    var POSITIVE_WORDS = [
        'growth', 'grew', 'growing', 'strong', 'strength', 'record', 'increase', 'increased',
        'improved', 'improvement', 'profit', 'profitable', 'profitability', 'gain', 'gains',
        'success', 'successful', 'expand', 'expansion', 'robust', 'outperform', 'outperformed',
        'exceeded', 'exceed', 'beat', 'upgrade', 'upgraded', 'opportunity', 'opportunities',
        'innovation', 'innovative', 'leadership', 'leading', 'resilient', 'resilience',
        'efficient', 'efficiency', 'accelerate', 'accelerated', 'positive', 'favorable',
        'delivered', 'deliver', 'momentum', 'solid', 'healthy', 'demand', 'award', 'awarded',
        'partnership', 'milestone', 'breakthrough', 'recovery', 'rebound', 'stability',
        'stable', 'confident', 'confidence', 'advantage', 'advantageous'
    ];
    var NEGATIVE_WORDS = [
        'risk', 'risks', 'decline', 'declined', 'declining', 'loss', 'losses', 'litigation',
        'lawsuit', 'lawsuits', 'liability', 'liabilities', 'investigation', 'penalty',
        'penalties', 'fine', 'fines', 'weak', 'weakness', 'weakened', 'downgrade',
        'downgraded', 'shortfall', 'default', 'bankruptcy', 'impairment', 'write-off',
        'writedown', 'restructuring', 'layoff', 'layoffs', 'termination', 'terminated',
        'breach', 'violation', 'volatility', 'volatile', 'uncertainty', 'uncertain',
        'adverse', 'unfavorable', 'disruption', 'disrupted', 'delay', 'delayed', 'shortage',
        'recall', 'lawsuit', 'fraud', 'noncompliance', 'deficit', 'deteriorate',
        'deteriorated', 'downturn', 'recession', 'exposure', 'concern', 'concerns',
        'material weakness', 'going concern', 'churn', 'attrition'
    ];

    function escapeHtml(text) {
        return text
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;');
    }

    function buildWordRegex(words) {
        var escaped = words.slice().sort(function(a, b) { return b.length - a.length; })
            .map(function(w) { return w.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'); });
        return new RegExp('\\b(' + escaped.join('|') + ')\\b', 'gi');
    }
    var POS_RE = buildWordRegex(POSITIVE_WORDS);
    var NEG_RE = buildWordRegex(NEGATIVE_WORDS);

    function normalizeWhitespace(text) {
        return text.replace(/\s+/g, ' ').trim();
    }

    function highlightText(rawText) {
        var escaped = escapeHtml(normalizeWhitespace(rawText));
        escaped = escaped.replace(POS_RE, '<span style="color:#16a34a;font-weight:600;">$1</span>');
        escaped = escaped.replace(NEG_RE, '<span style="color:#dc2626;font-weight:600;">$1</span>');
        return escaped;
    }

    $scope.sentimentClass = function(sentiment) {
        if (!sentiment) return '';
        var s = sentiment.toLowerCase();
        if (s.indexOf('positive') !== -1) return 'sentiment-positive';
        if (s.indexOf('negative') !== -1) return 'sentiment-negative';
        return 'sentiment-neutral';
    };

    // Filings only carry categorical sentiment labels (no raw score), so derive
    // a representative 0-100 score from the "overall" category (or the first
    // category if "overall" isn't present) for a consistent score badge display.
    function overallCategory() {
        if (!$scope.sentimentResult || !$scope.sentimentResult.categories || !$scope.sentimentResult.categories.length) return null;
        var cats = $scope.sentimentResult.categories;
        var overall = cats.filter(function(c) { return (c.name || '').toLowerCase() === 'overall'; })[0];
        return overall || cats[0];
    }

    var LABEL_SCORE = { positive: 78, neutral: 50, mixed: 50, negative: 22 };

    $scope.overallSentimentScore = function() {
        var cat = overallCategory();
        if (!cat) return '-';
        var key = (cat.sentiment || '').toLowerCase();
        return LABEL_SCORE.hasOwnProperty(key) ? LABEL_SCORE[key] : 50;
    };

    $scope.overallSentimentLabel = function() {
        var cat = overallCategory();
        return cat ? cat.sentiment : 'Unknown';
    };

    $scope.overallSentimentClass = function() {
        return $scope.sentimentClass(($scope.overallSentimentLabel() || ''));
    };

    $http.get('/api/filings/companies').then(function(resp) {
        $scope.companies = resp.data || [];
        var openai = $scope.companies.filter(function(c) { return c.TICKER === 'OAIP'; })[0];
        if (openai) {
            $scope.selectedTicker = openai.TICKER;
            $scope.loadFilings();
        }
    });

    $scope.search = function() {
        if (!$scope.query.trim()) return;
        $scope.searching = true;
        $scope.searched = true;
        $http.post('/api/search', { query: $scope.query, limit: 10 }).then(function(resp) {
            $scope.searchResults = resp.data.results || [];
            $scope.searching = false;
        }, function() {
            $scope.searchResults = [];
            $scope.searching = false;
        });
    };

    $scope.loadFilings = function() {
        $scope.filings = [];
        $scope.selectedFilingId = '';
        $scope.activeFiling = null;
        if (!$scope.selectedTicker) return;
        $http.get('/api/filings', { params: { ticker: $scope.selectedTicker } }).then(function(resp) {
            $scope.filings = resp.data || [];
        });
    };

    $scope.selectFiling = function() {
        $scope.showTranscript = false;
        $scope.summaryText = '';
        $scope.sentimentResult = null;
        $scope.transcriptText = '';
        $scope.transcriptHtml = null;
        $scope.analysisError = null;
        $scope.activeFiling = $scope.filings.filter(function(f) { return String(f.FILING_ID) === String($scope.selectedFilingId); })[0] || null;
        if (!$scope.activeFiling) return;

        var filingId = $scope.activeFiling.FILING_ID;
        $scope.loadingAnalysis = true;

        $http.get('/api/filings/' + filingId + '/analysis').then(function(resp) {
            $scope.summaryText = resp.data.summary || 'No summary available.';
            $scope.sentimentResult = resp.data.sentiment || null;
        }, function() {
            $scope.analysisError = 'Precomputed analysis not available for this filing.';
        });

        $http.get('/api/filings/' + filingId + '/text').then(function(resp) {
            $scope.transcriptText = resp.data.text || 'No text available.';
            $scope.transcriptTruncated = !!resp.data.truncated;
            $scope.transcriptHtml = $sce.trustAsHtml(highlightText($scope.transcriptText));
        }).finally(function() {
            $scope.loadingAnalysis = false;
        });
    };

    $scope.search();
}]);
