app.controller('CustomerCtrl', ['$scope', '$http', function($scope, $http) {
    $scope.customers = [];
    $scope.loading = true;
    $scope.sortField = 'AUM_COMMITMENT_GBP';
    $scope.sortReverse = true;
    $scope.totalAUM = 0;
    $scope.activeCount = 0;
    $scope.avgCommitment = 0;

    $http.get('/api/customers').then(function(resp) {
        $scope.customers = resp.data;
        $scope.totalAUM = resp.data.reduce(function(s, c) { return s + (c.AUM_COMMITMENT_GBP || 0); }, 0);
        $scope.activeCount = resp.data.filter(function(c) { return c.STATUS === 'Active'; }).length;
        $scope.avgCommitment = resp.data.length > 0 ? $scope.totalAUM / resp.data.length : 0;
        $scope.loading = false;
    });

    $scope.sortBy = function(field) {
        if ($scope.sortField === field) { $scope.sortReverse = !$scope.sortReverse; }
        else { $scope.sortField = field; $scope.sortReverse = false; }
    };
}]);
