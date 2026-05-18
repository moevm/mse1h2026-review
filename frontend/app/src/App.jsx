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
    const [activeTab, setActiveTab] = useState('statistics');
    const [temperature, setTemperature] = useState(0.2);
    const [nucleusSampling, setNucleusSampling] = useState(0.7);

    const [pullRequest, setPullRequest] = useState('All PRs');
    const [pullRequests, setPullRequests] = useState(['All PRs']);
    const [globalLikes, setGlobalLikes] = useState({ liked: 0, disliked: 0, without_mark: 0 });



    const fetchStats = async () => {
        try {
            const daysValue = timeRange === 'All time' ? 0 : parseInt(timeRange);
            const query = new URLSearchParams({
                repo: repository,
                days: daysValue
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
                setAllPrs(data);

                const uniqueRepoNames = Array.from(new Set(data.map(item => item.repo)));

                setRepositories([
                    'All repositories',
                    ...uniqueRepoNames
                ]);
            }
        } catch (error) {
            console.error("Ошибка:", error);
        }
    };

    const fetchPRDetails = async (owner, repo, pr_num) => {
        try {
            const response = await fetch(`http://localhost:8000/admin/repos/${owner}/${repo}/pulls/${pr_num}`);
            const data = await response.json();
            setDetails(data);
        } catch (error) {
            console.error("Ошибка при загрузке деталей PR:", error);
        }
    };

    const fetchGlobalLikes = async () => {
        try {
            const response = await fetch('http://localhost:8000/admin/repos/likes');
            const data = await response.json();
            setGlobalLikes(data);
        } catch (error) {
            console.error("Ошибка при загрузке общих лайков:", error);
        }
    };

    const displayStats = details ? {
        total_reviews: allPrs.find(p => p.pr_number === details.pr_number && p.repo === repository)?.reviews_count || 0,
        total_comments: details.comment_count || 0,
        avg_duration_ms: details.duration_ms || 0
    } : stats;


    const likesChartData = details
        ? {
            "Liked": details.is_liked === true ? 1 : 0,
            "Disliked": details.is_liked === false ? 1 : 0,
            "No information": (details.is_liked === null || details.is_liked === undefined) ? 1 : 0
        }
        : {
            "Liked": globalLikes.liked,
            "Disliked": globalLikes.disliked,
            "No information": globalLikes.without_mark
        };

    const LIKES_COLOR_MAP = {
        "Liked": "#55efc4",
        "Disliked": "#ff7675",
        "No information": "#dfe6e9"
    };



    useEffect(() => {
        // eslint-disable-next-line react-hooks/set-state-in-effect
        fetchRepositories();
    }, []);

    useEffect(() => {
        if (repository === 'All repositories') {
            setPullRequests(['All PRs']);
            setPullRequest('All PRs');
        } else {
            const filteredPrs = allPrs
                .filter(item => item.repo === repository)
                .map(item => item.pr_number.toString());

            setPullRequests(['All PRs', ...filteredPrs]);
            setPullRequest('All PRs');
        }
    }, [repository, allPrs]);


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
    const handleIntegerOnly = (e) => {
        const systemKeys = ['Backspace', 'Delete', 'Tab', 'Escape', 'Enter', 'ArrowLeft', 'ArrowRight'];

        if (!systemKeys.includes(e.key) && (e.key < '0' || e.key > '9')) {
            e.preventDefault();
        }
    };

    const handleFloatOnly = (e) => {
        const systemKeys = ['Backspace', 'Delete', 'Tab', 'Escape', 'Enter', 'ArrowLeft', 'ArrowRight'];

        if (e.key === '.' || e.key === ',') {
            if (e.target.value.includes('.') || e.target.value.includes(',')) {
                e.preventDefault();
            }
            return;
        }

        if (!systemKeys.includes(e.key) && (e.key < '0' || e.key > '9')) {
            e.preventDefault();
        }
    };

    useEffect(() => {
        if (repository !== 'All repositories' && pullRequest !== 'All PRs') {
            const selectedPrObj = allPrs.find(
                p => p.repo === repository && p.pr_number.toString() === pullRequest
            );

            if (selectedPrObj) {
                fetchPRDetails(selectedPrObj.owner, selectedPrObj.repo, selectedPrObj.pr_number);
            }
        } else {
            setDetails(null);
            fetchStats();
            fetchGlobalLikes();
        }
    }, [repository, pullRequest, timeRange]);

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
                    <button
                        className={`nav-item ${activeTab === 'statistics' ? 'active' : ''}`}
                        onClick={() => setActiveTab('statistics')}
                    >
                        Statistics
                    </button>
                    <button
                        className={`nav-item ${activeTab === 'parameters' ? 'active' : ''}`}
                        onClick={() => setActiveTab('parameters')}
                    >
                        Model parametrs
                    </button>
                </nav>
            </aside>

            <main className="main-content">
                <div className="top-white-bar">
                    <h1>{activeTab === 'statistics' ? 'Statistics' : 'Model’s parameters'}</h1>
                </div>
                <div className="page-content-inner">
                    {activeTab === 'statistics' ? ( <>
                            <section className="filter-card">
                                <div className="filter-group">
                                    <label>REPOSITORY</label>
                                    <select
                                        value={repository}
                                        onChange={(e) => setRepository(e.target.value)}
                                    >
                                        {repositories.map(repoName => (
                                            <option key={repoName} value={repoName}>
                                                {repoName}
                                            </option>
                                        ))}
                                    </select>
                                </div>

                                <div className="divider"></div>

                                <div className="filter-group">
                                    <label>PULL REQUEST</label>
                                    <select
                                        value={pullRequest}
                                        onChange={(e) => setPullRequest(e.target.value)}
                                        disabled={repository === 'All repositories'}
                                    >
                                        {repository === 'All repositories' ? (
                                            <option>Not available</option>
                                        ) : (
                                            pullRequests.map(pr => (
                                                <option key={pr} value={pr}>
                                                    {pr === 'All PRs' ? 'All PRs' : `#${pr}`}
                                                </option>
                                            ))
                                        )}
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

                            <section className={details ? "stats-grid-four" : "stats-grid-three"}>
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
                                {details && (
                                    <div className="stat-card-large bg-light-gray">
                                        <label>Feedback Status</label>
                                        <div className="stat-value" style={{ fontSize: '24px' }}>
                                            {details.is_liked === true && "Liked"}
                                            {details.is_liked === false && "Disliked"}
                                            {details.is_liked === null || details.is_liked === undefined ? "No info" : ""}
                                        </div>
                                    </div>
                                )}
                            </section>

                            <section className={!details ? "charts-grid-three" : "charts-grid"}>
                                <div className="chart-card-custom">
                                    <h3>Errors Types</h3>
                                    <p className="chart-subtitle">{details ? `PR #${details.pr_number}` : "General"}</p>

                                    <div className={!details ? "chart-content-compact" : "chart-content-row"}>
                                        <div className={!details ? "chart-circle-small" : "chart-circle"}
                                             style={{ background: getConicGradient(typesData, TYPES_COLOR_MAP) }}>
                                            <div className={!details ? "chart-inner-white-small" : "chart-inner-white"}></div>
                                        </div>
                                        <div className={!details ? "chart-legend-side" : "chart-legend-right"}>
                                            {Object.entries(typesData).map(([name, value]) => (
                                                <div className={!details ? "legend-row-compact" : "legend-row"} key={name}>
                                                    <span className="dot" style={{ backgroundColor: TYPES_COLOR_MAP[name] }}></span>
                                                    <span className="label">{name}: </span>
                                                    <span className="value">{value}</span>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                </div>

                                <div className="chart-card-custom">
                                    <h3>Errors Themes</h3>
                                    <p className="chart-subtitle">{details ? `Context distribution` : "General"}</p>
                                    <div className={!details ? "chart-content-compact" : "chart-content-row"}>
                                        <div className={!details ? "chart-circle-small" : "chart-circle"}
                                             style={{ background: getConicGradient(themesData, TOPICS_COLOR_MAP) }}>
                                            <div className={!details ? "chart-inner-white-small" : "chart-inner-white"}></div>
                                        </div>
                                        <div className={!details ? "chart-legend-side" : "chart-legend-right"}>
                                            {Object.entries(themesData).map(([name, value]) => (
                                                <div className={!details ? "legend-row-compact" : "legend-row"} key={name}>
                                                    <span className="dot" style={{ backgroundColor: TOPICS_COLOR_MAP[name] }}></span>
                                                    <span className="label">{name}: </span>
                                                    <span className="value">{value}</span>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                </div>

                                {!details && (
                                    <div className="chart-card-custom">
                                        <h3>Approval Rate</h3>
                                        <p className="chart-subtitle">Feedback</p>
                                        <div className="chart-content-compact">
                                            <div className="chart-circle-small"
                                                 style={{ background: getConicGradient(likesChartData, LIKES_COLOR_MAP) }}>
                                                <div className="chart-inner-white-small"></div>
                                            </div>
                                            <div className="chart-legend-side">
                                                {Object.entries(likesChartData).map(([name, value]) => (
                                                    <div className="legend-row-compact" key={name}>
                                                        <span className="dot" style={{ backgroundColor: LIKES_COLOR_MAP[name] }}></span>
                                                        <span className="label">{name}</span>
                                                        <span className="value">{value}</span>
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                    </div>
                                )}
                            </section>
                    </>
                    ) : (
                        <div className="parameters-layout">
                            <div className="params-main-column">
                                <section className="params-card">
                                    <label className="section-label">Choose a repository for tuning the model’s parameters:</label>
                                    <select className="full-width-select">
                                        <option value="">Select repository...</option>
                                        {repositories.filter(r => r !== 'All repositories').map(repoName => (
                                            <option key={repoName} value={repoName}>{repoName}</option>
                                        ))}
                                    </select>
                                </section>

                                <section className="params-card">
                                    <label className="section-label">Generation Parametrs </label>

                                    <div className="inputs-inline-row">
                                        <div className="input-group">
                                            <label className="label-name">
                                                Max tokens in answer
                                                <span className="help-icon"
                                                      data-tooltip="The maximum length of the model's response. One token is roughly 0.75 words. Setting this higher allows for longer reviews but may increase processing time.">
                                                    ?
                                                </span>
                                            </label>
                                            <input
                                                type="number"
                                                min="1"
                                                step="1"
                                                defaultValue="5000"
                                                onKeyDown={handleIntegerOnly}
                                                className="styled-input"
                                            />
                                        </div>
                                        <div className="input-group">
                                            <label className="label-name">
                                                Context window size
                                                <span className="help-icon"
                                                      data-tooltip="Determines how much surrounding code and repository data the AI can 'see' at once to understand the logic and dependencies of your changes.">
                                                    ?
                                                </span>
                                            </label>
                                            <input
                                                type="number"
                                                min="1"
                                                step="1"
                                                defaultValue="5000"
                                                onKeyDown={handleIntegerOnly}
                                                className="styled-input" />
                                        </div>
                                    </div>

                                    <div className="slider-container">
                                        <div className="slider-labels-top">
                                            <label>Temperature</label>
                                            <div className="slider-right-controls">
                                                <div className="slider-value-badge">{temperature}</div>
                                                <span className="help-icon"
                                                      data-tooltip="Controls randomness. Lower values (0.1–0.3) make the output more focused and deterministic, while higher values (0.7+) encourage more creative and diverse feedback.">
                                                    ?
                                                </span>
                                            </div>
                                        </div>
                                        <div className="slider-wrapper">
                                            <span className="range-label">Factual</span>
                                            <input
                                                type="range"
                                                min="0"
                                                max="1"
                                                step="0.01"
                                                value={temperature}
                                                onChange={(e) => setTemperature(parseFloat(e.target.value))}
                                                className="modern-slider"
                                            />
                                            <span className="range-label">Creative</span>
                                        </div>
                                    </div>

                                    <div className="slider-container">
                                        <div className="slider-labels-top">
                                            <label>Nucleus sampling</label>
                                            <div className="slider-right-controls">
                                                <div className="slider-value-badge">{nucleusSampling}</div>
                                                <span className="help-icon"
                                                      data-tooltip="An alternative to temperature that filters the model's word choices. Lowering it helps prevent the AI from choosing very unlikely words, ensuring more 'precise' results.">
                                                    ?
                                                </span>
                                            </div>
                                        </div>
                                        <div className="slider-wrapper">
                                            <span className="range-label">Precise</span>
                                            <input
                                                type="range"
                                                min="0"
                                                max="1"
                                                step="0.01"
                                                value={nucleusSampling}
                                                onChange={(e) => setNucleusSampling(parseFloat(e.target.value))}
                                                className="modern-slider"
                                            />
                                            <span className="range-label">Diverse</span>
                                        </div>
                                    </div>

                                    <div className="input-group" style={{marginTop: '30px', width: '350px'}}>
                                        <label className="label-name">Repetition penalty
                                            <span className="help-icon"
                                                  data-tooltip="Prevents the model from repeating the same phrases or getting stuck in loops. A value of 1.1–1.2 is usually enough to keep the review flow natural.">
                                                ?
                                            </span>
                                        </label>
                                        <input
                                            type="number"
                                            step="0.1"
                                            min="1"
                                            defaultValue="1.1"
                                            onKeyDown={handleFloatOnly}
                                            onBlur={(e) => {
                                                if (e.target.value.endsWith('.') || e.target.value.endsWith(',')) {
                                                    e.target.value = e.target.value.slice(0, -1);
                                                }
                                            }}
                                            className="styled-input"
                                        />
                                    </div>

                                    <div className="inputs-inline-row-2">
                                        <div className="input-group">
                                            <label className="label-name">
                                                Seed
                                                <span className="help-icon"
                                                      data-tooltip="The starting numerical value that initiates the pseudo-random number generator.">
                                                    ?
                                                </span>
                                            </label>
                                            <input
                                                type="number"
                                                min="1"
                                                step="1"
                                                defaultValue="42"
                                                onKeyDown={handleIntegerOnly}
                                                className="styled-input"
                                            />
                                        </div>
                                        <div className="input-group">
                                            <label className="label-name">
                                                Concurrency
                                                <span className="help-icon"
                                                      data-tooltip="The number of simultaneous requests to the model.">
                                                    ?
                                                </span>
                                            </label>
                                            <input
                                                type="number"
                                                min="1"
                                                step="1"
                                                defaultValue="2"
                                                onKeyDown={handleIntegerOnly}
                                                className="styled-input" />
                                        </div>
                                    </div>
                                </section>

                                <section className="params-card">
                                    <label className="section-label">Prompt</label>
                                    <textarea className="prompt-textarea" placeholder="Enter system prompt here..."></textarea>
                                </section>
                            </div>

                            <div className="params-side-column">
                                <section className="params-card">
                                    <label className="section-label-small">Choose the model</label>
                                    <select className="full-width-select"><option>Gemini 1.5 Pro</option></select>
                                </section>

                                <section className="params-card">
                                    <label className="section-label">Network</label>
                                    <div className="input-group">
                                        <label className="label-name">Timeout (sec)</label>
                                        <input type="number"
                                               min="1"
                                               step="1"
                                               defaultValue="500"
                                               onKeyDown={handleIntegerOnly}
                                               className="styled-input"
                                        />
                                        <p className="hint">Default network request timeout for API calls</p>
                                    </div>
                                </section>
                                <section className="params-card">
                                    <label className="section-label">Waiting GitHub</label>
                                    <div className="input-group">
                                        <label className="label-name">Timeout (sec)</label>
                                        <input type="number"
                                               min="1"
                                               step="1"
                                               defaultValue="120"
                                               onKeyDown={handleIntegerOnly}
                                               className="styled-input"
                                        />
                                        <p className="hint">Waiting for a response from GitHub</p>
                                    </div>
                                </section>
                                <section className="params-card">
                                    <label className="section-label">Review</label>
                                    <label className="label-name">Review mode</label>
                                    <select className="full-width-select">
                                        <option>FULL_FILE_DIFF</option>
                                        <option>FULL_FILE_CURRENT</option>
                                        <option>FULL_FILE_PREVIOUS</option>
                                        <option>ONLY_ADDED</option>
                                        <option>ONLY_REMOVED</option>
                                        <option>ADDED_AND_REMOVED</option>
                                        <option>ONLY_ADDED_WITH_CONTEXT</option>
                                        <option>ONLY_REMOVED_WITH_CONTEXT</option>
                                        <option>ADDED_AND_REMOVED_WITH_CONTEXT</option>
                                    </select>
                                    <div className="review-descriptions">
                                        <label className="label-name">Description</label>
                                        <p>
                                            <span>•</span> <strong>FULL_FILE_DIFF</strong><br/>
                                            <em>Compare added and removed lines (Default)</em>
                                        </p>
                                        <p>
                                            <span>•</span> <strong>FULL_FILE_CURRENT</strong><br/>
                                            <em>Review current version</em>
                                        </p>
                                        <p>
                                            <span>•</span> <strong>FULL_FILE_PREVIOUS</strong><br/>
                                            <em>Review previous version</em>
                                        </p>
                                        <p>
                                            <span>•</span> <strong>ONLY_ADDED</strong><br/>
                                            <em>Only added lines</em>
                                        </p>
                                        <p>
                                            <span>•</span> <strong>ONLY_REMOVED</strong><br/>
                                            <em>Only removed lines</em>
                                        </p>
                                        <p>
                                            <span>•</span> <strong>ADDED_AND_REMOVED</strong><br/>
                                            <em>Added and removed lines</em>
                                        </p>
                                        <p>
                                            <span>•</span> <strong>..._WITH_CONTEXT</strong><br/>
                                            <em>Includes N lines of surrounding context</em>
                                        </p>
                                    </div>
                                </section>
                            </div>
                            <button className="apply-btn">Apply changes</button>
                        </div>
                    )}
                </div>
            </main>
        </div>
    );
}

export default App;