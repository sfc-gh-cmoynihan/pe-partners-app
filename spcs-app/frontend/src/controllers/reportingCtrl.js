app.controller('ReportingCtrl', ['$scope', '$http', '$timeout', function($scope, $http, $timeout) {
    $scope.performance = [];
    $scope.funds = [];
    $scope.investments = [];
    $scope.customers = [];
    $scope.loading = true;
    $scope.selectedFundId = '';
    $scope.selectedFund = null;

    $scope.showEmailPanel = false;
    $scope.showSchedulePanel = false;
    $scope.emailRecipient = '';
    $scope.emailStatus = null;
    $scope.emailSending = false;

    $scope.schedule = { frequency: 'MONTHLY', day_of_week: 1, day_of_month: 1, hour: 8, minute: 0, recipient: '' };
    $scope.schedules = [];
    $scope.scheduleStatus = null;
    $scope.scheduleSaving = false;

    var returnsChart = null;
    var roicChart = null;

    $http.get('/api/funds').then(function(resp) {
        $scope.funds = resp.data;
        var defaultFund = resp.data[0];
        if (defaultFund && !$scope.selectedFundId) {
            $scope.selectedFundId = String(defaultFund.FUND_ID);
            $scope.selectedFund = defaultFund;
        }
        tryBuildCharts();
    });

    $http.get('/api/performance').then(function(resp) {
        $scope.allPerformance = resp.data;
        $scope.performance = resp.data;
        $scope.loading = false;
        tryBuildCharts();
    });

    $http.get('/api/investments').then(function(resp) {
        $scope.allInvestments = resp.data;
        $scope.investments = resp.data;
    });

    $http.get('/api/customers').then(function(resp) {
        $scope.customers = resp.data;
        $scope.totalCommitments = resp.data.reduce(function(s, c) { return s + (c.AUM_COMMITMENT_GBP || 0); }, 0);
    });

    loadSchedules();

    function tryBuildCharts() {
        if ($scope.funds.length && $scope.allPerformance) {
            if ($scope.selectedFundId) {
                $scope.loadPerformance();
            } else {
                $timeout(function() { buildReturnsChart(); buildRoicChart(); }, 100);
            }
        }
    }

    function latestPerformanceByFund() {
        var latest = {};
        ($scope.allPerformance || []).forEach(function(p) {
            var fid = p.FUND_ID;
            if (!latest[fid] || p.REPORTING_DATE > latest[fid].REPORTING_DATE) latest[fid] = p;
        });
        return latest;
    }

    var FUND_PALETTE = ['#6366f1', '#f59e0b', '#10b981', '#ef4444', '#8b5cf6', '#ec4899', '#14b8a6', '#f97316', '#06b6d4', '#84cc16'];

    function barColors(values, highlightId, ids) {
        return values.map(function(v, idx) {
            if (highlightId && ids && ids[idx] === highlightId) return '#1d4ed8';
            return FUND_PALETTE[idx % FUND_PALETTE.length];
        });
    }

    function buildReturnsChart() {
        var ctx = document.getElementById('returnsChart');
        if (!ctx) return;
        if (returnsChart) returnsChart.destroy();

        var labels, data, title, ids = null;
        if ($scope.selectedFundId) {
            var id = parseInt($scope.selectedFundId);
            var rows = $scope.allPerformance.filter(function(p) { return p.FUND_ID === id; })
                .sort(function(a, b) { return new Date(a.REPORTING_DATE) - new Date(b.REPORTING_DATE); })
                .slice(-12);
            labels = rows.map(function(r) { return r.REPORTING_DATE; });
            data = rows.map(function(r) { return r.MONTHLY_RETURN_PCT; });
            title = 'Monthly Returns';
        } else {
            var latest = latestPerformanceByFund();
            var rows2 = Object.keys(latest).map(function(k) { return latest[k]; })
                .sort(function(a, b) { return a.FUND_NAME.localeCompare(b.FUND_NAME); });
            labels = rows2.map(function(r) { return r.FUND_NAME; });
            data = rows2.map(function(r) { return r.YTD_RETURN_PCT; });
            ids = rows2.map(function(r) { return r.FUND_ID; });
            title = 'YTD Returns by Fund';
        }

        returnsChart = new Chart(ctx, {
            type: 'bar',
            data: { labels: labels, datasets: [{ label: title, data: data, backgroundColor: barColors(data, null, ids), borderRadius: 4 }] },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: { callbacks: { label: function(c) { return c.parsed.y.toFixed(2) + '%'; } } }
                },
                scales: {
                    y: { ticks: { callback: function(v) { return v + '%'; } }, grid: { color: 'rgba(0,0,0,0.05)' } },
                    x: { grid: { display: false } }
                },
                onClick: function(evt, elements) {
                    if (!$scope.selectedFundId && elements.length && ids) {
                        var idx = elements[0].index;
                        $scope.$apply(function() {
                            $scope.selectedFundId = String(ids[idx]);
                            $scope.loadPerformance();
                        });
                    }
                }
            }
        });
    }

    function buildRoicChart() {
        var ctx = document.getElementById('roicChart');
        if (!ctx) return;
        if (roicChart) roicChart.destroy();

        var latest = latestPerformanceByFund();
        var rows = Object.keys(latest).map(function(k) { return latest[k]; })
            .sort(function(a, b) { return a.FUND_NAME.localeCompare(b.FUND_NAME); });
        var labels = rows.map(function(r) { return r.FUND_NAME; });
        var data = rows.map(function(r) { return r.YTD_RETURN_PCT; });
        var ids = rows.map(function(r) { return r.FUND_ID; });
        var highlightId = $scope.selectedFundId ? parseInt($scope.selectedFundId) : null;

        roicChart = new Chart(ctx, {
            type: 'bar',
            data: { labels: labels, datasets: [{ label: 'ROIC (YTD)', data: data, backgroundColor: barColors(data, highlightId, ids), borderRadius: 4 }] },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: { callbacks: { label: function(c) { return 'ROIC (YTD): ' + c.parsed.y.toFixed(2) + '%'; } } }
                },
                scales: {
                    y: { ticks: { callback: function(v) { return v + '%'; } }, grid: { color: 'rgba(0,0,0,0.05)' } },
                    x: { grid: { display: false } }
                },
                onClick: function(evt, elements) {
                    if (elements.length) {
                        var idx = elements[0].index;
                        $scope.$apply(function() {
                            $scope.selectedFundId = String(ids[idx]);
                            $scope.loadPerformance();
                        });
                    }
                }
            }
        });
    }

    $scope.loadPerformance = function() {
        $scope.selectedFund = null;
        if ($scope.selectedFundId) {
            var id = parseInt($scope.selectedFundId);
            $scope.performance = $scope.allPerformance.filter(function(p) { return p.FUND_ID === id; });
            $scope.investments = ($scope.allInvestments || []).filter(function(i) { return i.FUND_ID === id; });
            $scope.selectedFund = $scope.funds.filter(function(f) { return f.FUND_ID === id; })[0] || null;
        } else {
            $scope.performance = $scope.allPerformance;
            $scope.investments = $scope.allInvestments;
        }
        $timeout(function() { buildReturnsChart(); buildRoicChart(); }, 100);
    };

    $scope.toggleEmailPanel = function() {
        $scope.showEmailPanel = !$scope.showEmailPanel;
        $scope.showSchedulePanel = false;
        $scope.emailStatus = null;
    };

    $scope.toggleSchedulePanel = function() {
        $scope.showSchedulePanel = !$scope.showSchedulePanel;
        $scope.showEmailPanel = false;
        $scope.scheduleStatus = null;
    };

    $scope.downloadPdf = function() {
        var url = '/api/reports/pdf' + ($scope.selectedFundId ? '?fund_id=' + $scope.selectedFundId : '');
        window.open(url, '_blank');
    };

    $scope.sendEmailReport = function() {
        if (!$scope.emailRecipient || !$scope.selectedFundId) {
            $scope.emailStatus = { ok: false, msg: 'Select a fund and enter a recipient email.' };
            return;
        }
        $scope.emailSending = true;
        $scope.emailStatus = null;
        $http.post('/api/reports/email', { fund_id: $scope.selectedFundId, recipient: $scope.emailRecipient })
            .then(function() {
                $scope.emailStatus = { ok: true, msg: 'Report emailed to ' + $scope.emailRecipient + '.' };
            })
            .catch(function(resp) {
                $scope.emailStatus = { ok: false, msg: (resp.data && resp.data.error) || 'Failed to send email.' };
            })
            .finally(function() { $scope.emailSending = false; });
    };

    function loadSchedules() {
        $http.get('/api/reports/schedules').then(function(resp) { $scope.schedules = resp.data; });
    }

    $scope.addSchedule = function() {
        if (!$scope.selectedFundId || !$scope.schedule.recipient) {
            $scope.scheduleStatus = { ok: false, msg: 'Select a fund and enter a recipient email.' };
            return;
        }
        $scope.scheduleSaving = true;
        $scope.scheduleStatus = null;
        var payload = angular.extend({}, $scope.schedule, {
            fund_id: $scope.selectedFundId,
            fund_name: $scope.selectedFund ? $scope.selectedFund.FUND_NAME : 'All Funds'
        });
        $http.post('/api/reports/schedule', payload)
            .then(function() {
                $scope.scheduleStatus = { ok: true, msg: 'Schedule created.' };
                loadSchedules();
            })
            .catch(function(resp) {
                $scope.scheduleStatus = { ok: false, msg: (resp.data && resp.data.error) || 'Failed to create schedule.' };
            })
            .finally(function() { $scope.scheduleSaving = false; });
    };

    $scope.deleteSchedule = function(s) {
        $http.delete('/api/reports/schedule/' + s.SCHEDULE_ID).then(function() { loadSchedules(); });
    };

    $scope.$on('$destroy', function() {
        if (returnsChart) returnsChart.destroy();
        if (roicChart) roicChart.destroy();
    });
}]);
