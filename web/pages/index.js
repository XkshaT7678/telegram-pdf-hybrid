import Head from 'next/head';
import { useState, useEffect } from 'react';
import Layout from '../components/Layout';
import SearchBox from '../components/SearchBox';

export default function Home() {
  const [stats, setStats] = useState(null);

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    try {
      const response = await fetch('/api/stats');
      const data = await response.json();
      setStats(data);
    } catch (error) {
      console.error('Error fetching stats:', error);
    }
  };

  return (
    <Layout>
      <Head>
        <title>PDF Library - 80,000+ Study Materials</title>
        <meta name="description" content="Search through 80,000+ PDF study materials and books" />
      </Head>

      <div className="text-center">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">
          📚 PDF Library
        </h1>
        <p className="text-xl text-gray-600 mb-8">
          Access 80,000+ Study Materials & Books
        </p>

        {stats && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
            <div className="bg-white p-4 rounded-lg shadow">
              <div className="text-2xl font-bold text-blue-600">{stats.total_files?.toLocaleString() || '0'}</div>
              <div className="text-gray-600">Total Files</div>
            </div>
            <div className="bg-white p-4 rounded-lg shadow">
              <div className="text-2xl font-bold text-green-600">{stats.total_size_gb || '0'} GB</div>
              <div className="text-gray-600">Total Size</div>
            </div>
            <div className="bg-white p-4 rounded-lg shadow">
              <div className="text-2xl font-bold text-purple-600">24/7</div>
              <div className="text-gray-600">Available</div>
            </div>
          </div>
        )}

        <SearchBox />

        <div className="mt-12 grid grid-cols-1 md:grid-cols-3 gap-6 text-left">
          <div className="bg-white p-6 rounded-lg shadow">
            <div className="text-2xl mb-2">🔍</div>
            <h3 className="font-semibold mb-2">Easy Search</h3>
            <p className="text-gray-600">Search by book name, author, or subject with our powerful search engine.</p>
          </div>
          
          <div className="bg-white p-6 rounded-lg shadow">
            <div className="text-2xl mb-2">🤖</div>
            <h3 className="font-semibold mb-2">Telegram Bot</h3>
            <p className="text-gray-600">Get instant delivery through our secure Telegram bot verification system.</p>
          </div>
          
          <div className="bg-white p-6 rounded-lg shadow">
            <div className="text-2xl mb-2">📱</div>
