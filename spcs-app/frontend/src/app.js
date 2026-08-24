var APP_VERSION = 'v4.1';
var app = angular.module('peApp', ['ngRoute']);

app.config(['$routeProvider', function($routeProvider) {
    $routeProvider
        .when('/investors', { templateUrl: 'views/customer.html?v=' + APP_VERSION, controller: 'CustomerCtrl' })
        .when('/financial', { templateUrl: 'views/financial.html?v=' + APP_VERSION, controller: 'FinancialCtrl' })
        .when('/reporting', { templateUrl: 'views/reporting.html?v=' + APP_VERSION, controller: 'ReportingCtrl' })
        .when('/search', { templateUrl: 'views/search.html?v=' + APP_VERSION, controller: 'SearchCtrl' })
        .when('/calls', { templateUrl: 'views/calls.html?v=' + APP_VERSION, controller: 'CallsCtrl' })
        .when('/call-analytics', { templateUrl: 'views/callAnalytics.html?v=' + APP_VERSION, controller: 'CallAnalyticsCtrl' })
        .when('/agent', { templateUrl: 'views/agent.html?v=' + APP_VERSION, controller: 'AgentCtrl' })
        .when('/schedules', { templateUrl: 'views/schedules.html?v=' + APP_VERSION, controller: 'SchedulesCtrl' })
        .otherwise({ redirectTo: '/investors' });
}]);

app.run(['$rootScope', '$location', '$http', function($rootScope, $location, $http) {
    $rootScope.isActive = function(path) {
        return $location.path() === path;
    };
    $rootScope.go = function(path) {
        $location.path(path);
    };

    $rootScope.loginTime = new Date().toLocaleString('en-US', {day:'2-digit', month:'short', year:'numeric', hour:'2-digit', minute:'2-digit'});
    $rootScope.currentUser = '';
    $rootScope.logout = function() {
        window.location.href = '/logout';
    };
    $http.get('/api/user/role').then(function(resp) {
        $rootScope.currentUser = resp.data.user || 'Unknown';
    });
}]);

app.filter('gbpCurrency', function() {
    return function(value) {
        if (value === null || value === undefined) return '-';
        var num = parseFloat(value);
        if (num >= 1e12) return '$' + (num / 1e12).toFixed(1) + ' Trillion';
        if (num >= 1e9) return 'USD ' + (num / 1e9).toFixed(2) + 'bn';
        if (num >= 1e6) return 'USD ' + (num / 1e6).toFixed(1) + 'm';
        if (num >= 1e3) return 'USD ' + (num / 1e3).toFixed(0) + 'k';
        return 'USD ' + num.toFixed(0);
    };
});

app.filter('pct', function() {
    return function(value) {
        if (value === null || value === undefined) return '-';
        return parseFloat(value).toFixed(2) + '%';
    };
});
