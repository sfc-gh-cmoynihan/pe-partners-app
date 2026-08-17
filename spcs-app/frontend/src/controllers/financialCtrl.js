app.controller('FinancialCtrl', ['$scope', '$http', '$timeout', function($scope, $http, $timeout) {
    $scope.funds = [];
    $scope.investments = [];
    $scope.loadingFunds = true;
    $scope.loadingInvestments = true;
    $scope.selectedFundId = null;
    $scope.totalAUM = 0;
    $scope.drillFund = null;

    var aumChart = null;
    var sectorChart = null;
    var weightChart = null;

    var strategyColors = {
        'Growth Equity': '#3b82f6',
        'Venture Capital': '#8b5cf6',
        'Infrastructure': '#f59e0b',
        'Applications': '#10b981',
        'Multi-Strategy': '#ef4444',
        'Long/Short Equity': '#0ea5e9',
        'Global Macro': '#6366f1',
        'Event Driven': '#f97316',
        'Credit': '#ec4899'
    };

    $http.get('/api/funds').then(function(resp) {
        $scope.funds = resp.data;
        $scope.totalAUM = resp.data.reduce(function(s, f) { return s + (f.TOTAL_AUM_GBP || 0); }, 0);
        $scope.loadingFunds = false;
        tryBuildCharts();
    });

    $http.get('/api/investments').then(function(resp) {
        $scope.allInvestments = resp.data;
        $scope.investments = resp.data;
        $scope.loadingInvestments = false;
        tryBuildCharts();
    });

    function tryBuildCharts() {
        if (!$scope.loadingFunds && !$scope.loadingInvestments) {
            $timeout(function() { buildAumChart(); }, 100);
        }
    }

    function buildAumChart() {
        var ctx = document.getElementById('aumChart');
        if (!ctx) return;
        if (aumChart) aumChart.destroy();

        var labels = $scope.funds.map(function(f) { return f.FUND_NAME; });
        var data = $scope.funds.map(function(f) { return f.TOTAL_AUM_GBP / 1e6; });
        var colors = $scope.funds.map(function(f) { return strategyColors[f.STRATEGY] || '#6b7280'; });

        aumChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'AUM ($M)',
                    data: data,
                    backgroundColor: colors,
                    borderRadius: 4
                }]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                onClick: function(e, elements) {
                    if (elements.length > 0) {
                        var idx = elements[0].index;
                        $scope.$apply(function() {
                            $scope.drillDown($scope.funds[idx]);
                        });
                    }
                },
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label: function(ctx) { return '$' + ctx.parsed.x.toFixed(1) + 'M'; }
                        }
                    }
                },
                scales: {
                    x: {
                        ticks: { callback: function(v) { return '$' + v + 'M'; } },
                        grid: { color: 'rgba(255,255,255,0.05)' }
                    },
                    y: { grid: { display: false } }
                }
            }
        });
    }

    $scope.drillDown = function(fund) {
        $scope.drillFund = fund;
        $scope.selectedFundId = String(fund.FUND_ID);
        $scope.loadInvestments();
        $timeout(function() {
            buildSectorChart(fund);
            buildWeightChart(fund);
        }, 100);
    };

    $scope.backToAllFunds = function() {
        $scope.drillFund = null;
        $scope.selectedFundId = '';
        $scope.loadInvestments();
        if (sectorChart) { sectorChart.destroy(); sectorChart = null; }
        if (weightChart) { weightChart.destroy(); weightChart = null; }
        $timeout(function() { buildAumChart(); }, 100);
    };

    function buildSectorChart(fund) {
        var ctx = document.getElementById('sectorChart');
        if (!ctx) return;
        if (sectorChart) sectorChart.destroy();

        var positions = $scope.allInvestments.filter(function(i) { return i.FUND_ID === fund.FUND_ID; });
        var sectors = {};
        positions.forEach(function(p) {
            if (!sectors[p.SECTOR]) sectors[p.SECTOR] = { long: 0, short: 0 };
            if (p.POSITION_TYPE === 'LONG') sectors[p.SECTOR].long += p.MARKET_VALUE_GBP / 1e6;
            else sectors[p.SECTOR].short += Math.abs(p.MARKET_VALUE_GBP) / 1e6;
        });

        var labels = Object.keys(sectors);
        var longData = labels.map(function(s) { return sectors[s].long; });
        var shortData = labels.map(function(s) { return sectors[s].short; });

        sectorChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [
                    { label: 'Long', data: longData, backgroundColor: '#10b981', borderRadius: 3 },
                    { label: 'Short', data: shortData, backgroundColor: '#ef4444', borderRadius: 3 }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    tooltip: {
                        callbacks: {
                            label: function(ctx) { return ctx.dataset.label + ': $' + ctx.parsed.y.toFixed(1) + 'M'; }
                        }
                    }
                },
                scales: {
                    y: {
                        ticks: { callback: function(v) { return '$' + v + 'M'; } },
                        grid: { color: 'rgba(255,255,255,0.05)' }
                    },
                    x: { grid: { display: false } }
                }
            }
        });
    }

    function buildWeightChart(fund) {
        var ctx = document.getElementById('weightChart');
        if (!ctx) return;
        if (weightChart) weightChart.destroy();

        var positions = $scope.allInvestments
            .filter(function(i) { return i.FUND_ID === fund.FUND_ID; })
            .sort(function(a, b) { return b.WEIGHT_PCT - a.WEIGHT_PCT; });

        var labels = positions.map(function(p) { return p.TICKER || p.SECURITY_NAME; });
        var data = positions.map(function(p) { return p.WEIGHT_PCT; });
        var colors = positions.map(function(p) { return p.POSITION_TYPE === 'LONG' ? '#3b82f6' : '#ef4444'; });

        weightChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Weight %',
                    data: data,
                    borderColor: '#3b82f6',
                    backgroundColor: 'rgba(59,130,246,0.1)',
                    fill: true,
                    tension: 0.3,
                    pointBackgroundColor: colors,
                    pointRadius: 5,
                    pointHoverRadius: 7
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    tooltip: {
                        callbacks: {
                            label: function(ctx) { return ctx.parsed.y.toFixed(2) + '%'; }
                        }
                    }
                },
                scales: {
                    y: {
                        ticks: { callback: function(v) { return v + '%'; } },
                        grid: { color: 'rgba(255,255,255,0.05)' }
                    },
                    x: {
                        ticks: { maxRotation: 45 },
                        grid: { display: false }
                    }
                }
            }
        });
    }

    $scope.loadInvestments = function() {
        if ($scope.selectedFundId) {
            var id = parseInt($scope.selectedFundId);
            $scope.investments = $scope.allInvestments.filter(function(i) { return i.FUND_ID === id; });
        } else {
            $scope.investments = $scope.allInvestments;
        }
    };

    $scope.$on('$destroy', function() {
        if (aumChart) aumChart.destroy();
        if (sectorChart) sectorChart.destroy();
        if (weightChart) weightChart.destroy();
    });
}]);
