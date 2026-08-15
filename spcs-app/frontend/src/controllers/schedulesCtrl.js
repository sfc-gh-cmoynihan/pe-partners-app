app.controller('SchedulesCtrl', ['$scope', '$http', function($scope, $http) {
    $scope.schedules = [];
    $scope.funds = [];
    $scope.loading = true;
    $scope.createError = '';
    $scope.createSuccess = '';
    $scope.schedule = { frequency: 'MONTHLY', day_of_week: '1', day_of_month: 1, hour: 8, minute: 0, recipient: '' };
    $scope.hours = Array.from({length: 24}, function(_, i) { return i; });
    $scope.minutes = [0, 15, 30, 45];
    $scope.daysOfMonth = Array.from({length: 28}, function(_, i) { return i + 1; });

    function loadSchedules() {
        $http.get('/api/reports/schedules').then(function(resp) {
            $scope.schedules = resp.data;
            $scope.loading = false;
        }, function() { $scope.loading = false; });
    }

    function loadFunds() {
        $http.get('/api/funds').then(function(resp) { $scope.funds = resp.data; });
    }

    loadSchedules();
    loadFunds();

    $scope.addSchedule = function() {
        $scope.createError = '';
        $scope.createSuccess = '';
        if (!$scope.schedule.recipient) {
            $scope.createError = 'Recipient email is required.';
            return;
        }
        var fund = $scope.funds.find(function(f) { return f.FUND_ID === $scope.schedule.fund_id; });
        var payload = {
            fund_id: $scope.schedule.fund_id || null,
            fund_name: fund ? fund.FUND_NAME : 'All Funds',
            recipient: $scope.schedule.recipient,
            frequency: $scope.schedule.frequency,
            day_of_week: parseInt($scope.schedule.day_of_week),
            day_of_month: $scope.schedule.day_of_month,
            hour: $scope.schedule.hour,
            minute: $scope.schedule.minute
        };
        $http.post('/api/reports/schedule', payload).then(function() {
            $scope.createSuccess = 'Schedule created successfully.';
            $scope.schedule.recipient = '';
            loadSchedules();
        }, function(err) {
            $scope.createError = (err.data && err.data.detail) || 'Failed to create schedule.';
        });
    };

    $scope.deleteSchedule = function(s) {
        if (!confirm('Delete schedule for ' + (s.FUND_NAME || 'All Funds') + ' → ' + s.RECIPIENT_EMAIL + '?')) return;
        $http.delete('/api/reports/schedule/' + s.SCHEDULE_ID).then(function() {
            loadSchedules();
        }, function(err) {
            alert('Failed to delete: ' + ((err.data && err.data.detail) || 'Unknown error'));
        });
    };
}]);
