app.controller('CallsCtrl', ['$scope', '$http', function($scope, $http) {
    $scope.query = '';
    $scope.results = [];
    $scope.searching = false;
    $scope.searched = false;

    $scope.search = function() {
        if (!$scope.query.trim()) return;
        $scope.searching = true;
        $scope.searched = true;
        $http.post('/api/search/calls', { query: $scope.query }).then(function(resp) {
            $scope.results = resp.data.results || [];
            $scope.searching = false;
        }, function() {
            $scope.results = [];
            $scope.searching = false;
        });
    };
}]);
