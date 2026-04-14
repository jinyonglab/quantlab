let chart = null;

document.getElementById('run-backtest').addEventListener('click', runBacktest);
document.getElementById('load-hs300').addEventListener('click', loadHs300);

async function loadHs300() {
    try {
        const response = await fetch('/api/stocks');
        const data = await response.json();
        if (data.success) {
            document.getElementById('symbols').value = data.symbols.join(',');
        }
    } catch (error) {
        console.error('Failed to load HS300:', error);
    }
}

async function runBacktest() {
    const btn = document.getElementById('run-backtest');
    const loading = document.getElementById('loading');
    const resultsPanel = document.getElementById('results-panel');
    
    btn.disabled = true;
    loading.style.display = 'block';
    resultsPanel.style.display = 'block';
    
    const requestData = {
        strategy: document.getElementById('strategy').value,
        symbols: document.getElementById('symbols').value.split(',').map(s => s.trim()),
        start_date: document.getElementById('start_date').value,
        end_date: document.getElementById('end_date').value,
        initial_capital: parseFloat(document.getElementById('initial_capital').value),
        use_mock: document.getElementById('use_mock').checked
    };
    
    try {
        const response = await fetch('/api/backtest', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestData)
        });
        
        const data = await response.json();
        
        if (data.success) {
            displayResults(data.result);
        } else {
            alert('回测失败: ' + (data.error || '未知错误'));
        }
    } catch (error) {
        console.error('Backtest failed:', error);
        alert('回测请求失败');
    } finally {
        btn.disabled = false;
        loading.style.display = 'none';
    }
}

function displayResults(result) {
    document.getElementById('total-return').textContent = result.total_return;
    document.getElementById('annual-return').textContent = result.annual_return;
    document.getElementById('sharpe-ratio').textContent = result.sharpe_ratio;
    document.getElementById('max-drawdown').textContent = result.max_drawdown;
    document.getElementById('total-trades').textContent = result.total_trades;
    document.getElementById('win-rate').textContent = result.win_rate;
    
    if (result.equity_curve && result.equity_curve.length > 0) {
        renderChart(result.equity_curve);
    }
}

function renderChart(equityCurve) {
    const ctx = document.getElementById('equity-chart').getContext('2d');
    
    const dates = equityCurve.map(item => item.date);
    const values = equityCurve.map(item => item.value);
    
    if (chart) {
        chart.destroy();
    }
    
    chart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: dates,
            datasets: [{
                label: '账户净值',
                data: values,
                borderColor: '#00d4ff',
                backgroundColor: 'rgba(0, 212, 255, 0.1)',
                fill: true,
                tension: 0.4,
                pointRadius: 0,
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    titleColor: '#fff',
                    bodyColor: '#00d4ff'
                }
            },
            scales: {
                x: {
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    },
                    ticks: {
                        color: '#888',
                        maxTicksLimit: 10
                    }
                },
                y: {
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    },
                    ticks: {
                        color: '#888'
                    }
                }
            },
            interaction: {
                mode: 'nearest',
                axis: 'x',
                intersect: false
            }
        }
    });
}
