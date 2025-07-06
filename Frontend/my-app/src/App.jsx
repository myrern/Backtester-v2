import React from 'react';
import CandleChart from './components/CandleChart';

function App() {
  return (
    <div className="App">
      <h1>AAPL Chart</h1>
      <CandleChart symbol="AAPL" />
    </div>
  );
}

export default App;
