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

    $scope.onCallChange = function() {
        $scope.callDetail = null;
        if (!$scope.selectedCall) return;
        $scope.loadingDetail = true;
        $http.get('/api/calls/' + $scope.selectedCall).then(function(resp) {
            $scope.callDetail = resp.data;
            $scope.videoUrl = '/api/calls/' + $scope.selectedCall + '/video';
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
