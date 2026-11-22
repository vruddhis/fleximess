import { useCallback, useEffect, useState } from 'react';

const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
).replace(/\/+$/, '');

async function getJson(path) {
  const response = await fetch(`${API_BASE_URL}${path}`);
  const body = await response.json();

  if (!response.ok) {
    throw new Error(body.detail || `Request failed (${response.status})`);
  }

  return body;
}

async function fetchDemoData() {
  const [health, messes, foods, menus] = await Promise.all([
    getJson('/health'),
    getJson('/api/messes'),
    getJson('/api/foods'),
    getJson('/api/menus?meal_type=lunch'),
  ]);
  return { health, messes, foods, menus };
}

function Demo() {
  const [data, setData] = useState(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);

  const loadDemoData = useCallback(async () => {
    setLoading(true);
    setError('');

    try {
      setData(await fetchDemoData());
    } catch (requestError) {
      setError(
        `${requestError.message}. Make sure the backend is running at ${API_BASE_URL}.`,
      );
      setData(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    let active = true;
    fetchDemoData()
      .then((responseData) => {
        if (active) setData(responseData);
      })
      .catch((requestError) => {
        if (active) {
          setError(
            `${requestError.message}. Make sure the backend is running at ${API_BASE_URL}.`,
          );
        }
      })
      .finally(() => {
        if (active) setLoading(false);
      });

    return () => {
      active = false;
    };
  }, []);

  return (
    <main style={{ maxWidth: 800, margin: '40px auto', padding: 24 }}>
      <h1>Frontend + Backend Demo</h1>
      <p>
        This page requests sample data from the FastAPI backend at{' '}
        <code>{API_BASE_URL}</code>.
      </p>
      <button type="button" onClick={loadDemoData} disabled={loading}>
        {loading ? 'Connecting…' : 'Try again'}
      </button>

      {loading && <p role="status">Connecting to the API…</p>}
      {error && <p role="alert">{error}</p>}

      {data && (
        <section aria-label="API response">
          <h2>Connection successful</h2>
          <p>API status: {data.health.status}</p>

          <h2>Hostels ({data.messes.length})</h2>
          <ul>
            {data.messes.map((mess) => (
              <li key={mess.mess_id}>{mess.mess_name}</li>
            ))}
          </ul>

          <h2>Foods ({data.foods.length})</h2>
          <ul>
            {data.foods.map((food) => (
              <li key={food.food_id}>
                {food.name} — {food.nutrition.calories_kcal} kcal,{' '}
                {food.nutrition.protein_g} g protein
              </li>
            ))}
          </ul>

          <h2>Sample lunch menus ({data.menus.length})</h2>
          {data.menus.map((menu) => (
            <section key={menu.mess_id}>
              <h3>{menu.mess_name}</h3>
              <ul>
                {menu.items.map((food) => (
                  <li key={food.food_id}>{food.name}</li>
                ))}
              </ul>
            </section>
          ))}
        </section>
      )}
    </main>
  );
}

export default Demo;