app.controller('CustomerCtrl', ['$scope', '$http', function($scope, $http) {
    $scope.customers = [];
    $scope.allCustomers = [];
    $scope.loading = true;
    $scope.sortField = 'AUM_COMMITMENT_GBP';
    $scope.sortReverse = true;
    $scope.totalAUM = 0;
    $scope.activeCount = 0;
    $scope.avgCommitment = 0;
    $scope.filters = {
        investor_type: '',
        region: '',
        status: ''
    };

    $http.get('/api/customers').then(function(resp) {
        $scope.allCustomers = resp.data;
        $scope.loadData();
        $scope.loading = false;
    });

    $scope.loadData = function() {
        $scope.customers = $scope.allCustomers.filter(function(customer) {
            if ($scope.filters.investor_type && customer.INVESTOR_TYPE !== $scope.filters.investor_type) return false;
            if ($scope.filters.region && customer.REGION !== $scope.filters.region) return false;
            if ($scope.filters.status && customer.STATUS !== $scope.filters.status) return false;
            return true;
        });

        $scope.totalAUM = $scope.customers.reduce(function(sum, customer) {
            return sum + (customer.AUM_COMMITMENT_GBP || 0);
        }, 0);
        $scope.activeCount = $scope.customers.filter(function(customer) {
            return customer.STATUS === 'Active';
        }).length;
        $scope.avgCommitment = $scope.customers.length > 0 ? $scope.totalAUM / $scope.customers.length : 0;
    };

    $scope.sortBy = function(field) {
        if ($scope.sortField === field) { $scope.sortReverse = !$scope.sortReverse; }
        else { $scope.sortField = field; $scope.sortReverse = false; }
    };
}]);
