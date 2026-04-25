import React, { useState, useEffect } from 'react';
import './App.css';
import logoImg from './logo.png';

function App() {
    const [repository, setRepository] = useState('All repositories');
    const [timeRange, setTimeRange] = useState('7 days');
    const [repositories, setRepositories] = useState(['All repositories']);
    const [stats, setStats] = useState({
        total_reviews: 0,
        total_comments: 0,
        avg_duration_ms: 0 });
    const [details, setDetails] = useState(null);
    const [allPrs, setAllPrs] = useState([]);

    const fetchStats = async () => {
        try {
            const query = new URLSearchParams({
                repo: repository,
                range: timeRange
            }).toString();

            const response = await fetch(`http://localhost:8000/admin/stats?${query}`);
            const data = await response.json();
            setStats(data);
        } catch (error) {
            console.error("Ошибка при загрузке статистики:", error);
        }
    };

    const TYPES_COLOR_MAP = {
        "Syntax Error": "#0984e3",
        "Logical Error": "#74b9ff",
        "Performance Error": "#6c5ce7",
        "Style Error": "#a29bfe",
        "Security Error": "#636e72",
        "Memory Error": "#b2bec3"
    };

    const TOPICS_COLOR_MAP = {
        "Algorithms": "#55efc4",
        "Databases": "#00b894",
        "File Operations": "#ffeaa7",
        "Testing": "#fdcb6e",
        "Input/Output": "#fab1a0",
        "Optimization": "#e17055",
        "Logging": "#d63031",
        "Documentation": "#81ecec",
        "Dependencies": "#00cec9"
    };

    const getConicGradient = (data, colorMap) => {
        if (!data || Object.keys(data).length === 0) return "#eee";

        const entries = Object.entries(data);
        let total = entries.reduce((acc, [_, val]) => acc + val, 0);
        if (total === 0) return "#eee";

        let currentPercent = 0;
        const gradient = entries.map(([name, val]) => {
            const percent = (val / total) * 100;
            const color = colorMap[name] || "#dfe6e9";
            const string = `${color} ${currentPercent}% ${currentPercent + percent}%`;
            currentPercent += percent;
            return string;
        }).join(", ");

        return `conic-gradient(${gradient})`;
    };

    const fetchRepositories = async () => {
        try {
            const response = await fetch('http://localhost:8000/admin/pulls');
            const data = await response.json();

            if (data && data.length > 0) {
                const formattedRepos = data.map(item => ({
                    id: item.repo,
                    displayName: `${item.repo}/${item.owner}/${item.pr_number}`
                }));
                const uniqueRepos = Array.from(new Map(formattedRepos.map(item => [item.displayName, item])).values());

                setRepositories([
                    { id: 'All repositories', displayName: 'All repositories' },
                    ...uniqueRepos
                ]);
                setAllPrs(data);
            }
        } catch (error) {
            console.error("Ошибка:", error);
        }
    };

    const fetchPRDetails = async (repoPath) => {
        const parts = repoPath.split('/');
        if (parts.length !== 3) return;

        const [repo, owner, pr_num] = parts;

        try {
            const response = await fetch(`http://localhost:8000/admin/repos/${owner}/${repo}/pulls/${pr_num}`);
            const data = await response.json();
            setDetails(data);
        } catch (error) {
            console.error("Ошибка при загрузке деталей PR:", error);
        }
    };

    const displayStats = details ? {
        total_reviews: allPrs.find(p => p.pr_number === details.pr_number && p.repo === repository.split('/')[0])?.reviews_count || 0,
        total_comments: details.comment_count || 0,
        avg_duration_ms: details.duration_ms || 0
    } : stats;

    const handleRepoChange = (e) => {
        setRepository(e.target.value);
    };

    useEffect(() => {
        // eslint-disable-next-line react-hooks/set-state-in-effect
        fetchRepositories();
    }, []);

    useEffect(() => {
        if (repository === 'All repositories') {
            // eslint-disable-next-line react-hooks/set-state-in-effect
            setDetails(null);
            fetchStats();
        } else {
            fetchPRDetails(repository);
        }
    }, [repository, timeRange]);

    const formatDuration = (ms) => {
        if (!ms || ms <= 0) return "0s";

        const totalSeconds = Math.round(ms / 1000);
        const hours = Math.floor(totalSeconds / 3600);
        const minutes = Math.floor((totalSeconds % 3600) / 60);
        const seconds = totalSeconds % 60;

        const parts = [];
        if (hours > 0) parts.push(`${hours}h`);
        if (minutes > 0) parts.push(`${minutes}m`);
        if (seconds > 0 || parts.length === 0) parts.push(`${seconds}s`);

        return parts.join(' ');
    };
    const ALLOWED_TYPES = ["Syntax Error", "Logical Error", "Performance Error", "Style Error", "Security Error", "Memory Error"];
    const ALLOWED_TOPICS = ["Algorithms", "Databases", "File Operations", "Testing", "Input/Output", "Optimization", "Logging", "Documentation", "Dependencies"];
    const displayChartData = details?.chart_data || stats?.chart_data || {};
    const safeChartData = displayChartData && typeof displayChartData === 'object' ? displayChartData : {};
    const typesData = Object.fromEntries(
        Object.entries(safeChartData).filter(([key]) => ALLOWED_TYPES.includes(key))
    );

    const themesData = Object.fromEntries(
        Object.entries(safeChartData).filter(([key]) => ALLOWED_TOPICS.includes(key))
    );
    console.log("DEBUG: Что пришло с сервера:", Object.keys(safeChartData));



    return (
        <div className="admin-layout">
            <aside className="sidebar">
                <div className="logo">
                    <img src={logoImg} alt="Logo" className="logo-icon-img" />
                    <div className="logo-info">
                        <strong>CodeReview Admin</strong>
                        <p>Management portal</p>
                    </div>
                </div>
                <nav>
                    <button className="nav-item active">Statistics</button>
                </nav>
            </aside>

            <main className="main-content">
                <div className="top-white-bar">
                    <h1>Statistics</h1>
                </div>
                <div className="page-content-inner">
                    <section className="filter-card">
                        <div className="filter-group">
                            <label>REPOSITORY SCOPE</label>
                            <select value={repository} onChange={handleRepoChange}>
                                {repositories.map((repoObj, index) => (
                                    <option key={index} value={repoObj.displayName}>
                                        {repoObj.displayName}
                                    </option>
                                ))}
                            </select>
                        </div>
                        <div className="divider"></div>
                        <div className="filter-group">
                            <label>TIME RANGE</label>
                            <select value={timeRange} onChange={(e) => setTimeRange(e.target.value)}>
                                <option>7 days</option>
                                <option>30 days</option>
                                <option>All time</option>
                            </select>
                        </div>
                    </section>

                    <section className="stats-grid-three">
                        <div className="stat-card-large bg-green">
                            <label>Total Reviews</label>
                            <div className="stat-value">
                                {(displayStats?.total_reviews || 0).toLocaleString()}
                            </div>
                        </div>
                        <div className="stat-card-large bg-blue">
                            <label>Average Time</label>
                            <div className="stat-value">
                                {formatDuration(displayStats?.avg_duration_ms || 0)}
                            </div>
                        </div>
                        <div className="stat-card-large bg-purple">
                            <label>Comment Volume</label>
                            <div className="stat-value">
                                {(displayStats?.total_comments || 0).toLocaleString()}
                            </div>
                        </div>
                    </section>

                    <section className="charts-grid">
                        {/* КАРТОЧКА №1: Errors Types */}
                        <div className="chart-card-custom">
                            <h3>Errors Types</h3>
                            <p className="chart-subtitle">
                                {details ? `PR #${details.pr_number} distribution` : "General distribution"}
                            </p>
                            <div className="chart-content-row">
                                <div className="chart-circle type-dist"
                                     style={{ background: getConicGradient(typesData, TYPES_COLOR_MAP) }}>
                                    <div className="chart-inner-white"></div>
                                </div>
                                <div className="chart-legend-right">
                                    {typesData && Object.entries(typesData).map(([name, value]) => (
                                        <div className="legend-row" key={name}>
                                            <span className="dot" style={{ backgroundColor: TYPES_COLOR_MAP[name] || "#dfe6e9" }}></span>
                                            {name}: {value}
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </div>

                        {/* КАРТОЧКА №2: Errors Themes */}
                        <div className="chart-card-custom">
                            <h3>Errors Themes</h3>
                            <p className="chart-subtitle">
                                {details ? `Context distribution` : "General distribution"}
                            </p>
                            <div className="chart-content-row">
                                <div className="chart-circle theme-dist"
                                     style={{ background: getConicGradient(themesData, TOPICS_COLOR_MAP) }}>
                                    <div className="chart-inner-white"></div>
                                </div>

                                <div className="chart-legend-right">
                                    {themesData && Object.entries(themesData).map(([name, value]) => (
                                        <div className="legend-row" key={name}>
                                            <span className="dot" style={{ backgroundColor: TOPICS_COLOR_MAP[name] || "#dfe6e9" }}></span>
                                            {name}: {value}
                                        </div>
                                    ))}
                                    {(!themesData || Object.keys(themesData).length === 0) && <p>No themes data</p>}
                                </div>
                            </div>
                        </div>
                    </section>
                </div>
            </main>
        </div>
    );
}

export default App;