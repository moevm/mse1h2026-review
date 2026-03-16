import React, { useState } from 'react';
import './App.css';
import logoImg from './logo.png';

function App() {
    const [repository, setRepository] = useState('All repositories');
    const [timeRange, setTimeRange] = useState('7 days');

    return (
        <div className="admin-layout">
            {/* Боковая панель */}
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

            {/* Основной контент */}
            <main className="main-content">
                <div className="top-white-bar">
                    <h1>Statistics</h1>
                </div>
                <div className="page-content-inner">
                    {/* БЛОК ФИЛЬТРОВ */}
                    <section className="filter-card">
                        <div className="filter-group">
                            <label>REPOSITORY SCOPE</label>
                            <select
                                value={repository}
                                onChange={(e) => setRepository(e.target.value)}
                            >
                                <option>All repositories</option>
                                <option>ai-backend</option>
                                <option>frontend-app</option>
                            </select>
                        </div>
                        <div className="divider"></div>
                        <div className="filter-group">
                            <label>TIME RANGE</label>
                            <select
                                value={timeRange}
                                onChange={(e) => setTimeRange(e.target.value)}
                            >
                                <option>7 days</option>
                                <option>30 days</option>
                                <option>All time</option>
                            </select>
                        </div>
                    </section>
                    {/* ЦВЕТНЫЕ КАРТОЧКИ ПОКАЗАТЕЛЕЙ */}
                    <section className="stats-grid-three">
                        <div className="stat-card-large bg-green">
                            <label>Total Reviews</label>
                            <div className="stat-value">1,500</div>

                        </div>
                        <div className="stat-card-large bg-blue">
                            <label>Average Time</label>
                            <div className="stat-value">2,5 h</div>
                        </div>
                        <div className="stat-card-large bg-purple">
                            <label>Comment Voluem</label>
                            <div className="stat-value">1,500</div>
                        </div>
                    </section>
                    <section className="charts-grid">
                        <div className="chart-card-custom">
                            <h3>Errors Types </h3>
                            <p className="chart-subtitle">Morphology errors</p>
                            <div className="chart-content-row">
                                <div className="chart-circle type-dist">
                                    <div className="chart-inner-white"></div>
                                </div>
                                <div className="chart-legend-right">
                                    <div className="legend-row"><span className="dot d-blue"></span> Typo / Spelling</div>
                                    <div className="legend-row"><span className="dot d-mid"></span> Syntax Error</div>
                                    <div className="legend-row"><span className="dot d-light"></span> Logic Error</div>
                                </div>
                            </div>
                        </div>

                        <div className="chart-card-custom">
                            <h3>Errors Themes</h3>
                            <p className="chart-subtitle">Context errors</p>
                            <div className="chart-content-row">
                                <div className="chart-circle theme-dist">
                                    <div className="chart-inner-white"></div>
                                </div>
                                <div className="chart-legend-right">
                                    <div className="legend-row"><span className="dot d-red"></span> Memory</div>
                                    <div className="legend-row"><span className="dot d-orange"></span> Security</div>
                                    <div className="legend-row"><span className="dot d-green"></span> API Integration</div>
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
