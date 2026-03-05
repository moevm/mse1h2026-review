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

                    {/* Заглушки */}
                    <div className="stats-placeholder">
                        Карточки
                    </div>
                    <div className="charts-placeholder">
                        Круговые диаграммы
                    </div>
                </div>
            </main>
        </div>
    );
}

export default App;