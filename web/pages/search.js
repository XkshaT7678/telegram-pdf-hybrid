// Mock API for demonstration
// In production, you'd connect to your actual database

export default async function handler(req, res) {
  if (req.method !== 'GET') {
    return res.status(405).json({ success: false, error: 'Method not allowed' });
  }

  const { q, page = 1, limit = 20 } = req.query;
  
  if (!q) {
    return res.status(400).json({ success: false, error: 'Query parameter is required' });
  }

  try {
    // Mock data - replace with actual database call
    const mockResults = [
      {
        file_id: 'file_1',
        file_name: 'Calculus Made Easy.pdf',
        file_size: 2500000,
        file_caption: 'Complete calculus guide for beginners',
        message_id: 123,
        created_at: '2024-01-15'
      },
      {
        file_id: 'file_2',
        file_name: 'Advanced Mathematics.pdf',
        file_size: 3500000,
        file_caption: 'Advanced mathematical concepts and theories',
        message_id: 124,
        created_at: '2024-01-14'
      },
      {
        file_id: 'file_3', 
        file_name: 'Python Programming Guide.pdf',
        file_size: 1800000,
        file_caption: 'Complete Python programming tutorial',
        message_id: 125,
        created_at: '2024-01-13'
      }
    ].filter(book => 
      book.file_name.toLowerCase().includes(q.toLowerCase()) ||
      book.file_caption.toLowerCase().includes(q.toLowerCase())
    );

    const stats = {
      total_files: 80000,
      total_size_gb: 150.5,
      last_updated: '2024-01-15'
    };

    res.status(200).json({
      success: true,
      results: mockResults,
      stats: {
        total_results: mockResults.length,
        query: q,
        page: parseInt(page),
        limit: parseInt(limit),
        ...stats
      }
    });

  } catch (error) {
    console.error('Search API error:', error);
    res.status(500).json({ 
      success: false, 
      error: 'Internal server error',
      message: error.message 
    });
  }
}
