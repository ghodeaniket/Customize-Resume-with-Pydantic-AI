"""API endpoints for metrics reporting and visualization.

This module provides endpoints for accessing metrics about agent performance,
API usage, and system resource utilization.
"""

from fastapi import APIRouter, Depends, Query
from fastapi.responses import HTMLResponse
from typing import Dict, Optional

from resume_customizer.api.dependencies import get_admin_user
from resume_customizer.core.metrics import (
    get_agent_metrics,
    get_api_metrics,
    get_system_metrics,
    reset_metrics,
)


router = APIRouter()


@router.get("/agents", response_model=Dict)
async def get_agent_performance_metrics(
    agent_name: Optional[str] = Query(None, description="Specific agent to get metrics for"),
    aggregated: bool = Query(True, description="Whether to return aggregated statistics"),
    _: Dict = Depends(get_admin_user),
):
    """Get performance metrics for agents.
    
    This endpoint provides metrics on agent execution time, token usage,
    and other performance indicators.
    
    Args:
        agent_name: Optional specific agent to filter metrics for
        aggregated: Whether to return aggregated statistics or raw values
        
    Returns:
        Dictionary of agent metrics
    """
    return get_agent_metrics(agent_name, aggregated)


@router.get("/api", response_model=Dict)
async def get_api_performance_metrics(
    endpoint: Optional[str] = Query(None, description="Specific endpoint to get metrics for"),
    aggregated: bool = Query(True, description="Whether to return aggregated statistics"),
    _: Dict = Depends(get_admin_user),
):
    """Get performance metrics for API endpoints.
    
    This endpoint provides metrics on API request duration, error rates,
    and other performance indicators.
    
    Args:
        endpoint: Optional specific endpoint to filter metrics for
        aggregated: Whether to return aggregated statistics or raw values
        
    Returns:
        Dictionary of API metrics
    """
    return get_api_metrics(endpoint, aggregated)


@router.get("/system", response_model=Dict)
async def get_system_performance_metrics(
    aggregated: bool = Query(True, description="Whether to return aggregated statistics"),
    _: Dict = Depends(get_admin_user),
):
    """Get system-level performance metrics.
    
    This endpoint provides metrics on CPU usage, memory utilization,
    disk usage, and other system metrics.
    
    Args:
        aggregated: Whether to return aggregated statistics or raw values
        
    Returns:
        Dictionary of system metrics
    """
    return get_system_metrics(aggregated)


@router.get("/prompts", response_model=Dict)
async def get_prompt_performance_metrics(
    agent_name: Optional[str] = Query(None, description="Specific agent to get metrics for"),
    _: Dict = Depends(get_admin_user),
):
    """Get performance metrics for prompt versions.
    
    This endpoint provides metrics on different prompt versions
    for comparative analysis and A/B testing results.
    
    Args:
        agent_name: Optional specific agent to filter metrics for
        
    Returns:
        Dictionary of prompt metrics by version
    """
    from resume_customizer.core.prompts.manager import prompt_manager
    
    result = {}
    
    if agent_name:
        # Get metrics for a specific agent
        try:
            templates = prompt_manager.templates.get(agent_name, {})
            for version, template in templates.items():
                result[version] = {
                    "metrics": template.metrics,
                    "is_active": template.is_active,
                    "created_at": template.created_at.isoformat(),
                    "description": template.description,
                }
        except Exception as e:
            return {"error": f"Failed to get prompt metrics: {str(e)}"}
    else:
        # Get metrics for all agents
        try:
            for agent_name, templates in prompt_manager.templates.items():
                result[agent_name] = {}
                for version, template in templates.items():
                    result[agent_name][version] = {
                        "metrics": template.metrics,
                        "is_active": template.is_active,
                        "created_at": template.created_at.isoformat(),
                        "description": template.description,
                    }
        except Exception as e:
            return {"error": f"Failed to get prompt metrics: {str(e)}"}
    
    return result


@router.post("/reset", response_model=Dict)
async def reset_all_metrics(
    _: Dict = Depends(get_admin_user),
):
    """Reset all collected metrics.
    
    This endpoint clears all stored metrics data.
    """
    reset_metrics()
    return {"status": "success", "message": "All metrics have been reset"}


@router.get("/evaluations", response_model=Dict)
async def get_agent_evaluations(
    agent_name: Optional[str] = Query(None, description="Specific agent to get evaluations for"),
    prompt_version: Optional[str] = Query(None, description="Specific prompt version"),
    min_score: Optional[float] = Query(None, description="Minimum evaluation score filter"),
    _: Dict = Depends(get_admin_user),
):
    """Get agent output evaluation results.
    
    This endpoint provides access to the validation results and quality
    scores for agent outputs.
    
    Args:
        agent_name: Optional specific agent to filter evaluations for
        prompt_version: Optional specific prompt version to filter for
        min_score: Optional minimum score filter
        
    Returns:
        Dictionary of evaluation results
    """
    from resume_customizer.core.evaluation import get_evaluation_results
    
    try:
        results = get_evaluation_results(
            agent_name=agent_name,
            prompt_version=prompt_version,
            min_score=min_score,
            max_results=100,  # Limit to recent evaluations
            include_feedback=True
        )
        
        # Calculate some summary statistics
        total_count = len(results)
        if total_count > 0:
            avg_score = sum(r.get("overall_score", 0) for r in results) / total_count
            pass_rate = sum(1 for r in results if r.get("overall_score", 0) >= settings.EVALUATION_SCORE_THRESHOLD) / total_count
            
            summary = {
                "total_evaluations": total_count,
                "average_score": avg_score,
                "pass_rate": pass_rate,
                "evaluation_threshold": settings.EVALUATION_SCORE_THRESHOLD
            }
        else:
            summary = {
                "total_evaluations": 0,
                "average_score": 0,
                "pass_rate": 0,
                "evaluation_threshold": settings.EVALUATION_SCORE_THRESHOLD
            }
        
        return {
            "summary": summary,
            "results": results
        }
        
    except Exception as e:
        return {"error": f"Failed to get evaluation results: {str(e)}"}


@router.get("/dashboard", response_class=HTMLResponse)
async def get_metrics_dashboard(
    _: Dict = Depends(get_admin_user),
):
    """Get a dashboard for visualizing metrics.
    
    This endpoint provides an HTML dashboard for visualizing agent performance,
    API usage, and system metrics.
    """
    dashboard_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Resume Customizer Metrics Dashboard</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <script src="https://cdn.tailwindcss.com"></script>
        <style>
            .card {
                background-color: #fff;
                border-radius: 0.5rem;
                box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
                padding: 1.5rem;
                margin-bottom: 1.5rem;
            }
            .metric-value {
                font-size: 1.875rem;
                font-weight: 700;
                color: #1e3a8a;
            }
            .metric-label {
                font-size: 0.875rem;
                color: #6b7280;
                margin-bottom: 0.25rem;
            }
        </style>
    </head>
    <body class="bg-gray-100 min-h-screen">
        <div class="container mx-auto px-4 py-8">
            <h1 class="text-3xl font-bold mb-8 text-gray-800">Resume Customizer Metrics Dashboard</h1>
            
            <!-- System Metrics -->
            <div class="card">
                <h2 class="text-xl font-semibold mb-4 text-gray-700">System Metrics</h2>
                <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                    <div>
                        <div class="metric-label">CPU Usage</div>
                        <div class="metric-value" id="cpu-usage">-</div>
                    </div>
                    <div>
                        <div class="metric-label">Memory Usage</div>
                        <div class="metric-value" id="memory-usage">-</div>
                    </div>
                    <div>
                        <div class="metric-label">Disk Usage</div>
                        <div class="metric-value" id="disk-usage">-</div>
                    </div>
                </div>
                <div>
                    <canvas id="system-chart"></canvas>
                </div>
            </div>
            
            <!-- Agent Metrics -->
            <div class="card">
                <h2 class="text-xl font-semibold mb-4 text-gray-700">Agent Performance</h2>
                <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                    <div>
                        <div class="metric-label">Average Execution Time</div>
                        <div class="metric-value" id="avg-execution-time">-</div>
                    </div>
                    <div>
                        <div class="metric-label">Total Runs</div>
                        <div class="metric-value" id="total-runs">-</div>
                    </div>
                    <div>
                        <div class="metric-label">Token Usage</div>
                        <div class="metric-value" id="token-usage">-</div>
                    </div>
                </div>
                <div>
                    <canvas id="agent-chart"></canvas>
                </div>
            </div>
            
            <!-- API Metrics -->
            <div class="card">
                <h2 class="text-xl font-semibold mb-4 text-gray-700">API Performance</h2>
                <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                    <div>
                        <div class="metric-label">Average Response Time</div>
                        <div class="metric-value" id="avg-response-time">-</div>
                    </div>
                    <div>
                        <div class="metric-label">Total Requests</div>
                        <div class="metric-value" id="total-requests">-</div>
                    </div>
                    <div>
                        <div class="metric-label">Error Rate</div>
                        <div class="metric-value" id="error-rate">-</div>
                    </div>
                </div>
                <div>
                    <canvas id="api-chart"></canvas>
                </div>
            </div>
            
            <!-- Prompt Metrics -->
            <div class="card">
                <h2 class="text-xl font-semibold mb-4 text-gray-700">Prompt Performance</h2>
                <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                    <div>
                        <div class="metric-label">Active Versions</div>
                        <div class="metric-value" id="active-prompt-versions">-</div>
                    </div>
                    <div>
                        <div class="metric-label">A/B Test Status</div>
                        <div class="metric-value" id="ab-test-status">-</div>
                    </div>
                    <div>
                        <div class="metric-label">Best Performing Version</div>
                        <div class="metric-value" id="best-prompt-version">-</div>
                    </div>
                </div>
                <div>
                    <canvas id="prompt-chart"></canvas>
                </div>
            </div>
            
            <!-- Evaluation Metrics -->
            <div class="card">
                <h2 class="text-xl font-semibold mb-4 text-gray-700">Output Quality</h2>
                <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                    <div>
                        <div class="metric-label">Pass Rate</div>
                        <div class="metric-value" id="quality-pass-rate">-</div>
                    </div>
                    <div>
                        <div class="metric-label">Average Score</div>
                        <div class="metric-value" id="quality-avg-score">-</div>
                    </div>
                    <div>
                        <div class="metric-label">Evaluations Count</div>
                        <div class="metric-value" id="evaluation-count">-</div>
                    </div>
                </div>
                <div>
                    <canvas id="evaluation-chart"></canvas>
                </div>
            </div>
            
            <!-- Controls -->
            <div class="flex justify-end mt-4">
                <button id="refresh-btn" class="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 mr-2">
                    Refresh Data
                </button>
                <button id="reset-btn" class="bg-red-600 text-white px-4 py-2 rounded hover:bg-red-700">
                    Reset Metrics
                </button>
            </div>
        </div>
        
        <script>
            // Charts
            let systemChart, agentChart, apiChart;
            
            // Initialize dashboard
            document.addEventListener('DOMContentLoaded', function() {
                initCharts();
                refreshData();
                
                // Set up refresh button
                document.getElementById('refresh-btn').addEventListener('click', refreshData);
                
                // Set up reset button
                document.getElementById('reset-btn').addEventListener('click', resetMetrics);
                
                // Auto-refresh every 30 seconds
                setInterval(refreshData, 30000);
            });
            
            function initCharts() {
                // System metrics chart
                const systemCtx = document.getElementById('system-chart').getContext('2d');
                systemChart = new Chart(systemCtx, {
                    type: 'line',
                    data: {
                        labels: [],
                        datasets: [
                            {
                                label: 'CPU Usage',
                                data: [],
                                borderColor: 'rgb(59, 130, 246)',
                                tension: 0.1
                            },
                            {
                                label: 'Memory Usage',
                                data: [],
                                borderColor: 'rgb(16, 185, 129)',
                                tension: 0.1
                            }
                        ]
                    },
                    options: {
                        responsive: true,
                        scales: {
                            y: {
                                beginAtZero: true,
                                max: 100,
                                title: {
                                    display: true,
                                    text: 'Usage (%)'
                                }
                            }
                        }
                    }
                });
                
                // Agent metrics chart
                const agentCtx = document.getElementById('agent-chart').getContext('2d');
                agentChart = new Chart(agentCtx, {
                    type: 'bar',
                    data: {
                        labels: [],
                        datasets: [
                            {
                                label: 'Execution Time (s)',
                                data: [],
                                backgroundColor: 'rgba(59, 130, 246, 0.5)',
                                borderColor: 'rgb(59, 130, 246)',
                                borderWidth: 1
                            }
                        ]
                    },
                    options: {
                        responsive: true,
                        scales: {
                            y: {
                                beginAtZero: true,
                                title: {
                                    display: true,
                                    text: 'Execution Time (s)'
                                }
                            }
                        }
                    }
                });
                
                // API metrics chart
                const apiCtx = document.getElementById('api-chart').getContext('2d');
                apiChart = new Chart(apiCtx, {
                    type: 'bar',
                    data: {
                        labels: [],
                        datasets: [
                            {
                                label: 'Response Time (ms)',
                                data: [],
                                backgroundColor: 'rgba(16, 185, 129, 0.5)',
                                borderColor: 'rgb(16, 185, 129)',
                                borderWidth: 1
                            }
                        ]
                    },
                    options: {
                        responsive: true,
                        scales: {
                            y: {
                                beginAtZero: true,
                                title: {
                                    display: true,
                                    text: 'Response Time (ms)'
                                }
                            }
                        }
                    }
                });
                
                // Prompt performance chart
                const promptCtx = document.getElementById('prompt-chart').getContext('2d');
                promptChart = new Chart(promptCtx, {
                    type: 'bar',
                    data: {
                        labels: [],
                        datasets: [
                            {
                                label: 'Execution Time (s)',
                                data: [],
                                backgroundColor: 'rgba(124, 58, 237, 0.5)',
                                borderColor: 'rgb(124, 58, 237)',
                                borderWidth: 1
                            }
                        ]
                    },
                    options: {
                        responsive: true,
                        scales: {
                            y: {
                                beginAtZero: true,
                                title: {
                                    display: true,
                                    text: 'Performance Score'
                                }
                            }
                        }
                    }
                });
                
                // Evaluation metrics chart
                const evalCtx = document.getElementById('evaluation-chart').getContext('2d');
                evaluationChart = new Chart(evalCtx, {
                    type: 'bar',
                    data: {
                        labels: [],
                        datasets: [
                            {
                                label: 'Quality Score',
                                data: [],
                                backgroundColor: 'rgba(245, 158, 11, 0.5)',
                                borderColor: 'rgb(245, 158, 11)',
                                borderWidth: 1
                            }
                        ]
                    },
                    options: {
                        responsive: true,
                        scales: {
                            y: {
                                beginAtZero: true,
                                max: 1,
                                title: {
                                    display: true,
                                    text: 'Score (0-1)'
                                }
                            }
                        }
                    }
                });
            }
            
            async function refreshData() {
                try {
                    // Fetch system metrics
                    const systemResponse = await fetch('/api/v1/metrics/system');
                    const systemData = await systemResponse.json();
                    updateSystemMetrics(systemData);
                    
                    // Fetch agent metrics
                    const agentResponse = await fetch('/api/v1/metrics/agents');
                    const agentData = await agentResponse.json();
                    updateAgentMetrics(agentData);
                    
                    // Fetch API metrics
                    const apiResponse = await fetch('/api/v1/metrics/api');
                    const apiData = await apiResponse.json();
                    updateApiMetrics(apiData);
                    
                    // Fetch prompt metrics
                    const promptResponse = await fetch('/api/v1/metrics/prompts');
                    const promptData = await promptResponse.json();
                    updatePromptMetrics(promptData);
                    
                    // Fetch evaluation metrics
                    const evalResponse = await fetch('/api/v1/metrics/evaluations');
                    const evalData = await evalResponse.json();
                    updateEvaluationMetrics(evalData);
                    
                } catch (error) {
                    console.error('Error fetching metrics:', error);
                }
            }
            
            function updateSystemMetrics(data) {
                if (!data || !data.latest) return;
                
                // Update current values
                document.getElementById('cpu-usage').textContent = `${data.latest.cpu_percent.toFixed(1)}%`;
                document.getElementById('memory-usage').textContent = `${data.latest.memory_percent.toFixed(1)}%`;
                document.getElementById('disk-usage').textContent = `${data.latest.disk_percent.toFixed(1)}%`;
                
                // Update chart if history data is available
                if (data.history && data.history.length > 0) {
                    const labels = data.history.map(entry => {
                        const date = new Date(entry.timestamp);
                        return `${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`;
                    });
                    
                    const cpuData = data.history.map(entry => entry.cpu_percent);
                    const memoryData = data.history.map(entry => entry.memory_percent);
                    
                    systemChart.data.labels = labels;
                    systemChart.data.datasets[0].data = cpuData;
                    systemChart.data.datasets[1].data = memoryData;
                    systemChart.update();
                }
            }
            
            function updateAgentMetrics(data) {
                if (!data) return;
                
                // Calculate aggregate stats
                let totalRuns = 0;
                let totalTokens = 0;
                let executionTimes = [];
                
                // For the chart
                const labels = [];
                const times = [];
                
                for (const [agentName, metrics] of Object.entries(data)) {
                    labels.push(agentName);
                    
                    if (metrics.execution_time) {
                        const avgTime = metrics.execution_time.avg;
                        times.push(avgTime);
                        executionTimes.push(avgTime);
                    } else {
                        times.push(0);
                    }
                    
                    if (metrics.token_count) {
                        totalTokens += metrics.token_count.count * metrics.token_count.avg;
                    }
                    
                    if (metrics.execution_time) {
                        totalRuns += metrics.execution_time.count;
                    }
                }
                
                // Update summary metrics
                document.getElementById('total-runs').textContent = totalRuns.toString();
                document.getElementById('token-usage').textContent = totalTokens.toLocaleString();
                
                const avgExecutionTime = executionTimes.length > 0 
                    ? executionTimes.reduce((sum, time) => sum + time, 0) / executionTimes.length 
                    : 0;
                document.getElementById('avg-execution-time').textContent = `${avgExecutionTime.toFixed(2)}s`;
                
                // Update chart
                agentChart.data.labels = labels;
                agentChart.data.datasets[0].data = times;
                agentChart.update();
            }
            
            function updateApiMetrics(data) {
                if (!data) return;
                
                // Calculate aggregate stats
                let totalRequests = 0;
                let responseTimes = [];
                let errors = 0;
                
                // For the chart
                const labels = [];
                const times = [];
                
                for (const [endpoint, metrics] of Object.entries(data)) {
                    labels.push(endpoint);
                    
                    if (metrics.response_time) {
                        const avgTime = metrics.response_time.avg;
                        times.push(avgTime);
                        responseTimes.push(avgTime);
                        totalRequests += metrics.response_time.count;
                    } else {
                        times.push(0);
                    }
                    
                    if (metrics.error_count) {
                        errors += metrics.error_count.sum || 0;
                    }
                }
                
                // Update summary metrics
                document.getElementById('total-requests').textContent = totalRequests.toString();
                
                const avgResponseTime = responseTimes.length > 0 
                    ? responseTimes.reduce((sum, time) => sum + time, 0) / responseTimes.length 
                    : 0;
                document.getElementById('avg-response-time').textContent = `${avgResponseTime.toFixed(2)}ms`;
                
                const errorRate = totalRequests > 0 ? (errors / totalRequests) * 100 : 0;
                document.getElementById('error-rate').textContent = `${errorRate.toFixed(2)}%`;
                
                // Update chart
                apiChart.data.labels = labels;
                apiChart.data.datasets[0].data = times;
                apiChart.update();
            }
            
            function updatePromptMetrics(data) {
                if (!data) return;
                
                // Count active versions
                let activeVersions = 0;
                let abTestActive = false;
                let bestVersion = null;
                let bestScore = -1;
                
                // For the chart
                const labels = [];
                const scores = [];
                
                // Process data for each agent
                for (const [agentName, versions] of Object.entries(data)) {
                    // Skip if this isn't a valid agent with versions
                    if (typeof versions !== 'object') continue;
                    
                    // Check each version
                    for (const [version, info] of Object.entries(versions)) {
                        if (info.is_active) {
                            activeVersions++;
                        }
                        
                        // Calculate a performance score based on metrics
                        let perfScore = 0;
                        let metricCount = 0;
                        
                        if (info.metrics) {
                            // Consider execution time (lower is better)
                            if (info.metrics.execution_time) {
                                // Convert to a 0-1 score (lower time = higher score)
                                const timeScore = Math.max(0, 1 - info.metrics.execution_time / 10); // Assuming 10s is slow
                                perfScore += timeScore;
                                metricCount++;
                            }
                            
                            // Consider token usage (lower is better)
                            if (info.metrics.token_count) {
                                // Convert to a 0-1 score (lower tokens = higher score)
                                const tokenScore = Math.max(0, 1 - info.metrics.token_count / 5000); // Assuming 5000 tokens is high
                                perfScore += tokenScore;
                                metricCount++;
                            }
                            
                            // Consider other metrics if available
                            if (info.metrics.success_rate) {
                                perfScore += info.metrics.success_rate;
                                metricCount++;
                            }
                        }
                        
                        // Calculate average performance score
                        const avgScore = metricCount > 0 ? perfScore / metricCount : 0;
                        
                        // Add to chart
                        labels.push(`${agentName} v${version}`);
                        scores.push(avgScore);
                        
                        // Track best version
                        if (avgScore > bestScore) {
                            bestScore = avgScore;
                            bestVersion = `${agentName} v${version}`;
                        }
                    }
                    
                    // If there are multiple versions for this agent, it could be A/B testing
                    const versionCount = Object.keys(versions).length;
                    if (versionCount > 1) {
                        abTestActive = true;
                    }
                }
                
                // Update summary metrics
                document.getElementById('active-prompt-versions').textContent = activeVersions.toString();
                document.getElementById('ab-test-status').textContent = abTestActive ? 'Active' : 'Inactive';
                document.getElementById('best-prompt-version').textContent = bestVersion || 'N/A';
                
                // Update chart
                promptChart.data.labels = labels;
                promptChart.data.datasets[0].data = scores;
                promptChart.data.datasets[0].label = 'Performance Score';
                promptChart.update();
            }
            
            function updateEvaluationMetrics(data) {
                if (!data || !data.summary) return;
                
                // Get summary data
                const summary = data.summary;
                
                // Update summary metrics
                document.getElementById('quality-pass-rate').textContent = `${(summary.pass_rate * 100).toFixed(1)}%`;
                document.getElementById('quality-avg-score').textContent = summary.average_score.toFixed(2);
                document.getElementById('evaluation-count').textContent = summary.total_evaluations.toString();
                
                // For the chart - get scores by agent
                const agents = {};
                const results = data.results || [];
                
                for (const result of results) {
                    const agentName = result.agent_name;
                    if (!agents[agentName]) {
                        agents[agentName] = {
                            scores: [],
                            count: 0
                        };
                    }
                    
                    agents[agentName].scores.push(result.overall_score || 0);
                    agents[agentName].count++;
                }
                
                // Calculate averages for the chart
                const labels = [];
                const scores = [];
                
                for (const [agentName, data] of Object.entries(agents)) {
                    labels.push(agentName);
                    const avgScore = data.scores.reduce((sum, score) => sum + score, 0) / data.scores.length;
                    scores.push(avgScore);
                }
                
                // Update chart
                evaluationChart.data.labels = labels;
                evaluationChart.data.datasets[0].data = scores;
                evaluationChart.update();
            }
            
            async function resetMetrics() {
                if (confirm('Are you sure you want to reset all metrics? This action cannot be undone.')) {
                    try {
                        await fetch('/api/v1/metrics/reset', { method: 'POST' });
                        alert('Metrics have been reset.');
                        refreshData();
                    } catch (error) {
                        console.error('Error resetting metrics:', error);
                        alert('Failed to reset metrics: ' + error.message);
                    }
                }
            }
        </script>
    </body>
    </html>
    """
    
    return dashboard_html
