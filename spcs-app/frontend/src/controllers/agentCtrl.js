app.controller('AgentCtrl', ['$scope', '$http', function($scope, $http) {
    $scope.messages = [];
    $scope.input = '';
    $scope.sending = false;
    $scope.today = new Date();

    $scope.models = [
        'claude-sonnet-5',
        'claude-opus-4-8',
        'claude-sonnet-4-6',
        'claude-opus-4-6',
        'gemini-3.1-pro',
        'llama4-maverick',
        'llama3.1-8b',
        'openai-gpt-5.2',
        'openai-gpt-5.4-mini',
        'mistral-large2',
        'mixtral-8x7b'
    ];
    $scope.agent = { selectedModel: 'claude-sonnet-5' };

    $http.get('/api/models').then(function(resp) {
        if (resp.data && resp.data.length > 0) {
            $scope.models = resp.data;
            if ($scope.models.indexOf($scope.agent.selectedModel) === -1) {
                $scope.agent.selectedModel = $scope.models[0];
            }
        }
    });

    $scope.sampleQuestions = [
        'What is the total AUM across all funds?',
        'Which fund has the highest Sharpe ratio?',
        'Show me all short positions in the portfolio',
        'Which investors are sovereign wealth funds?',
        'What is the YTD return for the Macro Fund?',
        'Who are our top 5 investors by commitment?',
        'What is the average maximum drawdown across funds?',
        'Which sectors have the largest long exposure?',
        'Compare the volatility of all funds this quarter',
        'List all investors from the Middle East region'
    ];

    $scope.askSample = function(q) {
        $scope.input = q;
        $scope.send();
    };

    $scope.send = function() {
        if (!$scope.input.trim() || $scope.sending) return;

        var userMsg = $scope.input.trim();
        $scope.messages.push({ role: 'user', content: userMsg });
        $scope.input = '';
        $scope.sending = true;

        var messagesPayload = [{ role: 'user', content: userMsg }];
        var modelUsed = $scope.agent.selectedModel;

        $http.post('/api/agent', { messages: messagesPayload, model: modelUsed }).then(function(resp) {
            $scope.messages.push({
                role: 'assistant',
                content: resp.data.response || 'No response.',
                model: modelUsed,
                timestamp: new Date()
            });
            $scope.sending = false;
        }, function(err) {
            $scope.messages.push({
                role: 'assistant',
                content: 'Error: ' + (err.data && err.data.error || 'Unknown error'),
                model: modelUsed,
                timestamp: new Date()
            });
            $scope.sending = false;
        });
    };
}]);
